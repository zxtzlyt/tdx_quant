# -*- coding: utf-8 -*-
"""测试共享配置: 路径与数据目录常量(本机实测目录, 缺失时相关用例自动跳过)。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CW_DIR = r"D:\jyrj\tdx\vipdoc\cw"        # 分析用财务文件目录(已从 gtja 同步)
GTJA_CW = r"D:\jyrj\gtja\vipdoc\cw"      # 财务文件数据源目录
GTJA_LDAY = r"D:\jyrj\gtja\vipdoc\sh\lday"   # 日线数据源目录(全历史)
