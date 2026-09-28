# -*- coding: utf-8 -*-
"""通达信专业财务字段注册表(真值锚定校准版)。

官方 FN 编号与 gpcw 文件实测存在三类偏差(2026-09-28 以贵州茅台 2012/2018/2024
年报公开数据锚定、并用报表内部勾稽复核; 证据与过程见 docs/LOCAL_NOTES.md):

  1. 缺失区: FN74-FN97 利润表主段官方文档缺失
     -> 锚定 FN74=营业收入(不含利息/手续费收入), FN95=净利润(含少数),
        FN96=归母净利润, FN97=少数股东损益(=FN95-FN96, 实测吻合);
  2. 单季陷阱: 衍生区 FN230/FN232/FN234 官方名义为"营业收入/归母净利/经营净额",
     实测为*单季*值(2024 年四个季度差分逐一吻合) -> 年度口径勿用这三个槽位;
  3. 新准则缺失: 合同负债/使用权资产/租赁负债在 584 个槽位中无对应
     (锚点扫描跨年无交集) -> 登记在 KNOWN_MISSING, 按名请求会抛错提示。

单位不统一: 主表科目=元, FN238=股, 比率=%, 每股=元/股 —— 以 unit 为准。
存储精度: 槽位值为 float32, 相对分辨率约 1e-7; 勾稽校验请用 gpcw.close_enough。
"""
# 每个槽位: name=注册名 / unit / period(时点|累计|单季|同比) / verified(实证标记)
# verified=True: 公开年报真值锚定或报表内部勾稽实证; False: 仅文档名义, 用前先自校。
FIELDS = {
    # —— 每股指标 ——
    1:   dict(name="基本每股收益", unit="元/股", period="累计", verified=True),
    4:   dict(name="每股净资产", unit="元/股", period="时点", verified=True),
    6:   dict(name="ROE摊薄", unit="%", period="累计", verified=False,
              note="仅文档名义, 未实证; 分析请用 281 加权ROE"),
    281: dict(name="ROE加权", unit="%", period="累计", verified=True),
    # —— 资产负债表(时点, 元) ——
    8:   dict(name="货币资金", unit="元", period="时点", verified=True),
    17:  dict(name="存货", unit="元", period="时点", verified=True),
    40:  dict(name="资产总计", unit="元", period="时点", verified=True,
              note="勾稽: FN63/FN40 与 FN210 在 2012/2024 两个报告期精确相等"),
    45:  dict(name="预收款项", unit="元", period="时点", verified=True,
              note="2020 起重分类为合同负债后恒为 0; 合同负债无槽位, 见 KNOWN_MISSING"),
    63:  dict(name="负债合计", unit="元", period="时点", verified=True),
    72:  dict(name="股东权益合计", unit="元", period="时点", verified=True,
              note="勾稽: FN271+FN69=FN72 精确相等"),
    238: dict(name="总股本", unit="股", period="时点", verified=True),
    271: dict(name="归母股东权益", unit="元", period="时点", verified=True),
    # —— 利润表(累计, 元; 74-97 为文档缺失区, 真值锚定) ——
    74:  dict(name="营业收入", unit="元", period="累计", verified=True,
              note="不含利息/手续费收入; 与'营业总收入'差财务公司利息收入(茅台约2%)"),
    95:  dict(name="净利润", unit="元", period="累计", verified=True,
              note="含少数股东损益"),
    96:  dict(name="归母净利润", unit="元", period="累计", verified=True),
    97:  dict(name="少数股东损益", unit="元", period="累计", verified=True,
              note="=FN95-FN96, 2024 实测 31.07 亿吻合"),
    # —— 现金流量表(累计, 元) ——
    107: dict(name="经营现金流净额", unit="元", period="累计", verified=True),
    # —— 比率(%) ——
    183: dict(name="营收增长率", unit="%", period="同比", verified=True),
    184: dict(name="净利增长率", unit="%", period="同比", verified=True),
    199: dict(name="销售净利率", unit="%", period="累计", verified=True,
              note="口径=净利润(含少数)/营业收入(FN74), 非归母口径"),
    202: dict(name="销售毛利率", unit="%", period="累计", verified=True),
    210: dict(name="资产负债率", unit="%", period="时点", verified=True),
    # —— 单季陷阱区: 官方文档名义为累计, 实测为单季 ——
    230: dict(name="营业收入单季", unit="元", period="单季", verified=True,
              note="文档名义'营业收入'; 2024 四季差分吻合; 年度值用 FN74"),
    232: dict(name="归母净利润单季", unit="元", period="单季", verified=True,
              note="文档名义'归属于母公司所有者的净利润'; 实测单季; 年度值用 FN96"),
    234: dict(name="经营现金流净额单季", unit="元", period="单季", verified=True,
              note="文档名义'经营活动产生的现金流量净额'; 2024 单季差分吻合; 年度值用 FN107"),
}

