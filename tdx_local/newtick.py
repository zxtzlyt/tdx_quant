# -*- coding: utf-8 -*-
"""通达信逐笔/分笔数据读取层(vipdoc/newtick)—— 实验性。

文件布局(2026-10-27 本机实测, sz000001 全 112 天对拍通过):
  - <市场><代码>.vid: 未压缩索引。16B 头 <IIII> = (version=2, 首日, 末日, 日数),
    其后每日一条 22B 记录 <IIIdH> = (日期YYYYMMDD, 该日解压后字节数,
    该日压缩后字节数, 疑似当日均价 f64, 未知 u16)。日期为十进制 YYYYMMDD 存 u32。
  - <市场><代码>.vtc: **每天一个 zlib 流连续拼接**(非 gzip); 第 i 个成员解压后
    长度 == vid 第 i 日 raw_size, 顺序一致。日段开头 4B = 日期 u32, 其后为
    逐笔记录体 —— **记录内部结构未逆向**(时间编码/价格定点/方向字段未知),
    解出的 data 请按 hex 自查; 对拍思路: 逐笔量合计 vs 当日 Volume、
    末笔价 vs 收盘价。

用法::

    from tdx_local import newtick

    days = newtick.read_days(directory, "000001.SZ")   # [{date, data}]
    #  -> data 为该日逐笔原始字节(结构未逆向, 见上)
"""
import struct
import zlib
from pathlib import Path

__all__ = ["read_vid", "read_days", "default_dir", "vid_path"]

_VID_HEAD = struct.Struct("<IIII")
_VID_DAY = struct.Struct("<IIIdH")


def default_dir():
    """newtick 目录: 环境变量 TDX_NEWTICK, 缺省 D:\\jyrj\\tdx\\vipdoc\\newtick(存在时)。"""
    import os
    env = os.environ.get("TDX_NEWTICK")
    if env:
        return env
    cand = r"D:\jyrj\tdx\vipdoc\newtick"
    return cand if Path(cand).is_dir() else ""


def vid_path(directory, code):
    """000001.SZ -> <dir>/sz000001.vid(市场小写)。"""
    num, mkt = code.split(".")
    return Path(directory) / f"{mkt.lower()}{num}.vid"


def read_vid(path) -> dict:
    """vid 索引 -> {"version", "first", "last", "days": [{date, raw_size,
    comp_size, price}]}。文件缺失返回 {}。"""
    p = Path(path)
    if not p.exists():
        return {}
    blob = p.read_bytes()
    ver, d1, d2, n = _VID_HEAD.unpack_from(blob)
    days = []
    for i in range(n):
        d, sz, comp, f64, _u16 = _VID_DAY.unpack_from(blob, _VID_HEAD.size + i * _VID_DAY.size)
        days.append({"date": d, "raw_size": sz, "comp_size": comp, "price": f64})
    return {"version": ver, "first": d1, "last": d2, "days": days}


def read_days(directory, code) -> list:
    """逐笔数据按日解出 -> [{"date", "data"}](data 为该日逐笔原始字节)。

    逐成员解压并按 vid raw_size 校验; 解压尺寸不符抛 ValueError(文件被
    客户端写入中/截断时可能发生, 重试或跳过该代码)。
    """
    vid = read_vid(vid_path(directory, code))
    if not vid.get("days"):
        return []
    vtc = vid_path(directory, code).with_suffix(".vtc")
    blob = vtc.read_bytes()
    out, off = [], 0
    for day in vid["days"]:
        do = zlib.decompressobj()
        raw = do.decompress(blob[off:])
        used = len(blob) - off - len(do.unused_data)
        off += used
        if len(raw) != day["raw_size"]:
            raise ValueError(f"{code} {day['date']}: 解压 {len(raw)}B != vid 记录 "
                             f"{day['raw_size']}B(vtc 可能被写入中)")
        out.append({"date": day["date"], "data": raw[4:]})
    return out
