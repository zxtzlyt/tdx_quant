# -*- coding: utf-8 -*-
"""配方: 板块动量榜 —— 按板块成分近 N 日涨幅中位数给板块排序, 找强势方向。

成分来源: 本机通达信板块文件(tdx_local.sectors, 离线); 行情: TQ 批量日线。
输出: 板块动量 TopK(成分涨幅中位数)+ 每板块领涨股; 板块数多时首跑较慢。

用法: python examples/pick_sector_momentum.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tdx_local import TqClient, TqError, sectors  # noqa: E402

# ============================ 参数区(按需修改) ============================
T0002 = sectors.default_t0002()      # 本机 T0002 目录
BLOCK_KEYWORDS = ("融资融券",)       # 只统计含关键词的板块; () = hq_cache 全部(上千个, 慢!)
WINDOW = 20           # 动量窗口(交易日)
TOPK = 15             # 展示前 K 个板块
MIN_MEMBERS = 10      # 成分少于该数的板块不计
BARS = WINDOW + 5
# =========================================================================


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    blocks = sectors.read_hq_blocks(Path(T0002) / "hq_cache")
    if BLOCK_KEYWORDS:
        blocks = {n: c for n, c in blocks.items()
                  if any(k in n for k in BLOCK_KEYWORDS)}
    blocks = {n: c for n, c in blocks.items() if len(c) >= MIN_MEMBERS}
    if not blocks:
        print("没有可用板块: 检查 T0002 目录或 BLOCK_KEYWORDS")
        return
    print(f"候选板块 {len(blocks)} 个(成分≥{MIN_MEMBERS}), 动量窗口 {WINDOW} 日")
    tq = TqClient()

    all_codes = sorted({c for codes in blocks.values() for c in codes})
    mom = {}
    for i in range(0, len(all_codes), 150):
        batch = all_codes[i:i + 150]
        r = tq.market_data(batch, count=BARS, period="1d", dividend_type="front",
                           field_list=["Date", "Close"])
        for code, val in (r.get("Value") or {}).items():
            closes = [float(x) for x in val.get("Close") or []]
            if len(closes) > WINDOW and closes[-WINDOW - 1] > 0:
                mom[code] = (closes[-1] / closes[-WINDOW - 1] - 1) * 100
    rows = []
    for name, codes in blocks.items():
        vals = [mom[c] for c in codes if c in mom]
        if len(vals) < MIN_MEMBERS // 2:
            continue
        vals.sort(reverse=True)
        med = vals[len(vals) // 2]
        leader = max(codes, key=lambda c: mom.get(c, -1e9))
        rows.append((med, len(vals), name, leader, mom.get(leader, 0.0)))
    rows.sort(reverse=True)
    print(f"\n板块动量榜(近 {WINDOW} 日涨幅中位数, Top {TOPK}):")
    for med, n, name, leader, lret in rows[:TOPK]:
        print(f"  {med:+7.2f}%  {name:<14}(成分{n:>3})  领涨 {leader} {lret:+.2f}%")


if __name__ == "__main__":
    main()
