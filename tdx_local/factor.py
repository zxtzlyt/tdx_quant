# -*- coding: utf-8 -*-
"""因子评测框架 —— 判断一个想法值不值得写成策略: 先跑 IC/分层, 再进 backtest。

与 backtest.run 的分工: backtest 回答"这个选股规则历史赚不赚", factor 回答
"这个打分序列有没有截面预测力" —— 每个调仓日对所有股票打分, 算因子值与
未来持有期收益的 RankIC(斯皮尔曼秩相关), 并按因子值分 n_groups 层看各层
平均前向收益与多空价差(spread = 最高层 - 最低层)。ICIR = IC均值/IC标准差,
t 近似 = ICIR × sqrt(期数)。

防未来函数与收益口径完全复用 backtest: 每个调仓日 T 的因子只看 slice_asof
截至 T 的窗口; 前向收益 = 不复权价 + 分红/送转再投(forward_return 同款)。

用法::

    from tdx_local import factor

    def momentum(asof, code):
        cl = asof["Close"]
        return cl[-1] / cl[-21] - 1 if len(cl) >= 21 else None   # 20日动量

    result = factor.run(bars_by_code, rebalance_dates, momentum,
                        dividends_by_code=tq.divid_factors,
                        splits_by_code=tq.divid_splits)
    print(factor.report(result))
"""
import statistics

from . import backtest

__all__ = ["run", "summarize", "report", "spearman", "pearson"]


def pearson(xs, ys):
    """皮尔逊相关系数; 方差为 0 或长度<2 返回 None。"""
    n = len(xs)
    if n < 2:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    vx = sum((a - mx) ** 2 for a in xs)
    vy = sum((b - my) ** 2 for b in ys)
    if vx <= 0 or vy <= 0:
        return None
    return cov / (vx * vy) ** 0.5


def _ranks(vals):
    """并列值取平均秩(斯皮尔曼标准处理)。"""
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    ranks = [0.0] * len(vals)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def spearman(xs, ys):
    """斯皮尔曼 RankIC(秩相关); 长度<3 或零方差返回 None。"""
    if len(xs) != len(ys) or len(xs) < 3:
        return None
    return pearson(_ranks(list(xs)), _ranks(list(ys)))


