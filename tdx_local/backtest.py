# -*- coding: utf-8 -*-
"""选股策略回测(point-in-time 重放) —— 回答"这个策略历史上管不管用"。

正确性设计(每一条都来自 docs/LOCAL_NOTES.md 的实测教训):

  1. **数据窗口按调仓日切片**: 策略在每个调仓日 T 只能看到日期 <= T 的K线
     (slice_asof 按 end_date 截断), 从构造上杜绝未来函数(有回归测试)。
  2. **收益 = 不复权价 + 分红/送转事件再投**: forward_return 与
     indicators.total_return_with_dividends 同口径(茅台 12.49 倍互证;
     送转必须进模型, 否则"10送10"标的除权日腰斩而股本没补 —— 2026-10-27
     起 forward_return/run 均支持 splits, 顺序: 派息按送转前股本 -> 扩股本
     -> 现金按除权价再投)。禁止用前复权价算收益 —— 高分红股会算出负价;
     后复权随窗口起点漂移, 跨窗口拼接必错。
  3. **指标在原始价上算**: 缓存/回放数据是不复权的, 策略指标也应在同一
     序列上算 —— "当时的前复权"无法从今天的复权序列复原, 原始价才是
     point-in-time 保真的。
  4. **交易成本(2026-10-27)**: cost_in/cost_out 为买卖双边比例成本, 净收益
     = 毛收益 × (1-cost_out) / (1+cost_in) - 1(全仓进出近似)。A股建议
     commission=0.00025(双边)、stamp_tax=0.0005(仅卖出)、slippage 自定;
     run(commission=..., stamp_tax=..., slippage=...) 会折算好。基准收益
     不含成本(指数口径), 超额=含成本个股-不含成本基准, 天然保守。

用法::

    from tdx_local import backtest

    result = backtest.run(bars_by_code, rebalance_dates,
                          strategy=lambda asof: [c for c in my_universe
                                                 if ind.is_bull_align(asof[c]["Close"])],
                          horizons=(5, 20, 60),
                          dividends_by_code=tq.divid_factors,
                          splits_by_code=tq.divid_splits,
                          commission=0.00025, stamp_tax=0.0005,
                          benchmark="999999.SH")
    print(backtest.report(result))
    print(backtest.report_yearly(result))
"""
import statistics
from bisect import bisect_right

HORIZONS = (5, 20, 60)          # 默认前向持有期(交易日)
WINDOW = 80                     # 传给策略/卖出规则的 as-of 窗口根数(够算 MA20 类指标)
A_SHARE_COSTS = {"commission": 0.00025, "stamp_tax": 0.0005, "slippage": 0.0}


def slice_asof(bars, end_date, window=WINDOW):
    """列式 bars -> 截至 end_date(含)的末端 window 根; 全过期返回空结构。

    bars["Date"] 须升序无重复(kcache/lday 落盘与 TQ 返回皆然)——
    二分定位截断点, 单次 O(log n), 全市场×全调仓日的重放规模才跑得动
    (2026-10-05 实测: 400只×201调仓日由 4.2s 降至 0.3s 量级)。
    """
    dates = bars.get("Date") or []
    cut = bisect_right(dates, end_date)
    lo = max(0, cut - window) if window else 0
    return {k: v[lo:cut] for k, v in bars.items()}   # 切片本身即新列表, 免二次复制


