# -*- coding: utf-8 -*-
"""分钟线归档器(vipdoc 直读版) —— 把 .01/.5 原样落成只增不减的本地归档。

痛点: DataTool 分钟转档每次重写 .5 只保留最近约 24000 根(约两年), 超出部分
被物理截掉且不可再生(1 分钟免费通道约 100 天, 过期服务器也不留)。本脚本
直读 vipdoc 分钟文件, 以同样的 32 字节记录格式增量写进归档目录:
  - 归档侧还没有该代码 -> 整文件拷贝(无损, 即种子);
  - 已有归档 -> 只把 vipdoc 里比归档末根 (日期,时间) 更新的记录追加进去。
转档 GUI 怎么截窗口都不影响归档, 深度随时间自然增长。与 archive_minutes.py
(TQ/CSV 版, 适合关注池、可在盘中取数)互补: 本版离线可跑(转档完即可, 不需要
TdxW 在线), 全市场体量下二进制体积只有 CSV 的约三分之一。

记录格式与 vipdoc 原生一致(<HH4IfI2H>, 见 docs/LOCAL_NOTES.md「.5/.01 新代
分钟文件布局」): 日期词 (y-2004)*2048+m*100+d、时间词 hh*60+mm、开高低收×100
(uint32)、成交额(f32 元)、成交量(uint32 股)、pad。归档即 vipdoc 镜像, 口径
原样保留; 读取用 read_bars() 还原成与 TQ market_data 同构的字段。

用法: python examples/archive_minutes_vipdoc.py               # 参数区池子, 1m+5m
      python examples/archive_minutes_vipdoc.py 5m all        # 全市场 5m(种子/增量)
      python examples/archive_minutes_vipdoc.py check 600519.SH   # 按日根数对账
"""
import os
import shutil
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ============================ 参数区(按需修改) ============================
VIPDOC = os.environ.get("TDX_VIPDOC") or r"D:\jyrj\tdx\vipdoc"
PERIODS = ("1m", "5m")   # 命令行可用 "5m" / "1m,5m" 覆盖
CODES = [                # 关注池; 命令行加 all 或改成 None = 全市场(sh/sz/bj)
    "999999.SH", "399001.SZ", "880001.SH",
    "600000.SH", "600519.SH", "000001.SZ", "300750.SZ",
]
# 归档压缩: gzip 多成员追加(每次追加一个成员, 合法 gzip, 读时自动解);
# 全市场裸 bin 体量约 gzip 的 2-3 倍, 默认开。旧裸 .bin 归档仍可读(读取按魔数识别)。
USE_GZIP = True
# 输出目录: 环境变量 TDX_MIN_ARCHIVE, 缺省 <仓库根>/minute_archive/<周期>/
# 全市场体量参考(2026-10-15): 5m 种子约 8GB; 1m 约 45GB, 且每交易日约 +0.4GB
# =========================================================================

REC = struct.Struct("<HH4IfI2H")
PERIOD_META = {
    "1m": {"sub": "minline", "ext": ".01", "bars": 240},
    "5m": {"sub": "fzline", "ext": ".5", "bars": 48},
}


def out_dir(period):
    env = os.environ.get("TDX_MIN_ARCHIVE")
    base = env or str(Path(__file__).resolve().parent.parent / "minute_archive")
    return Path(base) / period


def vip_path(vipdoc, code, period):
    """600519.SH + 5m -> <vipdoc>/sh/fzline/sh600519.5。"""
    num, mkt = code.split(".")
    meta = PERIOD_META[period]
    return Path(vipdoc) / mkt.lower() / meta["sub"] / f"{mkt.lower()}{num}{meta['ext']}"


def arc_path(code, period):
    """归档文件路径(USE_GZIP=True 为 .bin.gz; 读取端对两种后缀都兼容)。"""
    num, mkt = code.split(".")
    ext = ".bin.gz" if USE_GZIP else ".bin"
    return out_dir(period) / f"{mkt.lower()}{num}{ext}"


def _is_gz(path):
    """按魔数判断是否 gzip(与后缀无关, 旧裸 .bin 与新 .bin.gz 都能读)。"""
    try:
        with open(path, "rb") as f:
            return f.read(2) == b"\x1f\x8b"
    except OSError:
        return False


def _raw(path):
    """归档/vipdoc 文件 -> 原始 32B 记录流(gzip 自动解压)。"""
    if _is_gz(path):
        import gzip
        return gzip.open(path, "rb").read()
    return Path(path).read_bytes()


