# -*- coding: utf-8 -*-
"""测试共享配置: 路径与数据目录常量。

真实数据目录默认指向作者本机路径; 其他机器用同名环境变量覆盖
(TDX_CW_DIR / TDX_GTJA_CW / TDX_GTJA_LDAY), 目录缺失时相关用例自动跳过。
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CW_DIR = os.environ.get("TDX_CW_DIR", r"D:\jyrj\tdx\vipdoc\cw")        # 分析用财务文件目录(已从 gtja 同步)
GTJA_CW = os.environ.get("TDX_GTJA_CW", r"D:\jyrj\gtja\vipdoc\cw")     # 财务文件数据源目录
GTJA_LDAY = os.environ.get("TDX_GTJA_LDAY", r"D:\jyrj\gtja\vipdoc\sh\lday")  # 日线数据源目录(全历史)
