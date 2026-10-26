# -*- coding: utf-8 -*-
"""技术指标库(纯标准库) —— 选股配方与回测共用的指标口径, 指标一律 Python 自算。

背景: 公式计算通路(formula_*)在 HTTP 模式下实测不生效(docs/LOCAL_NOTES.md),
所以 MACD/均线等指标全部在本模块用 Python 算。此前的实现散落在
examples/{macd_demo, stock_checkup, pick_technical}.py 三处且口径不一,
本模块是唯一的权威版本。

口径约定::

    from tdx_local import indicators as ind

    mas = ind.sma(closes, 20)          # 序列: 前 n-1 个位置为 None
    dif, dea, hist = ind.macd(closes)  # hist=(dif-dea)*2, A股看盘软件口径
    ind.macd_state(closes)             # -> "金叉/死叉/多头/空头"
    p, t, n = ind.total_return_with_dividends(closes, dates, dividends)

收益计算红线(LOCAL_NOTES 2026-09-29 实测): 前复权价在高分红股上会算出
负价(茅台 2011 年 -176 元), 不可用于收益率; 正确口径是"不复权价格链 +
带日期分红事件再投", 即 total_return_with_dividends 的实现。
"""

__all__ = ["sma", "ma", "ema", "macd", "macd_state", "is_golden_cross",
           "is_bull_align", "is_volume_surge", "is_volume_shrink", "amplitude",
           "rsi", "kdj", "boll", "atr",
           "total_return_with_dividends", "max_drawdown"]


def sma(values, n):
    """简单均线序列: 滚动和实现, 前 n-1 个位置为 None。"""
    out, s = [], 0.0
    for i, v in enumerate(values):
        s += v
        if i >= n:
            s -= values[i - n]
        out.append(s / n if i >= n - 1 else None)
    return out


def ma(values, n):
    """末端均线值: 数据不足 n 根时返回 None。"""
    if len(values) < n:
        return None
    return sum(values[-n:]) / n


def ema(values, n):
    """指数均线序列: 种子值为首元素, 空列表返回 []。"""
    if not values:
        return []
    k = 2 / (n + 1)
    out = [values[0]]
    for v in values[1:]:
        out.append(v * k + out[-1] * (1 - k))
    return out


def macd(closes, fast=12, slow=26, signal=9):
    """MACD(fast,slow,signal) -> (dif, dea, hist) 三条等长序列。

    dif=EMA(fast)-EMA(slow); dea=EMA(dif,signal); hist=(dif-dea)*2
    (乘 2 是 A股看盘软件的 MACD 柱口径)。
    """
    dif = [a - b for a, b in zip(ema(closes, fast), ema(closes, slow))]
    dea = ema(dif, signal)
    hist = [(d - f) * 2 for d, f in zip(dif, dea)]
    return dif, dea, hist


def macd_state(closes):
    """最后一根K线的 MACD 状态 -> "金叉/死叉/多头/空头"。

    交叉判定: 今天 dif 在 dea 上方且昨天 dif<=dea(昨天相等也算触发)。
    数据不足 2 根返回 "数据不足"。
    """
    if len(closes) < 2:
        return "数据不足"
    dif, dea, _ = macd(closes)
    if dif[-1] > dea[-1] and dif[-2] <= dea[-2]:
        return "金叉"
    if dif[-1] < dea[-1] and dif[-2] >= dea[-2]:
        return "死叉"
    return "多头" if dif[-1] > dea[-1] else "空头"


def is_golden_cross(closes, fast=5, slow=10):
    """最后一根K线上, fast 均线上穿 slow 均线(今天>昨, 且昨天<=前)。"""
    ma_f, ma_s = sma(closes, fast), sma(closes, slow)
    a, b = len(closes) - 1, len(closes) - 2
    if b < 0 or min(ma_f[a], ma_s[a], ma_f[b], ma_s[b]) is None:
        return False
    return ma_f[a] > ma_s[a] and ma_f[b] <= ma_s[b]