def _group_avg(pts, n_groups):
    """[(因子值, 收益)] 按因子值升序等量分 n_groups 组 -> {组号: 平均收益%}。

    组 1 = 因子值最低, 组 n_groups = 最高。因子值并列按排序稳定切分;
    某组为空(截面太小)不出现在结果里。
    """
    if not pts:
        return {}
    pts = sorted(pts, key=lambda p: p[0])
    size = max(1, len(pts) // n_groups)
    out = {}
    for g in range(n_groups):
        seg = pts[g * size:(g + 1) * size] if g < n_groups - 1 else pts[g * size:]
        if seg:
            out[g + 1] = statistics.fmean(r for _, r in seg)
    return out


def _evaluate(T, rows, horizons, n_groups):
    """单期截面 -> {"date", "n", h: {"n", "ic", "groups", "spread"}}。"""
    out = {"date": T, "n": len(rows)}
    for h in horizons:
        pts = [(f, fwd[h]) for f, fwd in rows.values() if fwd.get(h) is not None]
        if len(pts) < 5:
            out[h] = {"n": len(pts), "ic": None, "groups": {}, "spread": None}
            continue
        groups = _group_avg(pts, n_groups)
        spread = (groups[n_groups] - groups[1]
                  if n_groups in groups and 1 in groups else None)
        out[h] = {"n": len(pts), "ic": spearman([p[0] for p in pts],
                                                [p[1] for p in pts]),
                  "groups": groups, "spread": spread}
    return out


def run(bars_by_code, rebalance_dates, factor_fn, horizons=backtest.HORIZONS,
        dividends_by_code=None, splits_by_code=None, window=backtest.WINDOW,
        n_groups=5) -> dict:
    """因子重放主入口。

    bars_by_code: {code: 列式全历史bars}(不复权, kcache.read_many 同款)。
    rebalance_dates: 调仓日(YYYYMMDD int 升序)。
    factor_fn(asof, code) -> 因子值(float; None=当日无效, 不入截面)。
              asof 是该 code 截至 T 的 slice_asof 切片 —— 只能用它, 不要闭包
              引用外部实时数据。因子方向: 值越大层号越大, spread = 高层-低层。
    dividends_by_code / splits_by_code: 同 backtest.run(可传 TqClient 方法)。
    返回 {"periods": [...], "summary": {h: {...}}}。

    规模预期: 全市场(约5000只)×200期×3个持有期约 20s~1min 量级(与
    backtest.run 全市场同型); 小池子秒级。
    """
    _pos_memo, div_memo, spl_memo = {}, {}, {}

    def _pos(code):
        if code not in _pos_memo:
            _pos_memo[code] = {d: i for i, d in enumerate(bars_by_code[code]["Date"])}
        return _pos_memo[code]

    def _memo(code, source, cache):
        if code not in cache:
            cache[code] = source(code) or {} if callable(source) \
                else (source or {}).get(code) or {}
        return cache[code]

    periods = []
    for T in rebalance_dates:
        rows = {}
        for code, bars in bars_by_code.items():
            dates = bars["Date"]
            pos = _pos(code).get(T)
            if pos is None or pos < 1:
                continue
            lo = max(0, pos + 1 - window)
            asof = {k: v[lo:pos + 1] for k, v in bars.items()}
            f = factor_fn(asof, code)
            if f is None:
                continue
            divs = _memo(code, dividends_by_code, div_memo)
            spls = _memo(code, splits_by_code, spl_memo)
            fwd = {h: backtest.forward_return(dates, bars["Close"], pos, h,
                                              divs, spls) for h in horizons}
            rows[code] = (f, fwd)
        periods.append(_evaluate(T, rows, horizons, n_groups))
    return {"periods": periods, "summary": summarize(periods, horizons, n_groups)}


def summarize(periods, horizons=backtest.HORIZONS, n_groups=5) -> dict:
    """逐期 -> {h: {n_periods, ic_mean, ic_std, icir, t_stat, ic_pos%,
                    spread_mean, groups_mean}}。"""
    out = {}
    for h in horizons:
        ics = [p[h]["ic"] for p in periods if p.get(h, {}).get("ic") is not None]
        spreads = [p[h]["spread"] for p in periods
                   if p.get(h, {}).get("spread") is not None]
        if not ics:
            out[h] = {"n_periods": 0}
            continue
        ic_mean, ic_std = statistics.fmean(ics), statistics.pstdev(ics)
        gmeans = {}
        for p in periods:
            for g, v in p[h].get("groups", {}).items():
                gmeans.setdefault(g, []).append(v)
        out[h] = {"n_periods": len(ics),
                  "ic_mean": ic_mean,
                  "ic_std": ic_std if len(ics) > 1 else None,
                  "icir": (ic_mean / ic_std) if ic_std else None,
                  "t_stat": (ic_mean / ic_std * len(ics) ** 0.5) if ic_std else None,
                  "ic_pos": sum(v > 0 for v in ics) / len(ics) * 100,
                  "spread_mean": statistics.fmean(spreads) if spreads else None,
                  "groups_mean": {g: statistics.fmean(vs) for g, vs in
                                  sorted(gmeans.items())}}
    return out


def report(result) -> str:
    """因子评测 -> 中文文本报告。"""
    s = result["summary"]
    lines = [f"共 {len(result['periods'])} 个调仓期"]
    lines.append(f"{'持有期':>6}{'期数':>6}{'IC均值':>9}{'ICIR':>8}{'t值':>7}"
                 f"{'IC>0占比%':>10}{'多空价差%':>10}")
    for h, m in s.items():
        if m.get("n_periods", 0) == 0:
            lines.append(f"{h:>4}日       0       --      --     --         --         --")
            continue
        icir = f"{m['icir']:>8.2f}" if m["icir"] is not None else "      --"
        t = f"{m['t_stat']:>7.2f}" if m["t_stat"] is not None else "     --"
        sp = (f"{m['spread_mean']:>+10.3f}" if m["spread_mean"] is not None
              else "        --")
        lines.append(f"{h:>4}日{m['n_periods']:>6}{m['ic_mean']:>+9.4f}{icir}{t}"
                     f"{m['ic_pos']:>10.1f}{sp}")
        gm = m.get("groups_mean") or {}
        if gm:
            cells = " ".join(f"G{g}:{v:+.2f}" for g, v in gm.items())
            lines.append(f"      分层均值(G1=因子最低 -> G{len(gm)}=最高): {cells}")
    return "\n".join(lines)
