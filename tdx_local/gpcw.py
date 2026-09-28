# -*- coding: utf-8 -*-
"""通达信专业财务数据文件 (vipdoc/cw/gpcwYYYYMMDD.dat) 解析器。

文件布局(实测验证, 详见 docs/LOCAL_NOTES.md):
  头部20字节 '<1hI1H3L': [0]=1, [1]=报告期YYYYMMDD, [2]=记录数, [3]=数据区起始偏移, [4]=单条记录字节数
  索引区: 记录数 × 11字节 '<6s1c1L' -> (6位代码, 标志, 该记录在数据区的字节偏移)
  数据区: 每记录 (记录字节数/4) 个 float32, 顺序即官方文档的 FN1..FNn 字段
字段含义见 docs/tdx-quant-docs/03-tqcenter-财务/get_financial_data.md
(FN1 基本每股收益, FN2 扣非每股收益, FN3 每股未分配利润, FN4 每股净资产, FN5 每股资本公积金, ...)。

**字段编号与文档有实测偏差**(文档缺失区/单季陷阱/新准则缺失科目),
语义、单位与实证状态以 `tdx_local.cw_fields` 注册表为准; 本模块的 read_series
因此支持按注册名取数。本模块另提供(对应 LOCAL_NOTES 实测坑):

  close_enough          float32 精度下的勾稽比较(勿用 ==)
  scan_reports          报告期文件状态扫描(ok/placeholder/suspect)
  cumulative            累计口径序列(年初至报告期; 年报即全年)
  single_quarters       累计 -> 自然单季(带连续性断言, 缺前置报告期抛 GpcwReportGap)
  approx_announce_date  报告期 -> 法定披露截止日(point-in-time 近似, 实际公告常更早)
  sync_cw               从数据源目录(如 gtja vipdoc/cw)同步, 自动跳过 20 字节下载占位

CLI 用法::

    python -m tdx_local.gpcw <cw目录或gpcw文件> [代码...]   # 代码不带市场后缀, 如 600519
    python -m tdx_local.gpcw sync <源cw目录> <目标cw目录> [--dry-run]

数据来源提示: 支持TQ的官方金融终端下载专业财务需订阅; 部分券商定制版通达信
(如国泰君安)的盘后下载免费提供同类文件, 目录结构与格式完全一致。
"""
import glob
import os
import shutil
import struct
import sys
from pathlib import Path

from . import cw_fields

HEADER_FMT = "<1hI1H3L"
ITEM_FMT = "<6s1c1L"
HEADER_SIZE = struct.calcsize(HEADER_FMT)
ITEM_SIZE = struct.calcsize(ITEM_FMT)

# 少于该字节数视为下载中的空占位文件(实测占位文件只有20字节头;
# 注意 shell 的 `test -s` 只拦 0 字节, 拦不住占位)。
MIN_VALID_SIZE = 1000
# 槽位值为 float32: 相对分辨率约 1e-7。勾稽校验(如 归母净利/总股本 vs EPS)
# 不要用 ==, 用 close_enough。
FLOAT32_REL_TOL = 1e-6

_QUARTER_MDS = ("0331", "0630", "0930", "1231")


class GpcwPlaceholder(ValueError):
    """文件为下载中/未披露的空占位(约20字节)。"""


class GpcwCorrupt(ValueError):
    """文件头/数据区不完整或越界, 解析不可信。"""


class GpcwReportGap(ValueError):
    """单季差分所需的前置报告期缺失(受影响报告期见异常消息)。"""


def close_enough(a, b, rel=FLOAT32_REL_TOL) -> bool:
    """float32 存储值与真值/参考值的勾稽比较(相对容差, 默认 1e-6)。

    例: close_enough(86228148224.0, 86228146421.62) -> True
    (float32 存 862 亿级净利时尾数含数千元噪声, == 判等必失败)。
    """
    if a is None or b is None:
        return a is None and b is None
    a, b = float(a), float(b)
    scale = max(abs(a), abs(b), 1.0)
    return abs(a - b) <= rel * scale


