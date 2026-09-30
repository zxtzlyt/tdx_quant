# -*- coding: utf-8 -*-
"""配方3: 板块与市场概览 —— 一屏看清市场生态。

内容:
  1. 申万一级行业板块近5日涨跌幅排名(谁强谁弱)
  2. 全A 市盈率(TTM, 整体法) 与 板块总市值
  3. 沪深两融余额近10日走势

用法: python examples/market_overview.py
"""
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tdx_local import TqClient  # noqa: E402

TOP_N = 10           # 最强/最弱各显示 N 个板块
RECENT_DAYS = 5      # 板块强弱统计窗口(交易日)


def sector_changes(closes_by_code):
    """{板块代码: 收盘序列} -> {板块代码: 近RECENT_DAYS日涨跌幅%}。"""
    out = {}
    for code, closes in closes_by_code.items():
        if len(closes) > RECENT_DAYS and closes[-RECENT_DAYS - 1]:
            out[code] = (closes[-1] / closes[-RECENT_DAYS - 1] - 1) * 100
    return out


def print_ranks(title, pairs, desc=True):
    pairs = sorted(pairs, key=lambda x: -x[1])[:TOP_N] if desc else \
        sorted(pairs, key=lambda x: x[1])[:TOP_N]
    print(f"\n{title}")
    for (code, name), chg in pairs:
        bar = "#" * max(1, int(abs(chg) * 2))
        print(f"  {code:<10}{name:<8}{chg:>+7.2f}%  {bar}")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    tq = TqClient()

    # ---- 1. 行业板块强弱(申万一级行业 = 881xxx 板块指数) ----
    rows = tq.call("get_stock_list", market="16", list_type=1).get("Value") or []
    sectors = {r["Code"]: r["Name"] for r in rows if r.get("Code")}
    print(f"行业板块 {len(sectors)} 个, 取近 {RECENT_DAYS} 日行情...")
    r = tq.market_data(sorted(sectors), count=RECENT_DAYS + 3, period="1d",
                       dividend_type="front", field_list=["Close"])
    closes = {c: [float(x) for x in v.get("Close") or []]
              for c, v in (r.get("Value") or {}).items()}
    changes = sector_changes(closes)
    pairs = sorted(((c, sectors[c]), chg) for c, chg in changes.items()
                   if c in sectors)
    print_ranks(f"近{RECENT_DAYS}日最强板块 TOP{TOP_N}:", [p for p in pairs])
    print_ranks(f"近{RECENT_DAYS}日最弱板块 TOP{TOP_N}:", [p for p in pairs], desc=False)

    # ---- 2. 全A 估值(880001=全部A股市盈率TTM 整体法) ----
    d30 = (date.today() - timedelta(days=40)).strftime("%Y%m%d")
    today = date.today().strftime("%Y%m%d")
    r = tq.call("get_bkjy_value", stock_list=["880001.SH"],
                field_list=["BK5", "BK10"], table_list=["BK5", "BK10"],
                start_time=d30, end_time=today)
    rec = (r.get("Value") or {}).get("880001.SH") or {}
    bk5 = rec.get("BK5") or []
    bk10 = rec.get("BK10") or []
    if bk5:
        pe = float(bk5[-1]["Value"][0])
        cap = float(bk10[-1]["Value"][0]) / 1e4 if bk10 else 0.0   # 亿元 -> 万亿
        print(f"\n全A 市盈率TTM(整体法): {pe:.2f} 倍    总市值: {cap:.1f} 万亿")

    # ---- 3. 两融余额(SC1, 单位万元)近10日 ----
    r = tq.call("get_scjy_value", field_list=["SC1"], table_list=["SC1"],
                start_time=d30, end_time=today)
    sc1 = (r.get("Value") or {}).get("SC1") or []
    if sc1:
        tail = sc1[-10:]
        print("\n沪深两融余额(近10个交易日, 亿元):")
        for row in tail:
            print(f"  {row['Date']}  {float(row['Value'][0]) / 1e4:>9.0f}")
        first, last = float(tail[0]["Value"][0]), float(tail[-1]["Value"][0])
        trend = "增加" if last > first else "减少"
        print(f"  10日合计{trend}: {(last - first) / 1e4:+.0f} 亿元")


if __name__ == "__main__":
    main()
