# -*- coding: utf-8 -*-
"""数据体检 —— 一条命令报告本地数据资产的覆盖情况: kcache/分钟归档/gpcw。

用法::

    python -m tdx_local.audit                     # 全部体检
    python -m tdx_local.audit --kcache-only       # 只看日K缓存

体检不是校验器: 它报告"有什么、到哪天、缺多少", 帮你决定今晚要不要
增量/补数; 逐笔对账用 lday.day_counts / archive 的 check 子命令。
"""
import os
import sys
import time
from pathlib import Path

from . import kcache, lday

__all__ = ["audit_kcache", "audit_minutes", "audit_cw", "run_audit"]


def _fmt_date(d):
    return str(d) if d else "--"


def audit_kcache(cache_dir=None, tail=8) -> dict:
    """日K缓存: 文件数/总根数/整体区间 + 末日期最落后的 tail 个代码。"""
    cache_dir = cache_dir or kcache.default_dir()
    files = sorted(Path(cache_dir).glob("*.day"))
    total, oldest, newest, laggards = 0, None, None, []
    today_hint = 0
    for f in files:
        n = f.stat().st_size // 32
        total += n
        if n == 0:
            continue
        d0 = lday.last_date(str(f))
        if d0:
            oldest = d0 if oldest is None or d0 < oldest else oldest
            newest = d0 if newest is None or d0 > newest else newest
            laggards.append((d0, n, f"{f.stem[2:]}.{f.stem[:2].upper()}"))
    laggards.sort()
    codes = [f"{f.stem[2:]}.{f.stem[:2].upper()}" for f in files]
    return {"dir": str(cache_dir), "n_files": len(files), "total_bars": total,
            "oldest": oldest, "newest": newest, "codes": codes,
            "laggards": laggards[:tail]}


def audit_minutes(base_dir=None, periods=("1m", "5m")) -> dict:
    """分钟归档: 每周期 {n_files, total_bytes}(只 stat 不解压 —— 全市场归档
    按 2026-10 实测 5m 即数 GB, 逐文件解压统计是天级耗时; 按日对账请用
    archive_minutes_vipdoc.py 的 check 子命令, 那是单代码粒度的)。"""
    out = {}
    for period in periods:
        d = Path(base_dir) / period if base_dir else _minute_dir(period)
        files = list(d.glob("*.bin")) + list(d.glob("*.bin.gz")) if d.is_dir() else []
        total = sum(f.stat().st_size for f in files)
        out[period] = {"dir": str(d), "n_files": len(files), "total_bytes": total}
    return out


def _minute_dir(period):
    env = os.environ.get("TDX_MIN_ARCHIVE")
    base = env or str(Path(__file__).resolve().parent.parent / "minute_archive")
    return Path(base) / period


def audit_cw(cw_dir=None) -> dict:
    """专业财务文件目录: 有数据的文件/最新报告期。"""
    cw_dir = cw_dir or os.environ.get("TDX_CW_DIR") or ""
    d = Path(cw_dir) if cw_dir else Path(__file__).resolve().parent.parent / "kcache"
    files = sorted(d.glob("gpcw*.dat")) if Path(cw_dir or "").is_dir() else []
    live, latest = 0, None
    for f in files:
        if f.stat().st_size > 64:                 # 占位文件约 20 字节
            live += 1
            stem = f.stem.replace("gpcw", "")
            latest = max(latest, stem) if latest else stem
    return {"dir": str(cw_dir), "n_files": len(files), "n_live": live,
            "latest_live": latest}


def run_audit(kcache_dir=None, cw_dir=None) -> int:
    """跑全部体检并打印报告; 返回 0。"""
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    t0 = time.time()
    kc = audit_kcache(kcache_dir)
    print("=" * 62)
    print(f"数据体检 @ {time.strftime('%Y-%m-%d %H:%M')}")
    print("-" * 62)
    print(f"[日K缓存] {kc['n_files']} 只 {kc['total_bars']:,} 根 "
          f"{_fmt_date(kc['oldest'])} ~ {_fmt_date(kc['newest'])}")
    if kc["laggards"]:
        print("  末日期最落后的(考虑增量或剔除):")
        for d, n, code in kc["laggards"]:
            print(f"    {code:<12} 末 {d}  {n:,} 根")
    mins = audit_minutes()
    for p, m in mins.items():
        if m["n_files"]:
            gb = m["total_bytes"] / 1e9
            size = f"{gb:.1f}GB" if gb >= 1 else f"{m['total_bytes'] / 1e6:.0f}MB"
            print(f"[{p}归档] {m['n_files']} 只 {size} ({m['dir']})")
        else:
            print(f"[{p}归档] (空: {m['dir']})")
    cw = audit_cw(cw_dir)
    if cw["n_files"]:
        print(f"[专业财务] {cw['n_live']}/{cw['n_files']} 个报告期有数据, 最新 {cw['latest_live']}")
    else:
        print("[专业财务] 未找到 gpcw 目录(设 TDX_CW_DIR)")
    print("=" * 62)
    print(f"耗时 {time.time() - t0:.1f}s; 建议动作: python examples/daily_pipeline.py")
    return 0


def main(argv) -> int:
    args = [a for a in argv[1:] if not a.startswith("--")]
    kw = {}
    if args:
        kw["kcache_dir"] = args[0]
    if "--no-cw" in argv:
        kw["cw_dir"] = "/nonexistent"
    return run_audit(**kw)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
