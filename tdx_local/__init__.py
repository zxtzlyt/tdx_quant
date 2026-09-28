# -*- coding: utf-8 -*-
"""通达信 TQ 本地量化工具箱。

三层数据通道:
  1. TQ HTTP JSON-RPC (127.0.0.1:17709) —— 行情/快照/板块/交易日历等, 需运行支持 TQ 的通达信金融终端
  2. gpcw 专业财务文件解析 —— 读取 vipdoc/cw/gpcwYYYYMMDD.dat (FN1..FN584 字段)
  3. get_stock_info 的 J_ 系列字段 —— 免费的最新一期财务摘要
实测注意事项见仓库 docs/LOCAL_NOTES.md。
"""
from .tq_client import TqClient, TqError
from .gpcw import read_gpcw, read_series

__all__ = ["TqClient", "TqError", "read_gpcw", "read_series"]
__version__ = "0.1.0"