def make_rebalances(calendar, last_n=250, step=10):
    """交易日历 -> 调仓日列表: 末端 last_n 根里每隔 step 根取一个(含末端)。"""
    cal = list(calendar)
    if not cal:
        return []
    idx = list(range(0, len(cal), step))
    if idx[-1] != len(cal) - 1:
        idx.append(len(cal) - 1)
    return [cal[i] for i in idx[-last_n // step - 1:]]


def forward_return(dates, closes, buy_idx, horizon, dividends=None, splits=None,
                   cost_in=0.0, cost_out=0.0, sell_rule=None, bars=None,
                   window=WINDOW):
    """T=buy_idx 收盘买入, 持有 horizon 个交易日 -> 期间净回报%。

    分红/送转事件取除权除息日位置在 (buy_idx, sell_idx] 的行 —— 买入当日
    除息的归属前手, 不计; 处理顺序同真实业务(派息按送转前股本 -> 扩股本 ->
    现金按除权日收盘再投)。cost_in/cost_out: 买卖双边比例成本, 净收益 =
    毛收益×(1-cost_out)/(1+cost_in) - 1(全仓进出近似)。
    sell_rule(asof, held_days) -> bool: 持有期内逐日检查(截至当日含收盘的
    window 切片), 触发即提前卖出; 需同时传 bars(列式全历史)。数据不足
    (卖不出)返回 None。
    """
    sell = buy_idx + horizon
    if sell >= len(closes) or buy_idx < 0 or closes[buy_idx] <= 0:
        return None
    sell_i = sell
    if sell_rule is not None:
        if bars is None:
            raise TypeError("sell_rule 需要同时传 bars(列式全历史)")
        for j in range(buy_idx + 1, sell + 1):
            lo = max(0, j + 1 - window)
            asof = {k: v[lo:j + 1] for k, v in bars.items()}
            if sell_rule(asof, j - buy_idx):
                sell_i = j
                break
    shares, cash = 1.0, 0.0
    for j in range(buy_idx + 1, sell_i + 1):
        split = splits.get(str(dates[j]), 0.0) if splits else 0.0
        div = dividends.get(str(dates[j]), 0.0) if dividends else 0.0
        if div:
            cash += shares * div
        if split:
            shares *= 1.0 + split
        if div and closes[j] > 0:
            shares += cash / closes[j]
            cash = 0.0
    gross = shares * closes[sell_i] + cash
    if cost_in or cost_out:
        return (gross * (1.0 - cost_out) / closes[buy_idx] / (1.0 + cost_in) - 1) * 100
    return (gross / closes[buy_idx] - 1) * 100


def _trade(bars, buy_idx, horizon, dividends=None, splits=None,
           cost_in=0.0, cost_out=0.0, sell_rule=None, window=WINDOW):
    """forward_return 的内部完整版: 额外返回 (net_ret, sell_date, early)。

    sell_date 为实际卖出日(YYYYMMDD int), 数据不足返回 None;
    early=True 表示被 sell_rule 提前触发。净口径与 forward_return 完全一致。
    """
    dates, closes = bars["Date"], bars["Close"]
    sell = buy_idx + horizon
    if sell >= len(closes) or buy_idx < 0 or closes[buy_idx] <= 0:
        return None, None, False
    sell_i, early = sell, False
    if sell_rule is not None:
        for j in range(buy_idx + 1, sell + 1):
            lo = max(0, j + 1 - window)
            asof = {k: v[lo:j + 1] for k, v in bars.items()}
            if sell_rule(asof, j - buy_idx):
                sell_i, early = j, True
                break
    shares, cash = 1.0, 0.0
    for j in range(buy_idx + 1, sell_i + 1):
        split = splits.get(str(dates[j]), 0.0) if splits else 0.0
        div = dividends.get(str(dates[j]), 0.0) if dividends else 0.0
        if div:
            cash += shares * div
        if split:
            shares *= 1.0 + split
        if div and closes[j] > 0:
            shares += cash / closes[j]
            cash = 0.0
    gross = shares * closes[sell_i] + cash
    if cost_in or cost_out:
        net = (gross * (1.0 - cost_out) / closes[buy_idx] / (1.0 + cost_in) - 1) * 100
    else:
        net = (gross / closes[buy_idx] - 1) * 100
    return net, dates[sell_i], early


def run(bars_by_code, rebalance_dates, strategy, horizons=HORIZONS,
        dividends_by_code=None, splits_by_code=None, benchmark=None,
        window=WINDOW, commission=0.0, stamp_tax=0.0, slippage=0.0,
        sell_rule=None) -> dict:
    """重放主入口。

    bars_by_code: {code: 列式全历史bars}(不复权; kcache.read_many 或 TQ 整段)。
    rebalance_dates: 调仓日(YYYYMMDD int, 升序), 通常取基准日历 make_rebalances。
    strategy: pick(asof_bars) -> [code] 纯函数; asof_bars 里每只都是
              slice_asof 切片(<=T), 策略从这里选票 —— 只能用这个参数,
              不要闭包引用外部实时数据, 否则防未来函数失效。
    dividends_by_code / splits_by_code: {code: {日期str: 值}}, 或 callable(code)
              (逐股惰性调用并记忆化, 可直接传 TqClient.divid_factors /
              divid_splits)。
    commission/stamp_tax/slippage: 比例成本; 折算 cost_in = slippage+commission,
              cost_out = slippage+commission+stamp_tax(印花税仅卖出)。
              A股建议见 A_SHARE_COSTS。基准收益不含成本。
    sell_rule(asof, held_days) -> bool: 持有期内逐日检查, 触发提前卖出
              (horizon 仍是上限); 各持有期独立判定。
    日期->下标映射只为基准与实际被选中的代码惰性建立 —— 全市场回测时
    未被选中的数千只不再各建一张映射, 省内存也省建表时间。

    返回 {"picks": [...(含 sell_date/early)], "bench": {T: {h: %}},
          "skipped": {code: 次}, "summary": {...}, "yearly": {...},
          "curve": {h: [(sell_date, nav)]}}。
    """
    cost_in = slippage + commission
    cost_out = slippage + commission + stamp_tax
    _pos_memo = {}

    def _pos(code):
        if code not in _pos_memo:
            _pos_memo[code] = {d: i for i, d in enumerate(bars_by_code[code]["Date"])}
        return _pos_memo[code]

    def _memo(code, source, cache):
        if code not in cache:
            if callable(source):
                cache[code] = source(code) or {}
            else:
                cache[code] = (source or {}).get(code) or {}
        return cache[code]

    div_memo, spl_memo = {}, {}

    bench_ret = {}
    if benchmark and benchmark in bars_by_code:
        bd, bc = bars_by_code[benchmark]["Date"], bars_by_code[benchmark]["Close"]
        for T in rebalance_dates:
            i = _pos(benchmark).get(T)
            if i is not None:
                bench_ret[T] = {h: forward_return(bd, bc, i, h)
                                for h in horizons}

    picks, skipped = [], {}
    for T in rebalance_dates:
        asof = {c: slice_asof(b, T, window) for c, b in bars_by_code.items()}
        for code in strategy(asof):
            if code not in bars_by_code or T not in _pos(code):
                skipped[code] = skipped.get(code, 0) + 1    # 候选日停牌/无本地数据
                continue
            bars = bars_by_code[code]
            pos = _pos(code)[T]
            divs = _memo(code, dividends_by_code, div_memo)
            spls = _memo(code, splits_by_code, spl_memo)
            ret, early = {}, {}
            for h in horizons:
                net, sell_date, is_early = _trade(
                    bars, pos, h, divs, spls, cost_in, cost_out, sell_rule, window)
                ret[h] = net
                if sell_date is not None:
                    early[h] = (sell_date, is_early)
            excess = ({h: (None if r is None or bench_ret.get(T, {}).get(h) is None
                           else r - bench_ret[T][h]) for h, r in ret.items()}
                      if benchmark else {})
            sell_map = {h: v[0] for h, v in early.items()}
            picks.append({"date": T, "code": code, "ret": ret, "excess": excess,
                          "sell_date": sell_map,
                          "early": {h: v[1] for h, v in early.items() if v[1]}})
    result = {"picks": picks, "bench": bench_ret, "skipped": skipped,
              "summary": summarize(picks, horizons)}
    result["yearly"] = yearly(picks, horizons)
    result["curve"] = equity_curve(picks, horizons)
    return result


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


def yearly(picks, horizons=HORIZONS) -> dict:
    """逐笔按卖出日年份聚合 -> {h: {year: {n, win%, avg%, avg_excess%}}}。

    卖出日缺失(数据不足)的笔不计入。用来看策略哪一年开始失效。
    """
    out = {}
    for h in horizons:
        by_year = {}
        for p in picks:
            sd = p.get("sell_date", {}).get(h)
            if sd is None or p["ret"].get(h) is None:
                continue
            y = str(sd)[:4]
            by_year.setdefault(y, []).append((p["ret"][h],
                                              p.get("excess", {}).get(h)))
        out[h] = {y: {"n": len(rows),
                      "win": sum(r > 0 for r, _ in rows) / len(rows) * 100,
                      "avg": statistics.fmean(r for r, _ in rows),
                      "avg_excess": (statistics.fmean(e for _, e in rows
                                                      if e is not None)
                                     if any(e is not None for _, e in rows)
                                     else None)}
                  for y, rows in sorted(by_year.items())}
    return out


def equity_curve(picks, horizons=HORIZONS) -> dict:
    """逐笔 -> {h: [(卖出日, 净值)]} 批次净值曲线。

    假设: 每个调仓批次内等权, 批次收益 = 批内各笔平均, 资金全额滚动再投
    (期内不换仓)。净值 = ∏(1 + 批次收益/100)。近似口径, 用来看策略资金
    曲线形态, 不替代逐日组合模拟。
    """
    out = {}
    for h in horizons:
        by_date = {}
        for p in picks:
            r = p["ret"].get(h)
            if r is None:
                continue
            sd = p.get("sell_date", {}).get(h)
            if sd is None:
                continue
            by_date.setdefault(sd, []).append(r)
        nav, curve = 1.0, []
        for sd in sorted(by_date):
            nav *= 1.0 + statistics.fmean(by_date[sd]) / 100.0
            curve.append((sd, nav))
        out[h] = curve
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


def report_yearly(result) -> str:
    """分年收益表 -> 中文文本(report(result) 的补充)。"""
    y = result.get("yearly") or {}
    lines = ["分年(按卖出日):"]
    for h, rows in y.items():
        if not rows:
            continue
        lines.append(f"  持有{h}日:")
        lines.append(f"    {'年份':>6}{'笔数':>6}{'胜率%':>8}{'平均%':>9}{'平均超额%':>11}")
        for year, m in rows.items():
            ae = (f"{m['avg_excess']:>+10.2f}" if m["avg_excess"] is not None
                  else "         --")
            lines.append(f"    {year:>6}{m['n']:>6}{m['win']:>8.1f}"
                         f"{m['avg']:>+9.2f}{ae}")
    return "\n".join(lines)
