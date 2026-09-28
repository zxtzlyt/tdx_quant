# -*- coding: utf-8 -*-
"""通达信日线文件 (vipdoc/<市场>/lday/<市场><代码>.day) 解析与合并同步。

文件布局: 每根 32 字节 '<IIIIIfII>' = 日期YYYYMMDD, 开/高/低/收(×100 定点整数),
成交额(元, float), 成交量(股, int), 1 个保留字段。按日期升序排列。

背景(见 docs/LOCAL_NOTES.md): 券商定制版(gtja)客户端常年盘后下载, lday 是
全市场完整历史(数千文件/数 GB); 官方 tdx 客户端只落地看过/刷新过的标的。
`sync_lday` 把前者并入后者:

  - 目标侧没有的代码 -> 整文件复制(同格式, 零解析), 客户端开着也安全;
  - 两边都有的代码   -> 按日期并集合并(重叠日以目标侧为准), 补老历史不丢新尾巴;
    (注意 gtja 尾部常滞后, 如 2026-07-30; 合并后以目标侧的更新尾部为准)

CLI 用法::

    python -m tdx_local.lday sync <源lday目录> <目标lday目录> [--only-missing] [--dry-run]

only_missing 只补目标缺失的文件(纯新增, 不改已有文件); 全量合并建议先关客户端。
"""
import glob
import os
import shutil
import struct
import sys

REC = struct.Struct("<IIIIIfII")


def read_lday(path: str) -> dict:
    """读日线文件 -> {日期YYYYMMDD(int): (开, 高, 低, 收, 成交额元, 成交量股)}。"""
    blob = open(path, "rb").read()
    out = {}
    for i in range(len(blob) // 32):
        d, o, h, l, c, amt, vol, _ = REC.unpack_from(blob, i * 32)
        out[d] = (o / 100, h / 100, l / 100, c / 100, amt, vol)
    return out


def write_lday(path: str, bars: dict) -> int:
    """按日期升序写日线文件(先写临时文件再原子替换)。返回根数。"""
    buf = bytearray()
    for d in sorted(bars):
        o, h, l, c, amt, vol = bars[d]
        buf += REC.pack(d, round(o * 100), round(h * 100), round(l * 100),
                        round(c * 100), amt, int(vol), 0)
    tmp = path + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(buf)
    os.replace(tmp, path)
    return len(bars)


def merge_day(src_path: str, dst_path: str) -> dict:
    """把源文件并进目标文件(日期并集; 重叠日以目标侧为准)。

    返回 {added, dates, changed, range}; changed=False 表示目标已覆盖源, 未改写。
    """
    src, dst = read_lday(src_path), read_lday(dst_path)
    added = set(src) - set(dst)
    if not added:
        return dict(added=0, dates=len(dst), changed=False)
    merged = dict(src)
    merged.update(dst)
    n = write_lday(dst_path, merged)
    return dict(added=len(added), dates=n, changed=True,
                range=(min(merged), max(merged)))


def sync_lday(src_dir: str, dst_dir: str, only_missing: bool = False,
              dry_run: bool = False) -> dict:
    """同步源 lday 目录 -> 目标 lday 目录。

    only_missing=True 只复制目标缺失的文件(纯新增, 不动已有文件, 客户端开着也安全);
    否则对两边都存在的文件做并集合并(逐文件重写目标, 全量时较慢, 建议先关客户端)。
    返回 {copied, merged, skipped, copied_files, dry_run}。
    """
    copied, merged, skipped = 0, 0, 0
    copied_files = []
    for src in sorted(glob.glob(os.path.join(src_dir, "*.day"))):
        name = os.path.basename(src)
        dst = os.path.join(dst_dir, name)
        if not os.path.exists(dst):
            if not dry_run:
                shutil.copy2(src, dst)
            copied += 1
            if len(copied_files) < 20:
                copied_files.append(name)
        elif only_missing:
            skipped += 1
        else:
            if dry_run:
                merged += 1  # 粗计: 不解析, 以"会尝试合并"计
            elif merge_day(src, dst)["changed"]:
                merged += 1
    return dict(copied=copied, merged=merged, skipped=skipped,
                copied_files=copied_files, dry_run=dry_run)


def main(argv) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(argv) < 4 or argv[1] != "sync":
        print(__doc__)
        return 1
    rep = sync_lday(argv[2], argv[3],
                    only_missing="--only-missing" in argv[4:],
                    dry_run="--dry-run" in argv[4:])
    tag = "dry-run" if rep["dry_run"] else "完成"
    print(f"同步{tag}: 新复制 {rep['copied']} 个, 合并 {rep['merged']} 个, 跳过 {rep['skipped']} 个")
    for name in rep["copied_files"]:
        print("  +", name)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