def is_bull_align(closes, n1=5, n2=10, n3=20):
    """均线多头排列: MA(n1) > MA(n2) > MA(n3)(末端值)。"""
    if len(closes) < n3:
        return False
    m1, m2, m3 = sma(closes, n1)[-1], sma(closes, n2)[-1], sma(closes, n3)[-1]
    return None not in (m1, m2, m3) and m1 > m2 > m3


def is_volume_surge(volumes, ratio=1.5, base=5):
    """今日成交量 > 前 base 日均量的 ratio 倍。"""
    if len(volumes) < base + 1:
        return False
    avg = sum(float(v) for v in volumes[-base - 1:-1]) / base
    return avg > 0 and float(volumes[-1]) > avg * ratio


def total_return_with_dividends(closes, dates, dividends, splits=None, years=5):
    """近 years 年: (纯价格回报%, 分红再投总回报%, 分红次数)。

    dividends: {除息日YYYYMMDD(int或str): 每股税前派息元} —— 即
    TqClient.divid_factors 的返回形态。splits: {除息日: 每股送转股数} ——
    即 TqClient.divid_splits 的返回形态(送转必须进模型, 否则"10送10"标的
    除权日价格腰斩而股本没补, 总回报严重低估)。除权除息日处理顺序按真实
    业务: 现金按送转前股本计 -> 股本×(1+送转) -> 现金按当日收盘(除权价)再投。
    买入日起每个除息日把现金分红按当日收盘价再投入(LOCAL_NOTES 茅台口径:
    12.49 倍 vs hexin 12.41 互证)。
    窗口锚定在数据末端(末端年份-years), 本地数据起点不足 years 年也能对齐。
    不修改传入的 dividends(2026-10-05 抽取时修正了原实现原地 pop 的副作用)。
    """
    if not closes:
        return None, None, 0
    divs = {str(k): v for k, v in dividends.items()}   # int/str 日期键统一
    spl = {str(k): v for k, v in (splits or {}).items()}
    cut = int(str(dates[-1])[:4]) - years
    idx0 = next((i for i, d in enumerate(dates) if int(str(d)[:4]) >= cut), 0)
    seg_d, seg_c = dates[idx0:], closes[idx0:]
    if len(seg_c) < 2:
        return None, None, 0
    price_ret = (seg_c[-1] / seg_c[0] - 1) * 100

    shares, cash, n_div = 1.0, 0.0, 0
    for d, c in zip(seg_d, seg_c):
        split = spl.get(str(d), 0.0)
        div = divs.get(str(d), 0.0)
        if div:
            n_div += 1
            cash += shares * div       # 派息基数是登记日(送转前)股本
        if split:
            shares *= 1.0 + split      # 送转后股本
        if div and c > 0:
            shares += cash / c         # 现金按除权日收盘再投
            cash = 0.0
    total_ret = (shares * seg_c[-1] + cash) / seg_c[0] - 1
    return price_ret, total_ret * 100, n_div


def max_drawdown(closes):
    """区间最大回撤(%, <=0): 峰值到其后谷底的最大跌幅; 数据<2根返回 0.0。"""
    if len(closes) < 2:
        return 0.0
    peak, worst = closes[0], 0.0
    for c in closes:
        peak = max(peak, c)
        if peak > 0:
            worst = min(worst, c / peak - 1)
    return worst * 100


# ---------------------------------------------------------------- 2026-10-27 扩展
def _wilder_smooth(values, n, init=50.0):
    """A股 SMA(X,N,1) 平滑(Wilder): y = y' + (x-y')/n; 初值 init。

    None 位置原样输出且不更新状态(等长对齐); EMA 类指标依赖历史长度,
    窗口起点不同末端值会略有差异 —— 与通达信全历史递推相比, 短窗口末端
    差异通常在第 2 位小数之后。
    """
    out, y, started = [], init, False
    for v in values:
        if v is None:
            out.append(None)
            continue
        y = y + (v - y) / n if started else init + (v - init) / n
        started = True
        out.append(y)
    return out