def read_gpcw(path) -> tuple:
    """读取单个 gpcw 文件。返回 (报告期YYYYMMDD字符串, {代码: [float字段...]})。

    占位文件抛 GpcwPlaceholder, 头部/数据区异常抛 GpcwCorrupt。
    """
    blob = Path(path).read_bytes()
    if len(blob) < MIN_VALID_SIZE:
        raise GpcwPlaceholder(
            f"{path} 仅 {len(blob)} 字节: 报告期未披露或下载中的占位文件")
    header = struct.unpack(HEADER_FMT, blob[:HEADER_SIZE])
    report_date, count, rec_bytes = header[1], header[2], header[4]
    if header[0] != 1 or count <= 0 or rec_bytes <= 0 or rec_bytes % 4:
        raise GpcwCorrupt(f"{path} 文件头异常: {header}")
    nfloats = rec_bytes // 4
    base = HEADER_SIZE + count * ITEM_SIZE
    stocks = {}
    for i in range(count):
        code_b, _flag, offset = struct.unpack(
            ITEM_FMT, blob[HEADER_SIZE + i * ITEM_SIZE: HEADER_SIZE + (i + 1) * ITEM_SIZE])
        if offset < base or offset + rec_bytes > len(blob):
            raise GpcwCorrupt(f"{path} 数据区越界: 记录{i} offset={offset}")
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


def scan_reports(cw_dir: str) -> list:
    """扫描报告期文件状态(轻量: 只读 20 字节头, 不全量解析)。

    返回按报告期升序的 [{date, path, bytes, status}];
    status: ok / placeholder(下载占位) / suspect(头部非法或与文件名报告期不一致)。
    连续性检查(specifically 单季差分)前可用它确认无缺期。
    """
    rows = []
    for p in sorted(glob.glob(os.path.join(cw_dir, "gpcw*.dat"))):
        size = os.path.getsize(p)
        date = os.path.basename(p)[4:-4]
        if size < MIN_VALID_SIZE:
            rows.append(dict(date=date, path=p, bytes=size, status="placeholder"))
            continue
        header = struct.unpack(HEADER_FMT, Path(p).read_bytes()[:HEADER_SIZE])
        head_ok = (header[0] == 1 and 19000101 < header[1] < 21000101
                   and header[2] > 0 and header[4] > 0 and header[4] % 4 == 0)
        status = "ok" if (head_ok and str(header[1]) == date) else "suspect"
        rows.append(dict(date=date, path=p, bytes=size, status=status))
    return rows


def read_series(cw_dir: str, code: str, fields=None, on_error: str = "skip") -> dict:
    """读取某只股票的财务历史序列。

    :param cw_dir: vipdoc/cw 目录
    :param code: 6位代码(不带市场后缀), 如 '600519'
    :param fields: 需要的字段列表 —— 1基槽位号(int)或 cw_fields 注册名/别名(str);
                   None 返回全部。注意槽位语义: FN230/232/234 实测为单季值,
                   累计口径请用注册名('营业收入'等)或 FN74/95/96/107。
    :param on_error: 'skip' 跳过占位/损坏文件(静默, 可用 scan_reports 核查);
                     'raise' 直接抛出。
    :return: {报告期YYYYMMDD: {f'FN{k}': value}}
    """
    code = code.lstrip("0").rjust(6, "0") if len(code) == 6 else code
    slots = None
    if fields is not None:
        slots = [cw_fields.resolve(f) if isinstance(f, str) else f for f in fields]
    series = {}
    for path in list_reports(cw_dir):
        try:
            report_date, stocks = read_gpcw(path)
        except (GpcwPlaceholder, GpcwCorrupt):
            if on_error == "raise":
                raise
            continue
        rec = stocks.get(code)
        if rec is None:
            continue
        if slots:
            series[report_date] = {f"FN{k}": rec[k - 1] for k in slots if 0 < k <= len(rec)}
        else:
            series[report_date] = {f"FN{k+1}": v for k, v in enumerate(rec)}
    return series


def cumulative(cw_dir: str, code: str, field, start: str = "", end: str = "") -> dict:
    """累计口径序列: {报告期YYYYMMDD: 年初至该期累计值}。

    field 为 cw_fields 注册名或 FN 槽位号; 年报(1231)的值即全年值。
    利润表/现金流量表累计槽位: 营业收入=FN74, 净利润=FN95, 归母=FN96,
    经营现金流净额=FN107 (FN230/232/234 是单季值, 别混用)。
    """
    slot = cw_fields.resolve(field)
    series = read_series(cw_dir, code, fields=[slot])
    return {d: rec[f"FN{slot}"] for d, rec in sorted(series.items())
            if d[4:] in _QUARTER_MDS and (not start or d >= start) and (not end or d <= end)}