# 常用别名 -> 槽位(与 FIELDS 的注册名互补; 解析优先级: 注册名 > 别名)
ALIASES = {
    "EPS": 1, "每股收益": 1, "每股净资产": 4, "ROE": 281, "ROE加权": 281, "ROE摊薄": 6,
    "货币资金": 8, "存货": 17, "总资产": 40, "资产总计": 40, "预收款项": 45,
    "负债合计": 63, "股东权益合计": 72, "总股本": 238, "归母权益": 271, "归母股东权益": 271,
    "营业收入": 74, "营收": 74, "净利润": 95, "归母净利润": 96, "少数股东损益": 97,
    "经营现金流净额": 107, "营收增长率": 183, "净利增长率": 184, "净利率": 199,
    "毛利率": 202, "资产负债率": 210,
    "营业收入单季": 230, "归母净利润单季": 232, "经营现金流净额单季": 234,
}

# 文件中确认缺失的科目(锚点扫描跨年无交集): 按名请求抛 LookupError 并给出原因。
KNOWN_MISSING = {
    "合同负债": "2020 收入准则重分类后新增, 584 槽位锚点扫描无匹配; FN45 预收款项随之恒为 0",
    "使用权资产": "新租赁准则科目, 锚点扫描无匹配",
    "租赁负债": "新租赁准则科目, 锚点扫描无匹配",
}


def resolve(field) -> int:
    """字段注册名/别名 -> 槽位号; int 原样返回。

    KNOWN_MISSING 中的科目与未注册名字抛 LookupError(附原因/可用名提示)。
    """
    if isinstance(field, int):
        return field
    for table in (FIELDS, ALIASES):
        if field in table:
            return field if isinstance(field, int) else table[field]
    if field in KNOWN_MISSING:
        raise LookupError(f"'{field}': {KNOWN_MISSING[field]}; "
                          f"如有新证据可用 cw_fields.find_slot 重新锚定")
    raise LookupError(f"未注册字段 '{field}'; 可用名: FIELDS 注册名、ALIASES 别名, "
                      f"或直接给 FN 槽位号(int)")


def meta(field) -> dict:
    """槽位号/注册名 -> 字段元数据(FIELDS 表项)。未登记的槽位返回占位元数据。"""
    slot = resolve(field)
    return FIELDS.get(
        slot, dict(name=f"FN{slot}", unit="未知", period="未知", verified=False))


def unit(field) -> str:
    """槽位号/注册名 -> 单位(元/股/%/元每股...)。"""
    return meta(field)["unit"]


def find_slot(records, targets, rel_tol=0.003) -> list:
    """锚点扫描: 用若干报告期的已知真值反查槽位号(字段重校准工具)。

    :param records: {报告期YYYYMMDD: [float槽位...]}, 即 gpcw.read_gpcw 的第二返回值
    :param targets: {报告期: 真值}; 至少给 2 个报告期, 取各期命中槽位的交集
    :param rel_tol: 相对误差容差(需显著大于 float32 分辨率 1e-7, 默认 0.3%)
    :return: 升序槽位号列表; 空列表 = 无槽位匹配(多半是文件缺该科目)
    """
    common = None
    for d, tv in targets.items():
        rec = records.get(d)
        if not rec:
            raise KeyError(f"{d} 不在 records 中")
        tv = float(tv)
        idxs = {i + 1 for i, v in enumerate(rec) if v and abs(v - tv) <= rel_tol * abs(tv)}
        common = idxs if common is None else common & idxs
        if not common:
            return []
    return sorted(common)
