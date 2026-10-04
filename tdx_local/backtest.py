# -*- coding: utf-8 -*-
"""选股策略回测(point-in-time 重放) —— 回答"这个策略历史上管不管用"。

正确性设计(每一条都来自 docs/LOCAL_NOTES.md 的实测教训):

  1. **数据窗口按调仓日切片**: 策略在每个调仓日 T 只能看到日期 <= T 的K线
     (slice_asof 按 end_date 截断), 从构造上杜绝未来函数(有回归测试)。
  2. **收益 = 不复权价 + 分红事件再投**: forward_return 与
     indicators.total_return_with_dividends 同口径(茅台 12.49 倍互证)。
     禁止用前复权价算收益 —— 高分红股会算出负价; 后复权随窗口起点漂移,
     跨窗口拼接必错。
  3. **指标在原始价上算**: 缓存/回放数据是不复权的, 策略指标也应在同一
     序列上算 —— "当时的前复权"无法从今天的复权序列复原, 原始价才是
     point-in-time 保真的。

用法::

    from tdx_local import backtest

    result = backtest.run(bars_by_code, rebalance_dates,
                          strategy=lambda asof: [c for c in my_universe
                                                 if ind.is_bull_align(asof[c]["Close"])],
                          horizons=(5, 20, 60),
                          dividends_by_code=divs, benchmark="999999.SH")
    print(backtest.report(result))
"""
import statistics

HORIZONS = (5, 20, 60)          # 默认前向持有期(交易日)
WINDOW = 80                     # 传给策略的 as-of 窗口根数(够算 MA20 类指标)


def slice_asof(bars, end_date, window=WINDOW):
    """列式 bars -> 截至 end_date(含)的末端 window 根; 全过期返回空结构。"""
    dates = bars.get("Date") or []
    cut = next((i for i in range(len(dates)) if dates[i] > end_date), len(dates))
    lo = max(0, min(cut - window if window else cut, cut))
    return {k: list(v[lo:cut]) for k, v in bars.items()}


