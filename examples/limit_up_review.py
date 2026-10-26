# -*- coding: utf-8 -*-
"""涨停/连板复盘配方 —— 从 kcache 读全池日线, 输出某日涨停梯队/炸板/跌停报告。

数据依赖: kcache 日线缓存(先跑 daily_pipeline 或 kcache.update 建缓存;
池子不够大时涨停统计只反映池内 —— 全市场复盘请先用 pick/板块代码把
缓存建满, 或把 CODES 指向全市场清单)。

用法: python examples/limit_up_review.py               # 参数区日期与池子
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tdx_local import kcache, limits

# ============================ 参数区(按需修改) ============================
DATE = 20261024          # 复盘日(YYYYMMDD; kcache 里须有该日及其前一根)
ST_BY_CODE = {}          # {code: True} 标记 ST(主板按 5% 算); 默认全按非 ST
# 池子: 空 = kcache 目录全部代码
CODES = []
# =========================================================================


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    cache_dir = kcache.default_dir()
    codes = CODES
    if not codes:
        codes = [f"{p.stem[2:]}.{p.stem[:2].upper()}"
                 for p in sorted(Path(cache_dir).glob("*.day"))]
    if not codes:
        print("kcache 为空: 先跑 examples/daily_pipeline.py 或 kcache.update 建缓存")
        return
    bars = kcache.read_many(cache_dir, codes)
    has_date = {c: b for c, b in bars.items()
                if int(str(DATE)) in [int(str(d)) for d in b["Date"]]}
    if not has_date:
        print(f"kcache 里没有 {DATE} 的K线: 先把缓存增量到该日")
        return
    rep = limits.review(has_date, DATE, ST_BY_CODE)
    print(limits.report(rep))
    if rep["limit_up"]:
        print("\n涨停名单:", ",".join(rep["limit_up"]))


if __name__ == "__main__":
    main()
