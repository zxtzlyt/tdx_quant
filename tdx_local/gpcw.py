# -*- coding: utf-8 -*-
"""通达信专业财务数据文件 (vipdoc/cw/gpcwYYYYMMDD.dat) 解析器。

文件布局(实测验证, 详见 docs/LOCAL_NOTES.md):
  头部20字节 '<1hI1H3L': [0]=1, [1]=报告期YYYYMMDD, [2]=记录数, [3]=数据区起始偏移, [4]=单条记录字节数
  索引区: 记录数 × 11字节 '<6s1c1L' -> (6位代码, 标志, 该记录在数据区的字节偏移)
  数据区: 每记录 (记录字节数/4) 个 float32, 顺序即官方文档的 FN1..FNn 字段
字段含义见 docs/tdx-quant-docs/03-tqcenter-财务/get_financial_data.md
(FN1 基本每股收益, FN2 扣非每股收益, FN3 每股未分配利润, FN4 每股净资产, FN5 每股资本公积金, ...)。

CLI 用法::

    python -m tdx_local.gpcw <cw目录或gpcw文件> [代码...]   # 代码不带市场后缀, 如 600519

数据来源提示: 支持TQ的官方金融终端下载专业财务需订阅; 部分券商定制版通达信
(如国泰君安)的盘后下载免费提供同类文件, 目录结构与格式完全一致。
"""
import glob
import os
import struct
import sys
from pathlib import Path

HEADER_FMT = "<1hI1H3L"
ITEM_FMT = "<6s1c1L"
HEADER_SIZE = struct.calcsize(HEADER_FMT)
ITEM_SIZE = struct.calcsize(ITEM_FMT)

# 少于该字节数视为下载中的空占位文件(实测占位文件只有20字节头)
MIN_VALID_SIZE = 1000


def read_gpcw(path: str) -> tuple:
    """读取单个 gpcw 文件。返回 (报告期YYYYMMDD字符串, {代码: [float字段...]})。"""
    blob = Path(path).read_bytes()
    if len(blob) < MIN_VALID_SIZE:
        raise ValueError(f"{path} 不是有效数据文件(仅 {len(blob)} 字节, 可能是下载占位)")
    header = struct.unpack(HEADER_FMT, blob[:HEADER_SIZE])
    report_date, count, rec_bytes = header[1], header[2], header[4]
    nfloats = rec_bytes // 4
    stocks = {}
    for i in range(count):
        code_b, _flag, offset = struct.unpack(
            ITEM_FMT, blob[HEADER_SIZE + i * ITEM_SIZE: HEADER_SIZE + (i + 1) * ITEM_SIZE])
        code = code_b.rstrip(b"\x00").decode("ascii", errors="replace")
        stocks[code] = struct.unpack(f"<{nfloats}f", blob[offset: offset + rec_bytes])
    return str(report_date), stocks


def list_reports(cw_dir: str) -> list:
    """列出目录内有效的报告期文件路径, 按报告期升序(自动跳过下载占位)。"""
    out = []
    for p in sorted(glob.glob(os.path.join(cw_dir, "gpcw*.dat"))):
        if os.path.getsize(p) >= MIN_VALID_SIZE:
            out.append(p)
    return out


def read_series(cw_dir: str, code: str, fields=None) -> dict:
    """读取某只股票的财务历史序列。

    :param cw_dir: vipdoc/cw 目录
    :param code: 6位代码(不带市场后缀), 如 '600519'
    :param fields: 需要的字段序号列表(1基), 如 [1, 4]; None 返回全部
    :return: {报告期YYYYMMDD: {f'FN{k}': value}}
    """
    code = code.lstrip("0").rjust(6, "0") if len(code) == 6 else code
    series = {}
    for path in list_reports(cw_dir):
        report_date, stocks = read_gpcw(path)
        rec = stocks.get(code)
        if rec is None:
            continue
        if fields:
            series[report_date] = {f"FN{k}": rec[k - 1] for k in fields if 0 < k <= len(rec)}
        else:
            series[report_date] = {f"FN{k+1}": v for k, v in enumerate(rec)}
    return series


def main(argv) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(argv) < 2:
        print(__doc__)
        return 1
    target, codes = argv[1], [c.lstrip("0").rjust(6, "0") if len(c) == 6 else c
                              for c in argv[2:]] or ["600519"]
    labels = {1: "FN1 基本每股收益", 2: "FN2 扣非每股收益", 3: "FN3 每股未分配利润",
              4: "FN4 每股净资产", 5: "FN5 每股资本公积金"}
    if os.path.isdir(target):
        for code in codes:
            print(f"== {code} 财务历史序列 ==")
            series = read_series(target, code, fields=list(labels))
            for date, rec in sorted(series.items()):
                cells = "  ".join(f"{labels[k].split()[1]}={rec[f'FN{k}']:.4f}" for k in labels)
                print(f"  {date}  {cells}")
    else:
        report_date, stocks = read_gpcw(target)
        print(f"文件: {target}  报告期: {report_date}  记录数: {len(stocks)}  "
              f"每条字段数: {len(next(iter(stocks.values())))}")
        for code in codes:
            rec = stocks.get(code)
            if not rec:
                print(f"{code}: 未找到")
                continue
            print(f"{code}:")
            for k, label in labels.items():
                print(f"  {label:<14} = {rec[k-1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
