# -*- coding: utf-8 -*-
"""扩展市场代码表 —— TQ 接口的市场枚举常量(官方文档 constants.md「市场类型」)。

TQ 接口的证券代码是后缀风格("688318.SH"); 扩展市场(港股/美股/期货/期权/
宏观等)用各自后缀, 本表给出后缀 -> 市场号 的对照与分类, 供筛选与文档用途。
注意: 扩展市场行情需要客户端先下载对应数据(本机 vipdoc/ds 为空时接口返回
空信封), 表本身不触发下载。

来源: docs/tdx-quant-docs/11-常量枚举/constants.md(2026-10-27 镜像核对)。
"""
__all__ = ["MARKETS", "A_SHARE", "FUTURES", "INDEX_PROVIDERS", "is_a_share"]

# 后缀: (市场号, 名称)
MARKETS = {
    ".SH": (1, "上海证券交易所"),
    ".SZ": (0, "深圳证券交易所"),
    ".BJ": (2, "北京证券交易所"),
    ".HK": (31, "香港交易所"),
    ".HI": (27, "港股指数"),
    ".US": (74, "美国股票"),
    ".NQ": (44, "新三板"),
    ".OF": (33, "开放式基金"),
    ".CSI": (62, "中证指数"),
    ".CNI": (102, "国证指数"),
    ".SHO": (8, "上交所个股期权"),
    ".SZO": (9, "深交所个股期权"),
    ".CFF": (47, "中金所期货"),
    ".CZC": (28, "郑商所期货"),
    ".DCE": (29, "大商所期货"),
    ".SHF": (30, "上期所期货"),
    ".INE": (30, "上海能源中心期货"),
    ".GFE": (66, "广期所期货"),
    ".HG": (38, "国内宏观"),
    ".QHZ": (42, "期货类指数"),
}

A_SHARE = (".SH", ".SZ", ".BJ")
FUTURES = (".CFF", ".CZC", ".DCE", ".SHF", ".INE", ".GFE")
INDEX_PROVIDERS = (".CSI", ".CNI")


def is_a_share(code: str) -> bool:
    """代码是否 A股口径(按后缀; 6 位裸代码按首位推断)。"""
    for mkt in A_SHARE:
        if code.endswith(mkt):
            return True
    if "." not in code and len(code) == 6 and code.isdigit():
        return code[0] in "034689"      # 沪深京 A股/B股首位
    return False
