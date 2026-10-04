# -*- coding: utf-8 -*-
"""日线本地缓存 —— 把 TQ 的日K增量落成 lday 32 字节 .day 文件, 支持截至某日回放。

为什么需要: 回测要对每个历史调仓日 T 取"截至 T 的窗口"。直接走 TQ 每个窗口
一次请求, 全市场重放很慢; 有了本地缓存, 全量读一次内存里切片即可, 且离线可复跑。
存的是 **不复权价**(dividend_type="none")—— 前复权序列会随未来分红整体平移,
拿它做 point-in-time 回放本身就是失真的(收益口径见 indicators.total_return_with_dividends)。

文件格式直接复用 lday.py 的 32 字节记录(<IIIIIfII), 可用 lday 工具互操作;
价格 ×100 定点存储, Amount 单位元, Volume 为 TQ 返回原值。缓存目录只由本
模块写入; 若用官方 vipdoc 的 .day 文件初始化, 注意两边 Volume 单位口径需自查。

用法::

    from tdx_local import TqClient, kcache

    tq = TqClient()
    kcache.update(tq, ["600000.SH", "000001.SZ"], count=-1)   # 首次全量/此后增量
    bars = kcache.read(kcache.default_dir(), "600000.SH",
                       count=80, end_date=20240628)           # 截至 2024-06-28 的 80 根
    # bars 形如 TqClient.market_data 的每股 Value: {"Date": [...], "Close": [...], ...}
"""
import os
from pathlib import Path

from . import lday

# 与 TQ market_data 日线返回一致的列; lday 记录只承载其中 7 列(Time 无日线语义)
FIELDS = ("Date", "Open", "High", "Low", "Close", "Volume", "Amount")
BATCH = 150          # 单次 get_market_data 的代码数(150只x全历史 < 24000 行分页上限)


def default_dir() -> str:
    """缓存目录: 环境变量 TDX_KCACHE_DIR, 缺省 <仓库根>/kcache/。"""
    env = os.environ.get("TDX_KCACHE_DIR")
    if env:
        return env
    return str(Path(__file__).resolve().parent.parent / "kcache")


def path_for(cache_dir, code):
    """代码 -> 缓存文件路径: 600000.SH -> <dir>/sh600000.day(BJ 北交所)。"""
    market = code.split(".")[-1].lower()
    num = code.split(".")[0]
    return Path(cache_dir) / f"{market}{num}.day"


def _to_int_date(d):
    return int(str(d).replace("-", ""))


def update(client, codes, cache_dir=None, count=-1, batch_size=BATCH) -> dict:
    """从 TQ 增量拉取日线并合并进缓存, 返回 {code: {added, updated, total}}。

    合并规则: 日期并集; 重叠日以 TQ 新数据为准(缓存语义是"向上游刷新",
    与 lday.sync_lday 的目标侧为准相反 —— 那里目标=官方客户端目录才是权威)。
    本地无数据的代码记入返回值 "_missing"。count>0 只刷新最近 n 根(增量)。
    """
    cache_dir = cache_dir or default_dir()
    codes = list(codes)
    stats, missing = {}, {}
    for i in range(0, len(codes), batch_size):
        batch = codes[i:i + batch_size]
        r = client.market_data(list(batch), count=count, period="1d",
                               dividend_type="none", field_list=list(FIELDS))
        missing.update(r.get("_missing") or {})
        for code in batch:
            val = (r.get("Value") or {}).get(code)
            if not isinstance(val, dict) or not val.get("Date"):
                continue
            path = path_for(cache_dir, code)
            old = lday.read_lday(str(path)) if path.exists() else {}
            merged = dict(old)
            dates = val["Date"]
            cols = {k: val.get(k) or [] for k in FIELDS}
            added = updated = 0
            for j, d in enumerate(dates):
                di = _to_int_date(d)
                bar = (
                    int(round(float(cols["Open"][j]) * 100)),
                    int(round(float(cols["High"][j]) * 100)),
                    int(round(float(cols["Low"][j]) * 100)),
                    int(round(float(cols["Close"][j]) * 100)),
                    float(cols["Amount"][j]) if j < len(cols["Amount"]) else 0.0,
                    int(round(float(cols["Volume"][j]))) if j < len(cols["Volume"]) else 0,
                )
                if di in merged:
                    if merged[di] != bar:
                        updated += 1
                else:
                    added += 1
                merged[di] = bar
            if merged != old:
                path.parent.mkdir(parents=True, exist_ok=True)
                lday.write_lday(str(path), merged)
            stats[code] = {"added": added, "updated": updated, "total": len(merged)}
    if missing:
        stats["_missing"] = missing
    return stats


def read(cache_dir, code, count=None, end_date=None):
    """读单只缓存 -> TQ 同款列式 {"Date": [...], "Close": [...], ...}。

    end_date(YYYYMMDD) 只保留 <= end_date 的K线(point-in-time 回放);
    count 取末端 n 根。文件不存在返回 {}。
    """
    path = path_for(cache_dir, code)
    if not path.exists():
        return {}
    bars = lday.read_lday(str(path))
    dates = sorted(bars)
    if end_date is not None:
        ei = _to_int_date(end_date)
        dates = [d for d in dates if d <= ei]
    if count is not None and count >= 0:
        dates = dates[-count:]
    out = {k: [] for k in FIELDS}
    for d in dates:
        o, h, l, c, amt, vol = bars[d]
        out["Date"].append(d)
        out["Open"].append(o / 100.0)
        out["High"].append(h / 100.0)
        out["Low"].append(l / 100.0)
        out["Close"].append(c / 100.0)
        out["Amount"].append(amt)
        out["Volume"].append(vol)
    return out


def read_many(cache_dir, codes, count=None, end_date=None) -> dict:
    """批量读缓存 -> {code: 列式bars}; 无缓存文件的代码不出现在返回里。"""
    out = {}
    for code in codes:
        bars = read(cache_dir, code, count=count, end_date=end_date)
        if bars:
            out[code] = bars
    return out