def rsi(closes, n=14):
    """RSI(n) 序列(Wilder 平滑, A股软件口径): 前 n 个位置为 None。

    分母为 0(单边)时返回 100/0 极值。>70 超买 / <30 超卖是常见用法。
    """
    m = len(closes)
    if m < n + 1:
        return [None] * m
    gains = losses = 0.0
    for i in range(1, n + 1):
        ch = closes[i] - closes[i - 1]
        gains += max(ch, 0.0)
        losses += max(-ch, 0.0)
    ag, al = gains / n, losses / n

    def _val(ag, al):
        if al == 0:
            return 100.0 if ag > 0 else 50.0      # 平盘 0/0 取中性 50
        return 0.0 if ag == 0 else 100.0 - 100.0 / (1.0 + ag / al)

    out = [None] * n
    out.append(_val(ag, al))
    for i in range(n + 1, m):
        ch = closes[i] - closes[i - 1]
        ag = (ag * (n - 1) + max(ch, 0.0)) / n
        al = (al * (n - 1) + max(-ch, 0.0)) / n
        out.append(_val(ag, al))
    return out


def kdj(highs, lows, closes, n=9, smooth=3):
    """KDJ(n, smooth) -> (k, d, j) 三条等长序列(前 n-1 个位置为 None)。

    RSV = (C-Ln)/(Hn-Ln)*100; K=SMA(RSV,smooth,1), D=SMA(K,smooth,1),
    J=3K-2D。一字板(Hn=Ln)当日 RSV 取 50(中性); 递推初值 50。
    """
    m = len(closes)
    rsv = []
    for i in range(m):
        if i < n - 1:
            rsv.append(None)
            continue
        hn, ln = max(highs[i - n + 1:i + 1]), min(lows[i - n + 1:i + 1])
        rsv.append(50.0 if hn == ln else (closes[i] - ln) / (hn - ln) * 100.0)
    k = _wilder_smooth(rsv, smooth, 50.0)
    d = _wilder_smooth(k, smooth, 50.0)
    j = [None if (a is None or b is None) else 3.0 * a - 2.0 * b for a, b in zip(k, d)]
    return k, d, j


def boll(closes, n=20, k=2):
    """BOLL(n,k) -> (mid, upper, lower) 三条等长序列(前 n-1 个位置为 None)。

    mid=MA(n), upper/lower = mid ± k×总体标准差(STDP, A股软件口径);
    滚动平方和实现 O(n)。方差负浮点误差钳为 0(常数序列 up=mid=lo)。
    """
    m = len(closes)
    mid = sma(closes, n)
    upper, lower = [None] * m, [None] * m
    s = ss = 0.0
    for i, v in enumerate(closes):
        s += v
        ss += v * v
        if i >= n:
            s -= closes[i - n]
            ss -= closes[i - n] * closes[i - n]
        if i >= n - 1:
            mean = s / n
            sd = max(ss / n - mean * mean, 0.0) ** 0.5
            upper[i] = mean + k * sd
            lower[i] = mean - k * sd
    return mid, upper, lower


def atr(highs, lows, closes, n=14):
    """ATR(n) 序列(Wilder 平滑): 前 n 个位置为 None。

    TR = max(H-L, |H-昨收|, |L-昨收|); 首日 TR=H-L。波动过滤/止损常用
    (如收盘跌破 ATR×k 通道)。
    """
    m = len(closes)
    tr = [highs[0] - lows[0]] if m else []
    for i in range(1, m):
        pc = closes[i - 1]
        tr.append(max(highs[i] - lows[i], abs(highs[i] - pc), abs(lows[i] - pc)))
    out = [None] * (n - 1)
    if m < n:
        return [None] * m
    y = sum(tr[:n]) / n
    out.append(y)
    for v in tr[n:]:
        y = y + (v - y) / n
        out.append(y)
    return out


def is_volume_shrink(volumes, ratio=0.7, base=5):
    """今日成交量 < 前 base 日均量的 ratio 倍(缩量, 配合回调企稳类策略)。"""
    if len(volumes) < base + 1:
        return False
    avg = sum(float(v) for v in volumes[-base - 1:-1]) / base
    return avg > 0 and float(volumes[-1]) < avg * ratio


def amplitude(high, low, prev_close):
    """单日振幅%: (high-low)/prev_close*100; prev_close<=0 返回 None。"""
    if not prev_close or prev_close <= 0:
        return None
    return (high - low) / prev_close * 100.0
