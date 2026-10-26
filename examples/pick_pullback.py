# -*- coding: utf-8 -*-
"""配方: 缩量回调企稳选股 —— 多头排列里等回调, 缩量回踩 10 日线附近。

逻辑: 均线多头(MA5>MA10>MA20)+ 今日缩量 + 收盘贴着 MA10(±TOLER)。
"强势股回调到十日线缩量企稳"是经典买点假设; 选中后请配合 backtest_picker
验证持有收益, 不要直接当买入信号用。

用法: python examples/pick_pullback.py(参数区改池子/容差)
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tdx_local import TqClient, TqError  # noqa: E402
from tdx_local.indicators import sma, is_bull_align, is_volume_shrink  # noqa: E402

# ============================ 参数区(按需修改) ============================
SECTOR = "银行"          # 候选板块; "" = 全部沪深A股(慢)
BARS = 60
MA_SLOW = 20
TOLER = 0.03             # 收盘距 MA10 的容差(±3%)
WANT_BULL_ALIGN = True   # 先保证趋势向上
WANT_SHRINK = True       # 缩量(今日量 < 5日均量×0.7)
COUNT = 120
SEND_TO_TDX = False      # 写回自定义板块(简称必须英文)
BLOCK_CODE = "HUIDIAO"
BLOCK_NAME = "HUIDIAO"
WRITE_CSV = False
CSV_DIR = os.environ.get("TDX_PICKS_CSV_DIR",
                         str(Path(__file__).resolve().parent.parent / "picks_csv"))
# =========================================================================


def pick(val) -> bool:
    """单股判定: 参数区条件全部满足才 True。"""
    closes = [float(x) for x in val.get("Close") or []]
    vols = val.get("Volume") or []
    if len(closes) < MA_SLOW + 2:
        return False
    ma10 = sma(closes, 10)
    if ma10[-1] is None or ma10[-1] <= 0:
        return False
    if WANT_BULL_ALIGN and not is_bull_align(closes):
        return False
    if WANT_SHRINK and not is_volume_shrink(vols):
        return False
    return abs(closes[-1] / ma10[-1] - 1) <= TOLER


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    try:
        tq = TqClient()
    except TqError as e:
        print(f"TQ 不可用: {e}")
        return
    if SECTOR:
        rows = tq.call("get_stock_list_in_sector", block_code=SECTOR,
                       list_type=1).get("Value") or []
        print(f"候选板块[{SECTOR}] 共 {len(rows)} 只")
    else:
        rows = tq.call("get_stock_list", market="50", list_type=1).get("Value") or []
        print(f"候选=沪深A股 共 {len(rows)} 只")
    universe = {r["Code"]: r.get("Name", "") for r in rows if r.get("Code")}
    hits = []
    codes = sorted(universe)
    for i in range(0, len(codes), 150):
        batch = codes[i:i + 150]
        r = tq.market_data(batch, count=BARS, period="1d", dividend_type="front",
                           field_list=["Date", "Close", "Volume"])
        for code, val in (r.get("Value") or {}).items():
            if pick(val):
                closes = [float(x) for x in val["Close"]]
                chg = (closes[-1] / closes[-2] - 1) * 100 if closes[-2] else 0.0
                hits.append((code, universe.get(code, ""), closes[-1], chg))
                if len(hits) >= COUNT:
                    break
    print(f"筛出 {len(hits)} 只(缩量回踩10日线)")
    for code, name, close, chg in hits:
        print(f"  {code:<12}{name:<8}{close:>10.2f}  {chg:+.2f}%")
    if hits and SEND_TO_TDX:
        import json
        payload = {"block_code": BLOCK_CODE, "block_name": BLOCK_NAME,
                   "stocks": [c for c, *_ in hits]}
        tq.call("send_user_block", **payload)
        print(f"已写回自定义板块 {BLOCK_CODE}(客户端切换页面后可见)")
    if hits and WRITE_CSV:
        import csv
        from datetime import date
        Path(CSV_DIR).mkdir(parents=True, exist_ok=True)
        fn = Path(CSV_DIR) / f"pullback_{date.today():%Y%m%d}.csv"
        with open(fn, "w", newline="", encoding="utf-8-sig") as f:
            csv.writer(f).writerows([("code", "name", "close", "chg%")]
                                    + [(c, n, f"{p:.2f}", f"{g:+.2f}")
                                       for c, n, p, g in hits])
        print(f"已写 {fn}")


if __name__ == "__main__":
    main()