def single_quarters(cw_dir: str, code: str, field,
                    start: str = "", end: str = "", on_missing: str = "raise") -> dict:
    """累计序列 -> 自然单季序列: {报告期YYYYMMDD: 单季值}。

    Q1=当季累计; Q2/Q3/Q4=当期累计-上期累计, 因此依赖报告期文件连续。
    start/end 只过滤输出窗口(差分仍用全量历史, 窗口边缘不会人为制造缺口);
    缺口告警也只看窗口内受影响的报告期, 窗口外的历史缺口不拦截。
    前置报告期缺失时: on_missing='raise' 抛 GpcwReportGap; 'skip' 打警告后略过。
    """
    slot = cw_fields.resolve(field)
    cum = cumulative(cw_dir, code, slot)
    prev_md = {"0630": "0331", "0930": "0630", "1231": "0930"}
    out, blocked = {}, []
    for d, v in cum.items():
        if d[4:] == "0331":
            out[d] = v
            continue
        prev_key = d[:4] + prev_md[d[4:]]
        if prev_key in cum:
            out[d] = v - cum[prev_key]
        else:
            blocked.append(d)
    hit = [d for d in blocked
           if (not start or d >= start) and (not end or d <= end)]
    if hit:
        msg = f"单季差分缺少前置报告期(受影响报告期: {', '.join(hit)})"
        if on_missing == "raise":
            raise GpcwReportGap(msg)
        print(f"[gpcw] 警告: {msg}", file=sys.stderr)
    return {d: v for d, v in out.items()
            if (not start or d >= start) and (not end or d <= end)}


def approx_announce_date(report_date: str) -> str:
    """报告期 -> 法定披露截止日(YYYYMMDD), point-in-time 回测的近似公告日。

    时限规则: 一季报/年报 04-30, 中报 08-31, 三季报 10-31。
    注意实际公告常早于截止日(如茅台年报多在 3 月底/4 月初), 需要精确
    announce_time 只能走 HTTP get_financial_data(report_type='announce_time')。
    """
    d = str(report_date)
    y, md = d[:4], d[4:]
    table = {"0331": f"{y}0430", "0630": f"{y}0831", "0930": f"{y}1031",
             "1231": f"{int(y) + 1}0430"}
    if md not in table:
        raise ValueError(f"非标准报告期(需 0331/0630/0930/1231): {report_date}")
    return table[md]


def sync_cw(src_dir: str, dst_dir: str, dry_run: bool = False) -> dict:
    """把数据源目录(如 gtja 客户端 vipdoc/cw)的财务文件同步到分析用目录。

    规则: 跳过 20 字节下载占位(< MIN_VALID_SIZE, `test -s` 拦不住它们);
    目标缺失或与源大小不一致时覆盖复制(保留源 mtime); 不删除目标多余文件。
    大小一致即视为最新(报告期文件一经写出不再变更)。
    返回 {copied, up_to_date, skipped_placeholder, dry_run}。
    """
    copied, uptodate, placeholders = [], [], 0
    for src in sorted(glob.glob(os.path.join(src_dir, "gpcw*.dat"))):
        name = os.path.basename(src)
        if os.path.getsize(src) < MIN_VALID_SIZE:
            placeholders += 1
            continue
        dst = os.path.join(dst_dir, name)
        if os.path.exists(dst) and os.path.getsize(dst) == os.path.getsize(src):
            uptodate.append(name)
            continue
        if not dry_run:
            shutil.copy2(src, dst)
        copied.append(name)
    return dict(copied=copied, up_to_date=uptodate,
                skipped_placeholder=placeholders, dry_run=dry_run)


def main(argv) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(argv) < 2:
        print(__doc__)
        return 1
    if argv[1] == "sync":
        if len(argv) < 4:
            print("用法: python -m tdx_local.gpcw sync <源cw目录> <目标cw目录> [--dry-run]")
            return 1
        rep = sync_cw(argv[2], argv[3], dry_run="--dry-run" in argv[4:])
        tag = "dry-run" if rep["dry_run"] else "完成"
        print(f"同步{tag}: 复制 {len(rep['copied'])} 个, 已最新 {len(rep['up_to_date'])} 个, "
              f"跳过占位 {rep['skipped_placeholder']} 个")
        for name in rep["copied"]:
            print("  +", name)
        return 0
    target = argv[1]
    codes = [c.lstrip("0").rjust(6, "0") if len(c) == 6 else c for c in argv[2:]] or ["600519"]
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
