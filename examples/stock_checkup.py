# -*- coding: utf-8 -*-
"""配方4: 单股一键体检 —— 输入代码, 生成行情/技术面/财务/分红综合报告。

数据通路全部走 TQ HTTP(客户端需在运行)。其中"分红再投总回报"用的是
LOCAL_NOTES 验证过的正确口径: 不复权价格链 + divid_factors 分红再投
(前复权价在高分红股上会算出负数, 不能用于收益率)。

用法: python examples/stock_checkup.py [代码, 默认 600000.SH]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tdx_local import TqClient, TqError  # noqa: E402


def ma(values, n):
    if len(values) < n:
        return None
    return sum(values[-n:]) / n


def macd_state(closes):
    """自算 MACD(12,26,9), 返回 '金叉/死叉/多头/空头'。"""
    def ema(vals, n):
        k, out = 2 / (n + 1), [vals[0]]
        for v in vals[1:]:
            out.append(v * k + out[-1] * (1 - k))
        return out
    dif = [a - b for a, b in zip(ema(closes, 12), ema(closes, 26))]
    dea = ema(dif, 9)
    if dif[-1] > dea[-1] and dif[-2] <= dea[-2]:
        return "金叉"
    if dif[-1] < dea[-1] and dif[-2] >= dea[-2]:
        return "死叉"
    return "多头" if dif[-1] > dea[-1] else "空头"


def total_return_with_dividends(closes, dates, dividends, years=5):
    """近 years 年: 纯价格回报 vs 分红再投总回报(%)。

    dividends: {除息日YYYYMMDD: 每股税前派息元}。买入日起每个除息日把
    现金分红按当日收盘价再投入。与 LOCAL_NOTES 茅台口径一致。
    窗口锚定在数据末端(末端年份-years), 本地数据起点不足5年也能对齐。
    """
    if not closes:
        return None, None, 0
    cut = int(str(dates[-1])[:4]) - years
    idx0 = next((i for i, d in enumerate(dates) if int(str(d)[:4]) >= cut), 0)
    seg_d, seg_c = dates[idx0:], closes[idx0:]
    if len(seg_c) < 2:
        return None, None, 0
    price_ret = (seg_c[-1] / seg_c[0] - 1) * 100

    shares, cash, n_div = 1.0, 0.0, 0
    for d, c in zip(seg_d, seg_c):
        div = dividends.pop(str(d), 0.0)
        if div:
            n_div += 1
            cash += shares * div
            if c > 0:
                shares += cash / c
                cash = 0.0
    total_ret = (shares * seg_c[-1] + cash) / seg_c[0] - 1
    return price_ret, total_ret * 100, n_div


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    code = sys.argv[1] if len(sys.argv) > 1 else "600000.SH"
    tq = TqClient()

    names = tq.match(code.split(".")[0])
    name = names[0]["Name"] if names else "?"
    print(f"====== {code} {name} 体检报告 ======")

    # ---- 行情与技术面(前复权, 指标口径) ----
    r = tq.market_data([code], count=1250, period="1d", dividend_type="front",
                       field_list=["Date", "Close", "Volume"])
    val = (r.get("Value") or {}).get(code) or {}
    closes = [float(x) for x in val.get("Close") or []]
    if closes:
        y1 = closes[-245:] or closes
        print(f"现价 {closes[-1]:.2f} | 近一年低/高 {min(y1):.2f}/{max(y1):.2f} "
              f"({(y1[-1] / y1[0] - 1) * 100:+.1f}%)")
        print(f"MA5 {ma(closes, 5):.2f} / MA20 {ma(closes, 20):.2f} / "
              f"MA60 {ma(closes, 60):.2f}" if ma(closes, 60) else "")
        print(f"MACD 状态: {macd_state(closes)}")
    else:
        print("[提示] 本地无该股日K —— 可在客户端打开该股页面后再跑")

    # ---- 财务(近几个报告期, 累计口径) ----
    fields = ["FN1", "FN4", "FN74", "FN96"]
    r = tq.paged("get_financial_data", stock_list=[code],
                 field_list=fields, table_list=fields,
                 report_type="tag_time",
                 start_time="20230101", end_time="20261231")
    per = (r.get("Value") or {}).get(code) or {}
    tags = per.get("tag_time") or []
    if tags:
        print("\n财报(累计口径):")
        print(f"{'报告期':<10}{'每股收益':>8}{'每股净资产':>10}{'营收(亿)':>9}{'归母净利(亿)':>11}")
        for i, d in enumerate(tags[-6:]):
            def f(fn):
                try:
                    return float(per[fn][i])
                except (KeyError, TypeError, ValueError, IndexError):
                    return float("nan")
            print(f"{d:<10}{f('FN1'):>8.2f}{f('FN4'):>10.2f}"
                  f"{f('FN74') / 1e8:>9.1f}{f('FN96') / 1e8:>11.2f}")

    # ---- 股息率与分红再投总回报 ----
    r = tq.call("get_gpjy_value", stock_list=[code],
                field_list=["GP21"], table_list=["GP21"],
                start_time="", end_time="")
    gp21 = ((r.get("Value") or {}).get(code) or {}).get("GP21") or []
    if gp21:
        print(f"\n当前股息率: {float(gp21[-1]['Value'][0]):.2f}%")

    divs = tq.divid_factors(code)
    if closes and divs:
        # 总回报用不复权价格链(前复权在高分红股会算出负价, 见 LOCAL_NOTES)
        r2 = tq.market_data([code], count=1250, period="1d",
                            dividend_type="none", field_list=["Date", "Close"])
        val2 = (r2.get("Value") or {}).get(code) or {}
        raw_c = [float(x) for x in val2.get("Close") or []]
        raw_d = [int(d) for d in val2.get("Date") or []]
        p_ret, t_ret, n_div = total_return_with_dividends(raw_c, raw_d, dict(divs))
        if p_ret is not None:
            print(f"近5年: 纯价格回报 {p_ret:+.1f}% | "
                  f"分红再投总回报 {t_ret:+.1f}% (期间分红 {n_div} 次)")

    # ---- 基础信息快照(J_ 字段, 金额单位万元) ----
    info = tq.stock_info(code)
    j = {k: info.get(k) for k in ("J_gdrs", "J_mgsy", "J_mgjzc")
         if info.get(k) not in (None, "")}
    if j:
        parts = []
        if j.get("J_gdrs") is not None:
            parts.append(f"股东人数 {float(j['J_gdrs']):,.0f}")
        if j.get("J_mgsy") is not None:
            parts.append(f"每股收益 {float(j['J_mgsy']):.3f}")
        if j.get("J_mgjzc") is not None:
            parts.append(f"每股净资产 {float(j['J_mgjzc']):.2f}")
        print("基本信息: " + " | ".join(parts))
    print("====== 报告完(数据=本地客户端, 非投资建议) ======")


if __name__ == "__main__":
    try:
        main()
    except TqError as e:
        print(f"\n[出错] {e}")
        print("请确认通达信金融终端已启动并登录(TQ 服务 http://127.0.0.1:17709/),"
              "环境要求见 README『快速开始』。")
        sys.exit(1)