def all_codes(vipdoc, period):
    """扫 vipdoc 目录列全市场代码(排序保证进度稳定)。"""
    meta = PERIOD_META[period]
    codes = []
    for mkt in ("sh", "sz", "bj"):
        folder = Path(vipdoc) / mkt / meta["sub"]
        if not folder.is_dir():
            continue
        for f in folder.iterdir():
            if f.suffix == meta["ext"] and f.stem.startswith(mkt):
                codes.append(f"{f.stem[len(mkt):]}.{mkt.upper()}")
    return sorted(codes)


def _last_member_stamp(path):
    """gzip 多成员文件: 只解最后一个成员取末 32B(最后追加段即最新数据)。

    反向找成员头魔数可能伪命中(压缩数据里也会出现 1f8b08), 从尾往前
    逐候选尝试解压, 第一个 CRC 通过的即最后一个完整成员 —— 崩溃截断的
    成员解压失败会被自然跳过(末 stamp 偏旧 -> 下次多拉重叠段, 归档侧
    按 stamp 过滤不会重复写入)。
    """
    import zlib
    data = Path(path).read_bytes()
    pos = data.rfind(b"\x1f\x8b\x08")
    while pos >= 0:
        try:
            out = zlib.decompressobj(16 + zlib.MAX_WBITS).decompress(data[pos:])
            if len(out) >= 32:
                return REC.unpack_from(out, len(out) - 32)[:2]
        except zlib.error:
            pass
        pos = data.rfind(b"\x1f\x8b\x08", 0, pos)
    return None


def _last_stamp(path):
    """末根 (日期词, 时间词); 空信封/长度不对返回 None(视为无有效归档)。"""
    if _is_gz(path):
        return _last_member_stamp(path)
    size = path.stat().st_size
    if size < 32 or size % 32:
        return None
    with open(path, "rb") as f:
        f.seek(size - 32)
        return REC.unpack(f.read(32))[:2]


def append_new(vip_file, arc_file, day_bars) -> int:
    """增量归档单个代码, 返回本次新增根数。归档只追加, 永不回缩。"""
    size = vip_file.stat().st_size
    if size < 32 or size % 32:
        return 0
    if not arc_file.exists() or _last_stamp(arc_file) is None:
        arc_file.parent.mkdir(parents=True, exist_ok=True)
        data = Path(vip_file).read_bytes()
        if str(arc_file).endswith(".gz"):
            import gzip
            with open(arc_file, "wb") as f:
                f.write(gzip.compress(data, mtime=0))   # mtime=0: 压缩流可复现
        else:
            shutil.copyfile(vip_file, arc_file)
        return len(data) // 32

    d_arc, t_arc = _last_stamp(arc_file)
    if _last_stamp(vip_file) <= (d_arc, t_arc):
        return 0
    # 从 vipdoc 尾部按块回找分界: 第一根 (日期,时间) 晚于归档末根的记录。
    # 窗口滚动把 vipdoc 前端截到归档末根之前时, 分界就是 0(整文件都算新增)。
    n_vip = size // 32
    split, idx, step = None, n_vip, 4 * day_bars
    with open(vip_file, "rb") as f:
        while split is None:
            lo = max(0, idx - step)
            f.seek(lo * 32)
            block = f.read((idx - lo) * 32)
            for off in range(0, len(block), 32):
                d, t = REC.unpack_from(block, off)[:2]
                if (d, t) > (d_arc, t_arc):
                    split = lo + off // 32
                    break
            if lo == 0:
                split = 0
            idx = lo
    with open(vip_file, "rb") as f:
        f.seek(split * 32)
        fresh = f.read()
    rows = [REC.unpack_from(fresh, off) for off in range(0, len(fresh), 32)]
    rows = [r for r in rows if (r[0], r[1]) > (d_arc, t_arc)]   # 乱序/重复兜底
    if rows:
        if str(arc_file).endswith(".gz"):
            import gzip
            with gzip.GzipFile(fileobj=open(arc_file, "ab"), mode="ab",
                               mtime=0) as f:      # 多成员追加(合法 gzip)
                f.write(b"".join(REC.pack(*r) for r in rows))
        else:
            with open(arc_file, "ab") as f:
                f.write(b"".join(REC.pack(*r) for r in rows))
    return len(rows)


