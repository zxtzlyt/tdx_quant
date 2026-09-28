# -*- coding: utf-8 -*-
"""示例: 读取本地 gpcw 专业财务文件, 输出某股票的每股收益/净资产历史序列。

数据文件来源(二选一, 目录结构一致):
  1. 券商定制版通达信(如国泰君安)盘后下载的财务数据: <券商tdx安装目录>/vipdoc/cw
  2. 官方金融终端订阅后下载的: <官方tdx安装目录>/vipdoc/cw

用法: python examples/financial_demo.py <cw目录> [代码, 默认 600519]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tdx_local.gpcw import read_series  # noqa: E402

FIELDS = {1: "每股收益", 4: "每股净资产", 3: "每股未分配利润"}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cw_dir = sys.argv[1]
    code = sys.argv[2] if len(sys.argv) > 2 else "600519"

    series = read_series(cw_dir, code, fields=list(FIELDS))
    if not series:
        print(f"{code}: 在 {cw_dir} 中未找到财务记录(检查目录与数据是否已下载)")
        return
    print(f"{code} 财务历史序列({len(series)}期):")
    print(f"{'报告期':<10}" + "".join(f"{name:>12}" for name in FIELDS.values()))
    for date, rec in sorted(series.items()):
        row = "".join(f"{rec.get(f'FN{k}', float('nan')):>12.4f}" for k in FIELDS)
        print(f"{date:<10}{row}")


if __name__ == "__main__":
    main()
