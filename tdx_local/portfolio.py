# -*- coding: utf-8 -*-
"""组合层工具 —— 权重方案、相关性与等权组合净值, 纯标准库。

输入约定: returns_by_code = {code: [日收益%, 按交易日对齐]}(不等长时按最短
对齐; 全对齐由调用方保证更稳)。所有权重归一化和为 1。

用法::

    from tdx_local import portfolio

    w = portfolio.weights_by_inverse_vol(returns)   # 波动率倒数加权
    m = portfolio.corr_matrix(returns)              # 相关性矩阵
    curve = portfolio.equity_curve(weights, returns)  # [(日, 净值)] 每日再平衡
"""
import math
import statistics

from . import factor

__all__ = ["weights_equal", "weights_by_inverse_vol", "corr_matrix",
           "equity_curve"]


def _align(returns_by_code):
    """截到最短长度(少于 2 个交易日收益或股票数 <1 返回空)。"""
    codes = [c for c, rs in returns_by_code.items() if len(rs) >= 2]
    if not codes:
        return codes, 0
    n = min(len(returns_by_code[c]) for c in codes)
    return codes, n


def weights_equal(returns_by_code) -> dict:
    """等权: {code: 1/N}(以 returns 里有效代码为准)。"""
    codes, _ = _align(returns_by_code)
    return {c: 1.0 / len(codes) for c in codes} if codes else {}


def weights_by_inverse_vol(returns_by_code) -> dict:
    """波动率倒数加权: 波动小的配得多(日收益样本标准差的倒数, 归一化)。"""
    codes, n = _align(returns_by_code)
    if not codes:
        return {}
    inv = {}
    for c in codes:
        sd = statistics.stdev(returns_by_code[c][-n:])
        inv[c] = 1.0 / sd if sd > 1e-12 else 1e12    # 近似零波动给大权重并钳顶
    total = sum(inv.values())
    return {c: v / total for c, v in inv.items()}


def corr_matrix(returns_by_code) -> dict:
    """日收益相关性矩阵 -> {code: {code: corr}}(对角恒 1; 样本不足对为 None)。"""
    codes, n = _align(returns_by_code)
    out = {c: {} for c in codes}
    for i, a in enumerate(codes):
        out[a][a] = 1.0
        for b in codes[i + 1:]:
            ra = returns_by_code[a][-n:]
            rb = returns_by_code[b][-n:]
            r = factor.pearson(ra, rb)
            out[a][b] = out[b][a] = r
    return out


def equity_curve(weights, returns_by_code) -> list:
    """每日再平衡的组合净值曲线 -> [(日序号, 净值)]。

    假设每个交易日收盘按 weights 再平衡(日频调仓近似); 收益序列按最短对齐。
    """
    codes = [c for c in weights if c in returns_by_code and returns_by_code[c]]
    if not codes:
        return []
    total_w = sum(weights[c] for c in codes) or 1.0
    n = min(len(returns_by_code[c]) for c in codes)
    nav, out = 1.0, []
    for i in range(n):
        r = sum(weights[c] / total_w * returns_by_code[c][i] for c in codes) / 100.0
        nav *= 1.0 + r
        out.append((i, nav))
    return out