def read_bars(path, count=None, end_date=None):
    """读归档(或 vipdoc)分钟文件, 返回与 TQ market_data 同构的 {field: [..]}。

    end_date=20261015 取截至该日的数据; count 截取末 n 根; 都不传取全量。
    """
    data = _raw(path)
    rows = [REC.unpack_from(data, off)
            for off in range(0, len(data) - len(data) % 32, 32)]
    if end_date is not None:
        end_dw = _date_word(int(str(end_date)))
        rows = [r for r in rows if r[0] <= end_dw]
    if count is not None:
        rows = rows[-count:]
    out = {"Date": [], "Time": [], "Open": [], "High": [], "Low": [],
           "Close": [], "Volume": [], "Amount": []}
    for d, t, o, h, l, c, amt, vol, _, _ in rows:
        out["Date"].append(str(_date_int(d)))
        out["Time"].append(f"{t // 60:02d}{t % 60:02d}")
        out["Open"].append(o / 100)
        out["High"].append(h / 100)
        out["Low"].append(l / 100)
        out["Close"].append(c / 100)
        out["Volume"].append(vol)
        out["Amount"].append(amt)
    return out


def _date_word(date_int):
    y, mm, dd = int(str(date_int)[:4]), int(str(date_int)[4:6]), int(str(date_int)[6:8])
    return (y - 2004) * 2048 + mm * 100 + dd


def _date_int(word):
    return (2004 + word // 2048) * 10000 + (word % 2048) // 100 * 100 + (word % 2048) % 100


def day_counts(path):
    """{日期词: 根数} —— 留洞对账用, 完整一天应恰为 bars 根。"""
    data = _raw(path)
    out = {}
    for off in range(0, len(data) - len(data) % 32, 32):
        d = REC.unpack_from(data, off)[0]
        out[d] = out.get(d, 0) + 1
    return out


def do_check(code, periods):
    """按日根数对账: 根数≠整日 bars 的日期即转档留洞/半日市, 人眼复核。"""
    for period in periods:
        path = arc_path(code, period)
        tag = "归档"
        if not path.exists():
            path = vip_path(VIPDOC, code, period)
            tag = "vipdoc"
            if not path.exists():
                print(f"[{period}] {code}: 两边都没有")
                continue
        counts = day_counts(path)
        bars = PERIOD_META[period]["bars"]
        odd = {f"{_date_int(d)}": n for d, n in counts.items() if n != bars}
        days = sorted(_date_int(d) for d in counts)
        span = f"{days[0]} ~ {days[-1]}" if days else "空"
        print(f"[{period}] {code} {tag}: {len(counts)} 天 {span}; "
              f"非整日({bars}根) {odd if odd else '无'}")


def _pack_gz(periods, codes=None):
    """一次性迁移: 归档目录里裸 .bin -> .bin.gz(原子替换, 幂等)。"""
    import gzip
    for period in periods:
        folder = out_dir(period)
        if not folder.is_dir():
            continue
        n = 0
        for p in sorted(folder.glob("*.bin")):
            if codes is not None and p.stem not in codes:
                continue
            if (p.with_suffix(".bin.gz")).exists():
                continue
            raw = p.read_bytes()
            tmp = str(p) + ".gz.tmp"
            with open(tmp, "wb") as f:
                f.write(gzip.compress(raw, mtime=0))
            os.replace(tmp, str(p) + ".gz")
            p.unlink()
            n += 1
        print(f"[{period}] 迁移 {n} 个文件 -> .bin.gz (目录 {folder})")


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = sys.argv[1:]
    periods, codes = PERIODS, CODES
    if args and set(args[0].split(",")) <= set(PERIOD_META):
        want = set(args[0].split(","))
        periods = tuple(p for p in PERIODS if p in want)
        args = args[1:]
    if args and args[0] == "all":
        codes = None
        args = args[1:]
    if args and args[0] == "check":
        do_check(args[1], periods)
        return
    if args and args[0] == "pack":
        _pack_gz(periods, None if args[1:] == ["all"] else (args[1:] or None))
        return

    for period in periods:
        targets = codes if codes is not None else all_codes(VIPDOC, period)
        bars = PERIOD_META[period]["bars"]
        print(f"[{period}] 归档 {len(targets)} 只 -> {out_dir(period)}")
        added = missing = 0
        for i, code in enumerate(targets, 1):
            vip = vip_path(VIPDOC, code, period)
            if not vip.exists():
                missing += 1
            else:
                try:
                    added += append_new(vip, arc_path(code, period), bars)
                except OSError as e:
                    print(f"\n  [跳过] {code}: {e}")
            if i % 2000 == 0:
                print(f"\r  {i}/{len(targets)} 累计新增 {added} 根", end="", flush=True)
        print(f"\r  完成: 新增 {added} 根, vipdoc 缺文件 {missing} 只"
              f"(0 行也可能正常: 转档后无新数据)")


if __name__ == "__main__":
    main()
