# -*- coding: utf-8 -*-
"""配方: N字反包选股 —— 前高回调后放量再突破。

逻辑: 近 LOOKBACK 日内有过高点, 其后至少 PULLBACK_MIN 根回调
(最低价离高点回撤 >= RETRACE), 今日收盘站上该高点且放量。
N 字结构 = 涨-回调-再涨; 选中后同样建议 backtest_picker 先验证。

用法: python examples/pick_nshape.py
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tdx_local import TqClient, TqError  # noqa: E402
from tdx_local.indicators import is_volume_surge  # noqa: E402

# ============================ 参数区(按需修改) ============================
SECTOR = "银行"
BARS = 80
LOOKBACK = 20           # 前高搜索窗口(不含今日)
RETRACE = 0.03          # 高点后回调幅度下限(3%)
PULLBACK_MIN = 2        # 高点之后至少几根(避免把"创新高"当反包)
WANT_VOLUME = True      # 突破日放量
COUNT = 120
SEND_TO_TDX = False
BLOCK_CODE = "NZFB"
BLOCK_NAME = "NZFB"
WRITE_CSV = False
CSV_DIR = os.environ.get("TDX_PICKS_CSV_DIR",
                         str(Path(__file__).resolve().parent.parent / "picks_csv"))
# =========================================================================


def pick(val) -> bool:
    """单股判定: 窗口内前高 -> 回调确认 -> 今日收盘反包。"""
    closes = [float(x) for x in val.get("Close") or []]
    highs = [float(x) for x in val.get("High") or []]
    lows = [float(x) for x in val.get("Low") or []]
    vols = val.get("Volume") or []
    if len(closes) < LOOKBACK + 2:
        return False
    win_c, win_h = closes[-LOOKBACK - 1:-1], highs[-LOOKBACK - 1:-1]
    hi = max(win_h)
    i_hi = len(win_h) - 1 - win_h[::-1].index(hi)   # 最近一次触及高点的位置
    after = len(win_h) - 1 - i_hi                    # 高点之后的根数
    if after < PULLBACK_MIN:
        return False
    pull_low = min(lows[-after - 1:-1]) if after else 0.0
    if hi <= 0 or pull_low / hi - 1 > -RETRACE:
        return False                                  # 回调不够, 不是 N 字
    if closes[-1] <= hi:
        return False                                  # 尚未反包
    if WANT_VOLUME and not is_volume_surge(vols):
        return False
    return True


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
                           field_list=["Date", "Open", "High", "Low", "Close", "Volume"])
        for code, val in (r.get("Value") or {}).items():
            if pick(val):
                closes = [float(x) for x in val["Close"]]
                chg = (closes[-1] / closes[-2] - 1) * 100 if closes[-2] else 0.0
                hits.append((code, universe.get(code, ""), closes[-1], chg))
                if len(hits) >= COUNT:
                    break
    print(f"筛出 {len(hits)} 只(N字反包)")
    for code, name, close, chg in hits:
        print(f"  {code:<12}{name:<8}{close:>10.2f}  {chg:+.2f}%")
    if hits and SEND_TO_TDX:
        tq.call("send_user_block", block_code=BLOCK_CODE, block_name=BLOCK_NAME,
                stocks=[c for c, *_ in hits])
        print(f"已写回自定义板块 {BLOCK_CODE}")
    if hits and WRITE_CSV:
        import csv
        from datetime import date
        Path(CSV_DIR).mkdir(parents=True, exist_ok=True)
        fn = Path(CSV_DIR) / f"nshape_{date.today():%Y%m%d}.csv"
        with open(fn, "w", newline="", encoding="utf-8-sig") as f:
            csv.writer(f).writerows([("code", "name", "close", "chg%")]
                                    + [(c, n, f"{p:.2f}", f"{g:+.2f}")
                                       for c, n, p, g in hits])
        print(f"已写 {fn}")


if __name__ == "__main__":
    main()
