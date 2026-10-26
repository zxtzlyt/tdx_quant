# -*- coding: utf-8 -*-
"""财务衍生比率层 —— 在已锚定的 FN 槽位之上做组合计算, 选股/体检直接用名取值。

定位: cw_fields.FIELDS 是"官方槽位=什么"的注册表(真值锚定), gpcw 负责
把文件解析成 {报告期: [槽位值]}; 本模块负责"比率怎么算" —— 现成比率
(FN199/FN202/FN210/FN183/FN184/FN281 官方已算)直接取槽位, 缺现成槽位的
组合比率(归母净利率/净现比等)按注册表公式自算, 单位/口径随表说明。

用法::

    from tdx_local import gpcw, ratios

    dates, records = gpcw.read_gpcw(cw_dir, "600519")   # records: {报告期: [槽位...]}
    table = ratios.compute(records, ["毛利率", "ROE加权", "归母净利率", "净现比"])
    # -> {20241231: {"毛利率": 91.9, "ROE加权": 34.2, ...}, ...}
"""
from . import cw_fields

__all__ = ["READY_MADE", "DERIVED", "compute", "latest"]

# 官方已算好的比率槽位: 名字 -> (FN槽位, 单位, 口径说明)
READY_MADE = {
    "毛利率": (202, "%", "累计; 官方口径"),
    "净利率": (199, "%", "累计; 含少数股东损益口径(净利润/营收)"),
    "ROE加权": (281, "%", "累计; 加权平均"),
    "ROE摊薄": (6, "%", "累计; 仅文档名义未实证, 谨慎用"),
    "资产负债率": (210, "%", "时点"),
    "营收增长率": (183, "%", "同比"),
    "净利增长率": (184, "%", "同比"),
}

# 组合比率注册表: 名字 -> (分子槽位, 分母槽位, 变换, 单位, 口径说明)
# 变换(a, b) -> 值; 分母为 0/缺失返回 None。
DERIVED = {
    "归母净利率": (96, 74, lambda a, b: a / b * 100, "%",
                   "累计; 归母净利润/营业收入 —— 与净利率(199)差异即少数股东损益"),
    "净现比": (107, 96, lambda a, b: a / b, "倍",
               "累计; 经营现金流净额/归母净利润, >1 视为利润有现金支撑"),
    "归母权益占比": (271, 72, lambda a, b: a / b * 100, "%",
                     "时点; 归母权益/股东权益合计, 越低说明少数股东权益占比越高"),
    "存货占比": (17, 40, lambda a, b: a / b * 100, "%", "时点; 存货/总资产"),
    "货币资金占比": (8, 40, lambda a, b: a / b * 100, "%", "时点; 货币资金/总资产"),
    "每股归母权益": (271, 238, lambda a, b: a / b, "元/股",
                     "时点; 归母权益/总股本(=每股净资产的自算互证, 对照 FN4)"),
}

_EPS = 1e-12


def _slot_value(rec, slot):
    v = rec[slot - 1] if rec and len(rec) >= slot else None
    return float(v) if v is not None else None


def compute(records, names) -> dict:
    """{报告期: [槽位...]} -> {报告期: {比率名: 值}}。

    names 可含 READY_MADE 现成比率与 DERIVED 组合比率; 未注册名抛 LookupError
    (带可用名提示)。槽位缺失/分母为 0 的格子为 None, 不造假数。
    """
    for n in names:
        if n not in READY_MADE and n not in DERIVED:
            raise LookupError(
                f"未注册比率 '{n}'; 现成: {sorted(READY_MADE)}; 组合: {sorted(DERIVED)}")
    out = {}
    for d, rec in records.items():
        row = {}
        for n in names:
            if n in READY_MADE:
                slot, _, _ = READY_MADE[n]
                v = _slot_value(rec, slot)
            else:
                num, den, fn, _, _ = DERIVED[n]
                a, b = _slot_value(rec, num), _slot_value(rec, den)
                v = fn(a, b) if (a is not None and b is not None
                                 and abs(b) > _EPS) else None
            row[n] = v
        out[d] = row
    return out


def latest(table, name):
    """compute 结果里取最新报告期的单个比率值; 无有效值返回 None。"""
    for d in sorted(table, key=str, reverse=True):
        v = table[d].get(name)
        if v is not None:
            return v
    return None
