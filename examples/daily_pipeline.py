# -*- coding: utf-8 -*-
"""盘后一条龙 —— 分钟归档 -> (可选)券商 lday 合并 -> kcache 日线增量, 一条命令。

每天收盘后的数据主链路本来是三条独立命令(官方下载器/DataTool 是 GUI, 不在此列):
  1. 分钟归档(vipdoc 直读, 离线可跑, 转档 GUI 截窗不影响);
  2. 券商定制版 lday -> 官方客户端目录(补历史, 日常只补新文件);
  3. kcache 日线增量(TQ 在线, 只拉缓存末日期之后的新段)。
本脚本按参数区开关依次执行, 单步失败不影响后续步骤, 最后汇总一张表;
配 Windows 任务计划每天定时跑, 分钟深度和日K缓存就不用手动维护。

用法: python examples/daily_pipeline.py                 # 按参数区默认全跑
      python examples/daily_pipeline.py --no-kcache     # 只跑离线步(客户端不开时)
      python examples/daily_pipeline.py --only-kcache   # 只跑日K增量

任务计划(每天 18:30, 以实际收盘后 DataTool/下载器完成为准):
  schtasks /Create /TN "tdx_daily_pipeline" /SC DAILY /ST 18:30 ^
    /TR "python D:\\my_program\\tdx_quant\\examples\\daily_pipeline.py"
"""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))     # 同目录配方可 import

from tdx_local import TqClient, TqError, kcache, lday
import archive_minutes_vipdoc as amv

# ============================ 参数区(按需修改) ============================
RUN_MINUTES = True
MINUTE_PERIODS = ("1m",)          # 全市场体量参考见 archive_minutes_vipdoc.py
MINUTE_ALL = False                # True = 全市场(首跑种子 5m 约 8GB / 1m 约 45GB)
MINUTE_CODES = amv.CODES          # 关注池, 与 vipdoc 归档配方一致
VIPDOC = amv.VIPDOC               # TDX_VIPDOC 环境变量优先

RUN_LDAY_SYNC = False             # 有券商定制版数据源才开
GTJA_LDAY_SRC = os.environ.get("TDX_GTJA_LDAY") or r"D:\gtja\tdx\vipdoc"
GTJA_LDAY_DST = os.environ.get("TDX_VIPDOC") or r"D:\jyrj\tdx\vipdoc"
LDAY_ONLY_MISSING = True          # 日常只补官方侧没有的文件(秒级); False=全量并集合并

RUN_KCACHE = True
KCACHE_CODES_FILE = ""            # 一行一个代码的池子文件; 空 = kcache 现有文件反推(推荐)
# =========================================================================


def _kcache_codes():
    """池子文件优先; 否则从缓存目录现有 .day 文件反推代码(sh600000.day -> 600000.SH)。"""
    if KCACHE_CODES_FILE:
        codes = [ln.strip() for ln in open(KCACHE_CODES_FILE, encoding="utf-8")
                 if ln.strip() and not ln.startswith("#")]
        return [c for c in codes if "." in c]
    out = []
    for p in sorted(Path(kcache.default_dir()).glob("*.day")):
        mkt, num = p.stem[:2], p.stem[2:]
        out.append(f"{num}.{mkt.upper()}")
    return out


def step_minutes():
    """vipdoc 分钟 -> 归档目录, 返回 {period: (新增根数, vip缺文件数)}。"""
    out = {}
    for period in MINUTE_PERIODS:
        targets = amv.all_codes(VIPDOC, period) if MINUTE_ALL else MINUTE_CODES
        bars = amv.PERIOD_META[period]["bars"]
        added = missing = 0
        for code in targets:
            vip = amv.vip_path(VIPDOC, code, period)
            if not vip.exists():
                missing += 1
            else:
                added += amv.append_new(vip, amv.arc_path(code, period), bars)
        out[period] = (added, missing, len(targets))
    return out


def step_lday_sync():
    """券商 lday -> 官方客户端各市场 lday 目录, 返回 {市场: sync_lday 报告}。"""
    out = {}
    for mkt in ("sh", "sz", "bj"):
        for cand in (Path(GTJA_LDAY_SRC) / mkt / "lday",
                     Path(GTJA_LDAY_SRC) / "vipdoc" / mkt / "lday"):
            if cand.is_dir():
                dst = Path(GTJA_LDAY_DST) / mkt / "lday"
                dst.mkdir(parents=True, exist_ok=True)
                out[mkt] = lday.sync_lday(str(cand), str(dst),
                                          only_missing=LDAY_ONLY_MISSING)
                break
    return out


def step_kcache():
    """TQ 日K -> kcache 增量, 返回汇总 {codes, added, updated, missing, elapsed}。"""
    codes = _kcache_codes()
    if not codes:
        return {"codes": 0, "added": 0, "updated": 0, "missing": 0}
    tq = TqClient()
    t0 = time.time()
    stats = kcache.update(tq, codes, incremental=True)
    el = time.time() - t0
    return {"codes": len(codes),
            "added": sum(s["added"] for c, s in stats.items() if c != "_missing"),
            "updated": sum(s["updated"] for c, s in stats.items() if c != "_missing"),
            "missing": len(stats.get("_missing") or {}),
            "elapsed": el}


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    args = sys.argv[1:]
    run_min, run_lday, run_kc = RUN_MINUTES, RUN_LDAY_SYNC, RUN_KCACHE
    if "--no-minutes" in args:
        run_min = False
    if "--no-kcache" in args:
        run_kc = False
    if "--only-kcache" in args:
        run_min = run_lday = False
    if "--only-minutes" in args:
        run_lday = run_kc = False

    results = []                                   # (步骤, ok, 秒, 详情)
    if run_min:
        t0 = time.time()
        try:
            detail = " | ".join(f"{p}: +{a}根(缺{m}/{n})"
                                for p, (a, m, n) in step_minutes().items())
            results.append(("分钟归档", True, time.time() - t0, detail))
        except (OSError, KeyError, ValueError) as e:
            results.append(("分钟归档", False, time.time() - t0, f"{type(e).__name__}: {e}"))
    if run_lday:
        t0 = time.time()
        try:
            rep = step_lday_sync()
            detail = " | ".join(f"{m}: 新复制{r['copied']} 合并{r['merged']}"
                                for m, r in rep.items()) or "未找到券商 lday 目录"
            results.append(("lday合并", bool(rep), time.time() - t0, detail))
        except OSError as e:
            results.append(("lday合并", False, time.time() - t0, str(e)))
    if run_kc:
        t0 = time.time()
        try:
            s = step_kcache()
            results.append(("日K增量", True, time.time() - t0,
                            f"{s['codes']}只 +{s['added']} 新 {s['updated']} 修订 "
                            f"缺数据{s['missing']}"
                            + (f" {s['elapsed']:.1f}s" if s.get("elapsed") else "")))
        except TqError as e:
            results.append(("日K增量", False, time.time() - t0,
                            f"TQ 不可用: {e.action_hint if hasattr(e, 'action_hint') else e}"))

    print("=" * 62)
    print("盘后一条龙汇总")
    print("-" * 62)
    failed = 0
    for name, ok, el, detail in results:
        flag = "OK  " if ok else "FAIL"
        failed += 0 if ok else 1
        print(f"[{flag}] {name}  {el:>5.1f}s  {detail}")
    if not results:
        print("(所有步骤均被开关关闭)")
    print("=" * 62)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
