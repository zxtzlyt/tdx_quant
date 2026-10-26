# -*- coding: utf-8 -*-
"""涨停/跌停判定与连板复盘 —— 纯价量统计, 数据来自日线(不复权收盘)。

交易所涨跌停规则(2026-10-27 口径):
  - 主板(60x/00x): ±10%; ST 主板 ±5%
  - 创业板(30x)/科创板(68x): ±20%(ST 仍 20%)
  - 北交所(8x/4x/92x): ±30%
  涨停价 = 前收 × (1+比例) 四舍五入到分(交易所规则, 非 Python 银行家舍入)。
判定: 收盘 == 涨停价 -> 涨停(封板); 盘中触涨停价但收盘未封 -> 炸板;
跌停对称。上市首日无前收, 跳过(不计入统计, 避免误判)。

用法::

    from tdx_local import limits

    bars = kcache.read_many(kcache.default_dir(), codes)
    rep = limits.review(bars, 20261023)
    print(limits.report(rep))
"""
import math

__all__ = ["limit_ratio", "limit_up_price", "limit_down_price", "classify",
           "streaks", "review", "report"]

_EPS = 1e-6


def _round2(x):
    """交易所口径四舍五入到分(Python round 是银行家舍入, 不能用)。"""
    return math.floor(x * 100 + 0.5) / 100


def limit_ratio(code, st=False):
    """代码 -> 当日涨跌停比例(0.10/0.05/0.20/0.30)。"""
    num, mkt = code.split(".")
    if mkt == "BJ":
        return 0.30
    is_gem = num.startswith("30") or num.startswith("68")   # 创业板/科创板
    if st and not is_gem:
        return 0.05
    return 0.20 if is_gem else 0.10


def limit_up_price(prev_close, code, st=False):
    """前收 -> 当日涨停价(四舍五入到分)。"""
    return _round2(prev_close * (1 + limit_ratio(code, st)))


def limit_down_price(prev_close, code, st=False):
    """前收 -> 当日跌停价。"""
    return _round2(prev_close * (1 - limit_ratio(code, st)))


def classify(code, prev_close, high, low, close, st=False):
    """单日K线 -> "涨停"/"炸板"/"跌停"/"跌停炸板"/"普通"; 前收无效返回 None。"""
    if prev_close is None or prev_close <= 0:
        return None
    up, dn = limit_up_price(prev_close, code, st), limit_down_price(prev_close, code, st)
    touched_up = high >= up - _EPS
    touched_dn = low <= dn + _EPS
    sealed_up = close >= up - _EPS
    sealed_dn = close <= dn + _EPS
    if sealed_up:
        return "涨停"
    if sealed_dn:
        return "跌停"
    if touched_up:
        return "炸板"
    if touched_dn:
        return "跌停炸板"
    return "普通"


def _is_limit(bars, i, st, direction="up"):
    """第 i 根(以 i-1 为前收)是否封板; i==0 无前收 -> False。"""
    code = bars["Code"]
    cls = classify(code, bars["Close"][i - 1], bars["High"][i], bars["Low"][i],
                   bars["Close"][i], st)
    return cls == ("涨停" if direction == "up" else "跌停")


def streaks(bars_by_code, st_by_code=None) -> dict:
    """全池连板数 -> {code: 连续涨停天数}(从数据末端往前数; 末端非涨停=0)。"""
    out = {}
    for code, bars in bars_by_code.items():
        st = (st_by_code or {}).get(code, False)
        n, i = 0, len(bars["Close"]) - 1
        while i > 0 and _is_limit(bars, i, st, "up"):
            n += 1
            i -= 1
        if n:
            out[code] = n
    return out


def review(bars_by_code, date, st_by_code=None) -> dict:
    """某交易日全池复盘 -> 涨停/炸板/跌停名单与连板梯队。

    bars_by_code: {code: 列式bars}(含该日及其前一根); 当日不在数据里的代码
    跳过(停牌); 首日无前收跳过。连板梯队 {板数: [code]} 按"当日涨停"的
    连续天数(含当日)计。
    """
    up, up_open, dn, first_day = [], [], [], []
    ladder = {}
    for code, bars in bars_by_code.items():
        st = (st_by_code or {}).get(code, False)
        try:
            i = [int(str(d)) for d in bars["Date"]].index(int(date))
        except ValueError:
            continue
        if i == 0:
            first_day.append(code)                     # 无前收, 无法判定
            continue
        cls = classify(code, bars["Close"][i - 1], bars["High"][i],
                       bars["Low"][i], bars["Close"][i], st)
        if cls == "涨停":
            up.append(code)
            n, j = 1, i
            while j > 0 and _is_limit(bars, j, st, "up"):
                if j < i:
                    n += 1
                j -= 1
            ladder.setdefault(n, []).append(code)
        elif cls == "炸板":
            up_open.append(code)
        elif cls == "跌停":
            dn.append(code)
        elif cls == "跌停炸板":
            dn.append(code)                            # 跌停口径合并(复盘常用封板/触板)
    return {"date": int(date), "limit_up": sorted(up), "limit_up_open": sorted(up_open),
            "limit_down": sorted(dn), "first_day": sorted(first_day),
            "ladder": {n: sorted(cs) for n, cs in sorted(ladder.items(), reverse=True)},
            "n_scanned": len(bars_by_code)}


def report(rep) -> str:
    """复盘 dict -> 中文文本报告。"""
    lines = [f"{rep['date']} 复盘(扫描 {rep['n_scanned']} 只):"
             f" 涨停 {len(rep['limit_up'])}, 炸板 {len(rep['limit_up_open'])},"
             f" 跌停 {len(rep['limit_down'])}"
             + (f", 无前收 {len(rep['first_day'])}" if rep["first_day"] else "")]
    if rep["ladder"]:
        lines.append("连板梯队: " + " | ".join(
            f"{n}板x{len(cs)}({','.join(cs[:6])}{'…' if len(cs) > 6 else ''})"
            for n, cs in rep["ladder"].items()))
    if rep["limit_up_open"]:
        lines.append("炸板: " + ",".join(rep["limit_up_open"][:20])
                     + ("…" if len(rep["limit_up_open"]) > 20 else ""))
    return "\n".join(lines)
