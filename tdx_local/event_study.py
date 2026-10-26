# -*- coding: utf-8 -*-
"""事件研究 —— 事件日(除息/财报/自定义)前后 N 日的平均收益漂移。

回答"这类事件之后股票平均怎么走": 对每个事件取事件日收盘为锚, 逐日分红
送转再投算窗口累计收益曲线(car, cumulative abnormal return 的简化口径:
未减去系统性收益时是"累计收益", 传 benchmark 则输出超额), 再把所有事件的
曲线按偏移日平均 —— 即事件研究的"平均漂移"图。

防未来函数说明: 事件研究只看事件日之后的价格反应, 窗口含事件日及以后,
天然无前视; pre 窗口仅供画"事件前基准", 不用于决策。

用法::

    from tdx_local import event_study as es

    # 事件: 每只股票的除息日列表(可从 tq.divid_factors 取)
    events = {c: list(divs) for c, divs in ...}
    res = es.study(bars_by_code, events, pre=5, post=10,
                   dividends_by_code=tq.divid_factors, splits_by_code=tq.divid_splits)
    print(es.report(res))
"""
import statistics

from . import backtest

__all__ = ["window_curve", "study", "report"]


def window_curve(bars, i_event, pre=5, post=10, dividends=None, splits=None):
    """事件日=i_event 收盘为锚 -> {偏移: 累计收益%}(偏移 -pre..post, 数据不足截尾)。

    分红/送转再投与 backtest.forward_return 同口径(事件日之后发生的才计入,
    事件当日除息归前手 —— 与"买入在事件日收盘"一致)。
    """
    dates, closes = bars["Date"], bars["Close"]
    out = {}
    lo, hi = max(0, i_event - pre), min(len(closes) - 1, i_event + post)
    anchor = closes[i_event]
    if anchor <= 0:
        return out
    shares, cash = 1.0, 0.0
    for j in range(i_event + 1, hi + 1):
        split = splits.get(str(dates[j]), 0.0) if splits else 0.0
        div = dividends.get(str(dates[j]), 0.0) if dividends else 0.0
        if div:
            cash += shares * div
        if split:
            shares *= 1.0 + split
        if div and closes[j] > 0:
            shares += cash / closes[j]
            cash = 0.0
        out[j - i_event] = ((shares * closes[j] + cash) / anchor - 1) * 100
    out[0] = 0.0
    return out


def study(bars_by_code, events_by_code, pre=5, post=10,
          dividends_by_code=None, splits_by_code=None, benchmark=None) -> dict:
    """{code: [事件日]} -> 平均漂移汇总。

    事件日不在该股日历里的跳过; 每事件窗口数据不足按实际可得偏移平均。
    benchmark: 基准代码(须在 bars_by_code)—— 输出超额漂移(car 减基准同窗)。
    返回 {"n_events", "offsets": [-pre..post], "car_mean": {偏移: %},
          "car_med": {...}, "hit": {偏移: 正收益率%}}。
    """
    _pos_memo, div_memo, spl_memo = {}, {}, {}

    def _pos(code):
        if code not in _pos_memo:
            _pos_memo[code] = {int(str(d)): i for i, d in
                               enumerate(bars_by_code[code]["Date"])}
        return _pos_memo[code]

    def _memo(code, source, cache):
        if code not in cache:
            cache[code] = source(code) or {} if callable(source) \
                else (source or {}).get(code) or {}
        return cache[code]

    curves, n_events = [], 0
    bench = bars_by_code.get(benchmark) if benchmark else None
    for code, days in events_by_code.items():
        if code not in bars_by_code:
            continue
        bars = bars_by_code[code]
        pos_map = _pos(code)
        divs = _memo(code, dividends_by_code, div_memo)
        spls = _memo(code, splits_by_code, spl_memo)
        for day in days:
            i = pos_map.get(int(str(day)))
            if i is None or closes_bad(bars["Close"], i):
                continue
            cur = window_curve(bars, i, pre, post, divs, spls)
            if bench is not None and int(str(day)) in _pos(benchmark):
                jb = _pos(benchmark)[int(str(day))]
                bcur = window_curve(bench, jb, pre, post)
                cur = {o: v - bcur[o] for o, v in cur.items() if o in bcur}
            if cur:
                curves.append(cur)
                n_events += 1
    offsets = list(range(-pre, post + 1))
    car_mean, car_med, hit = {}, {}, {}
    for o in offsets:
        vals = [c[o] for c in curves if o in c]
        if vals:                                   # 样本少时仍是描述统计, 由 n_events 判断可信度
            car_mean[o] = statistics.fmean(vals)
            car_med[o] = statistics.median(vals)
            hit[o] = sum(v > 0 for v in vals) / len(vals) * 100
    return {"n_events": n_events, "offsets": offsets, "car_mean": car_mean,
            "car_med": car_med, "hit": hit}


def closes_bad(closes, i):
    return i < 0 or i >= len(closes) or closes[i] <= 0


def report(res) -> str:
    """事件研究 -> 中文文本报告。"""
    lines = [f"共 {res['n_events']} 个事件, 平均漂移(相对事件日收盘):"]
    lines.append(f"{'偏移日':>6}{'平均%':>9}{'中位%':>9}{'正收益率%':>10}")
    for o in res["offsets"]:
        if o not in res["car_mean"]:
            continue
        lines.append(f"{o:>+6}{res['car_mean'][o]:>+9.2f}{res['car_med'][o]:>+9.2f}"
                     f"{res['hit'][o]:>10.1f}")
    return "\n".join(lines)