def make_rebalances(calendar, last_n=250, step=10):
    """交易日历 -> 调仓日列表: 末端 last_n 根里每隔 step 根取一个(含末端)。"""
    cal = list(calendar)
    if not cal:
        return []
    idx = list(range(0, len(cal), step))
    if idx[-1] != len(cal) - 1:
        idx.append(len(cal) - 1)
    return [cal[i] for i in idx[-last_n // step - 1:]]


def forward_return(dates, closes, buy_idx, horizon, dividends=None):
    """T=buy_idx 收盘买入, 持有 horizon 个交易日 -> 期间总回报%(分红再投)。

    分红事件取除息日位置在 (buy_idx, sell_idx] 的行 —— 买入当日除息的
    分红属于前手, 不计。数据不足(卖不出)返回 None。
    """
    sell = buy_idx + horizon
    if sell >= len(closes) or buy_idx < 0 or closes[buy_idx] <= 0:
        return None
    shares, cash = 1.0, 0.0
    if dividends:
        for j in range(buy_idx + 1, sell + 1):
            div = dividends.get(str(dates[j]), 0.0)
            if div:
                cash += shares * div
                if closes[j] > 0:
                    shares += cash / closes[j]
                    cash = 0.0
    return ((shares * closes[sell] + cash) / closes[buy_idx] - 1) * 100


def run(bars_by_code, rebalance_dates, strategy, horizons=HORIZONS,
        dividends_by_code=None, benchmark=None, window=WINDOW) -> dict:
    """重放主入口。

    bars_by_code: {code: 列式全历史bars}(不复权; kcache.read_many 或 TQ 整段)。
    rebalance_dates: 调仓日(YYYYMMDD int, 升序), 通常取基准日历 make_rebalances。
    strategy: pick(asof_bars) -> [code] 纯函数; asof_bars 里每只都是
              slice_asof 切片(<=T), 策略从这里选票 —— 只能用这个参数,
              不要闭包引用外部实时数据, 否则防未来函数失效。
    dividends_by_code: {code: {除息日str: 每股派息}}, 或 callable(code)->同结构
              (逐股惰性调用并记忆化, 可直接传 TqClient.divid_factors)。
    benchmark: 基准代码(须在 bars_by_code 里), 计算逐笔超额。

    返回 {"picks": [...], "bench": {T: {h: %}}, "skipped": {code: 次}, "summary": {...}}。
    """
    positions = {c: {d: i for i, d in enumerate(b["Date"])}
                 for c, b in bars_by_code.items()}
    div_memo = {}

    def dividends_of(code):
        if code not in div_memo:
            if callable(dividends_by_code):
                div_memo[code] = dividends_by_code(code) or {}
            else:
                div_memo[code] = (dividends_by_code or {}).get(code) or {}
        return div_memo[code]

    bench_ret = {}
    if benchmark and benchmark in bars_by_code:
        bd, bc = bars_by_code[benchmark]["Date"], bars_by_code[benchmark]["Close"]
        bpos = positions[benchmark]
        for T in rebalance_dates:
            if T in bpos:
                bench_ret[T] = {h: forward_return(bd, bc, bpos[T], h)
                                for h in horizons}

    picks, skipped = [], {}
    for T in rebalance_dates:
        asof = {c: slice_asof(b, T, window) for c, b in bars_by_code.items()}
        for code in strategy(asof):
            bars = bars_by_code.get(code)
            pos = positions.get(code, {}).get(T)
            if bars is None or pos is None:      # 候选日停牌/无本地数据
                skipped[code] = skipped.get(code, 0) + 1
                continue
            divs = dividends_of(code)
            ret = {h: forward_return(bars["Date"], bars["Close"], pos, h, divs)
                   for h in horizons}
            excess = ({h: (None if r is None or bench_ret.get(T, {}).get(h) is None
                           else r - bench_ret[T][h]) for h, r in ret.items()}
                      if benchmark else {})
            picks.append({"date": T, "code": code, "ret": ret, "excess": excess})
    return {"picks": picks, "bench": bench_ret, "skipped": skipped,
            "summary": summarize(picks, horizons)}


def summarize(picks, horizons=HORIZONS) -> dict:
    """逐笔 -> 每个持有期的 {n, win%, avg%, med%, avg_excess%, best, worst}。"""
    out = {}
    for h in horizons:
        rets = [(p["code"], p["date"], p["ret"][h]) for p in picks
                if p["ret"].get(h) is not None]
        exc = [p["excess"][h] for p in picks
               if p.get("excess", {}).get(h) is not None]
        if not rets:
            out[h] = {"n": 0}
            continue
        vals = [r for _, _, r in rets]
        best = max(rets, key=lambda x: x[2])
        worst = min(rets, key=lambda x: x[2])
        out[h] = {"n": len(vals),
                  "win": sum(v > 0 for v in vals) / len(vals) * 100,
                  "avg": statistics.fmean(vals),
                  "med": statistics.median(vals),
                  "avg_excess": statistics.fmean(exc) if exc else None,
                  "excess_win": (sum(e > 0 for e in exc) / len(exc) * 100)
                                if exc else None,
                  "best": best, "worst": worst}
    return out


def report(result, top=5) -> str:
    """回测结果 -> 中文文本报告(配方输出风格)。"""
    s = result["summary"]
    lines = [f"共 {len(result['picks'])} 笔选股(去重前), "
             f"无法成交跳过 {sum(result['skipped'].values())} 次"]
    lines.append(f"{'持有期':>6}{'笔数':>6}{'胜率%':>8}{'平均%':>8}{'中位%':>8}"
                 f"{'平均超额%':>10}{'超额胜率%':>10}")
    for h, m in s.items():
        if m.get("n", 0) == 0:
            lines.append(f"{h:>4}日       0     --      --      --         --         --")
            continue
        ae = f"{m['avg_excess']:>+10.2f}" if m["avg_excess"] is not None else "        --"
        ew = f"{m['excess_win']:>9.1f}%" if m["excess_win"] is not None else "        --"
        lines.append(f"{h:>4}日{m['n']:>6}{m['win']:>8.1f}{m['avg']:>+8.2f}"
                     f"{m['med']:>+8.2f}{ae}{ew}")
        lines.append(f"      最好: {m['best'][0]} @{m['best'][1]} {m['best'][2]:+.2f}%"
                     f" | 最差: {m['worst'][0]} @{m['worst'][1]} {m['worst'][2]:+.2f}%")
    return "\n".join(lines)
