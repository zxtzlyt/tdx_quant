# -*- coding: utf-8 -*-
"""分钟线归档器 —— 每天收盘后跑一次, 把关注池的分钟K增量追加进本地 CSV。

痛点: 通达信客户端本地分钟数据只有约 100 天留存(docs/LOCAL_NOTES.md 实测),
过了窗口历史就永远拿不到了(东财等免费通道均已封)。本脚本用 TQ 取"本地
还留存的全部分钟线", 按 (Date, Time) 去重后追加进 CSV —— 坚持每天跑,
深度随时间自然增长, 突破 100 天上限。

用法: python examples/archive_minutes.py        # 池子在下面参数区改
      配合任务计划程序每个交易日 15:30 跑一次效果最佳。
"""
import csv
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tdx_local import TqClient, TqError  # noqa: E402

# ============================ 参数区(按需修改) ============================
PERIOD = "5m"            # "1m"(约100天留存) / "5m" / "15m" / "30m" / "60m"
CODES = [                # 关注池(通达信代码); 改成你的自选股
    "999999.SH", "399001.SZ", "880001.SH",
    "600000.SH", "600519.SH", "000001.SZ", "300750.SZ",
]
# 输出目录: 环境变量 TDX_KCACHE_MIN_DIR, 缺省 <仓库根>/kcache_min/<PERIOD>/
# ========================================================================

COLS = ("Date", "Time", "Open", "High", "Low", "Close", "Volume", "Amount")


def out_dir(period):
    env = os.environ.get("TDX_KCACHE_MIN_DIR")
    base = env or str(Path(__file__).resolve().parent.parent / "kcache_min")
    return Path(base) / period


def archive_code(tq, code, period, folder) -> int:
    """归档单只: 返回本次新增行数。文件按 (Date,Time) 去重增量追加。"""
    r = tq.market_data([code], count=-1, period=period,
                       dividend_type="none", field_list=list(COLS))
    val = (r.get("Value") or {}).get(code)
    if not isinstance(val, dict) or not val.get("Date"):
        return 0
    cols = {k: [str(x) for x in (val.get(k) or [])] for k in COLS}
    rows = sorted(zip(*(cols[k] for k in COLS)), key=lambda t: (t[0], t[1]))

    market, num = code.split(".")[-1].lower(), code.split(".")[0]
    path = folder / f"{market}{num}.csv"
    have = set()
    if path.exists():
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                have.add((row["Date"], row["Time"]))
    fresh = [t for t in rows if (t[0], t[1]) not in have]
    if not fresh:
        return 0
    folder.mkdir(parents=True, exist_ok=True)
    is_new = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if is_new:
            w.writerow(COLS)
        w.writerows(fresh)
    return len(fresh)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    tq = TqClient()
    folder = out_dir(PERIOD)
    print(f"归档 {PERIOD} 分钟线 -> {folder} ({len(CODES)} 只)")
    total = 0
    for code in CODES:
        try:
            n = archive_code(tq, code, PERIOD, folder)
        except TqError as e:
            print(f"  [跳过] {code}: {e}")
            continue
        total += n
        print(f"  {code:<12} 新增 {n} 行")
    print(f"合计新增 {total} 行(0 行也可能正常: 盘中已归档过)")


if __name__ == "__main__":
    try:
        main()
    except TqError as e:
        print(f"\n[出错] {e}")
        print("请确认通达信金融终端已启动并登录(TQ 服务 http://127.0.0.1:17709/),"
              "环境要求见 README『快速开始』。")
        sys.exit(1)
