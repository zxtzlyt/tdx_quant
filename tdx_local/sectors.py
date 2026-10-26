# -*- coding: utf-8 -*-
"""板块文件解析 —— hq_cache 板块定义与 blocknew 自定义板块, 纯 GBK 文本。

格式(2026-10-27 本机实测, D:\\jyrj\\tdx):
  - T0002/hq_cache/*.dat: `#板块名\\r\\n` 后每行一个代码, 直到下一个 `#`。
    代码行 7 位 = 市场标志 1 位 + 6 位代码(0=深 1=沪, 2=北交所为推断);
    跨市场板块(中证/基金/港美股)行形如 `市场号,代码` 或带 CNY 后缀, 不属
    A股口径, 跳过并计数。
  - T0002/blocknew/*.blk: 自定义板块, 每 7 位一行(同上编码), 文件名即板块名。
    pick_technical 写回的自选板块从这里能读回来(信号持久化闭环)。

用法::

    from tdx_local import sectors

    blocks = sectors.read_hq_blocks(r"D:\\jyrj\\tdx\\T0002\\hq_cache")
    blocks["融资融券"]        # -> ["000001.SZ", ...]
    mine = sectors.read_custom_blocks(r"D:\\jyrj\\tdx\\T0002\\blocknew")
"""
import os
from pathlib import Path

__all__ = ["parse_block_file", "read_hq_blocks", "read_custom_blocks",
           "default_t0002", "find_block"]

_MKT_FLAG = {"0": ".SZ", "1": ".SH", "2": ".BJ"}


def _norm_7(line):
    """7 位代码行 -> "600000.SH"; 无法识别返回 None。"""
    mkt = _MKT_FLAG.get(line[0])
    return f"{line[1:]}{mkt}" if mkt else None


def _norm_6(line):
    """6 位代码行(老格式) -> 按首位推断市场。"""
    if line[0] in "69" or line.startswith("68"):
        return line + ".SH"
    if line[0] in "03":
        return line + ".SZ"
    if line[0] in "48":
        return line + ".BJ"
    return None


def default_t0002():
    """本机 T0002 目录: 环境变量 TDX_T0002, 缺省 D:\\jyrj\\tdx\\T0002(存在时)。"""
    env = os.environ.get("TDX_T0002")
    if env:
        return env
    cand = r"D:\jyrj\tdx\T0002"
    return cand if Path(cand).is_dir() else ""


def parse_block_file(path, encoding="gbk") -> list:
    """hq_cache 板块文件 -> [{"name", "codes", "skipped"}]。

    skipped 为非 A股口径行数(跨市场/逗号行等), 不中断解析 —— 板块文件
    混排多种市场, 解析器要容错。
    """
    text = Path(path).read_bytes().decode(encoding, errors="replace")
    out, cur = [], None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            name = line.lstrip("#").split(",")[0].strip()
            if name:                                  # `######` 分隔线不是板块
                cur = {"name": name, "codes": [], "skipped": 0}
                out.append(cur)
            continue
        if cur is None:
            continue
        if "," in line or not line.isdigit():
            cur["skipped"] += 1
            continue
        code = (_norm_7(line) if len(line) == 7
                else _norm_6(line) if len(line) == 6 else None)
        if code:
            cur["codes"].append(code)
        else:
            cur["skipped"] += 1
    return [b for b in out if b["codes"] or b["skipped"]]


def read_hq_blocks(hq_cache_dir) -> dict:
    """hq_cache 目录全部 *.dat -> {板块名: [A股代码]}(同名板块后者覆盖)。"""
    out = {}
    d = Path(hq_cache_dir)
    if not d.is_dir():
        return out
    for f in sorted(d.glob("*.dat")):
        if f.name.startswith("ds_"):          # 扩展市场证券表, 非板块
            continue
        for blk in parse_block_file(f):
            out[blk["name"]] = blk["codes"]
    return out


def read_custom_blocks(blocknew_dir) -> dict:
    """blocknew 目录 *.blk -> {板块名(文件名): [A股代码]}。"""
    out = {}
    d = Path(blocknew_dir)
    if not d.is_dir():
        return out
    for f in sorted(d.glob("*.blk")):
        text = f.read_bytes().decode("gbk", errors="replace")
        codes = []
        for line in text.split():
            line = line.strip()
            if len(line) == 7 and line.isdigit():
                code = _norm_7(line)
                if code:
                    codes.append(code)
        out[f.stem] = codes
    return out


def find_block(blocks, keyword):
    """板块名模糊查找 -> (名, 代码列表); 无命中返回 (None, [])。空成分不算命中。"""
    for name, codes in blocks.items():
        if keyword in name and codes:
            return name, codes
    return None, []
