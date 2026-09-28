# -*- coding: utf-8 -*-
"""通达信 TQ 本地量化工具箱。

三层数据通道:
  1. TQ HTTP JSON-RPC (127.0.0.1:17709) —— 行情/快照/板块/交易日历等, 需运行支持 TQ 的通达信金融终端
  2. gpcw 专业财务文件解析 —— 读取 vipdoc/cw/gpcwYYYYMMDD.dat (FN1..FN584 字段)
  3. get_stock_info 的 J_ 系列字段 —— 免费的最新一期财务摘要
实测注意事项见仓库 docs/LOCAL_NOTES.md。
"""
from . import cw_fields
from .tq_client import TqClient, TqError

# gpcw 相关导出走惰性加载(PEP 562): `python -m tdx_local.gpcw` 时避免 runpy
# "found in sys.modules" 警告, 且不拖累纯行情场景的导入开销。
_GPCW_EXPORTS = ("GpcwCorrupt", "GpcwPlaceholder", "GpcwReportGap", "approx_announce_date",
                 "close_enough", "read_gpcw", "read_series", "scan_reports",
                 "single_quarters", "sync_cw")


def __getattr__(name):
    if name in _GPCW_EXPORTS:
        from . import gpcw
        return getattr(gpcw, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["TqClient", "TqError", "cw_fields", "read_gpcw", "read_series", "scan_reports",
           "single_quarters", "sync_cw", "close_enough", "approx_announce_date",
           "GpcwPlaceholder", "GpcwCorrupt", "GpcwReportGap"]
__version__ = "0.2.0"
