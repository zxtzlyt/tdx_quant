# -*- coding: utf-8 -*-
"""配方2: 基本面选股 —— 用最新财报的业绩增速筛股票。

数据通路: TQ HTTP 专业财务通道(get_financial_data)。
关键坑: table_list 必须等于 field_list, 否则返回全空 —— 本脚本已按正确姿势传参。

口径说明: FN 系列是**累计值**(三季报=前三个季度合计), 累计值与去年同期累计值
直接相除就是同比, 口径天然可比。增速 = 最新报告期 / 去年同期 - 1。

用法: python examples/pick_fundamental.py
"""
import csv
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tdx_local import TqClient, TqError  # noqa: E402

# ============================ 参数区(按需修改) ============================
UNIVERSE_LIST_TYPE = "23"   # 候选池: "23"=沪深300(快) / "50"=沪深A股(全市场, 慢)
FIELDS = {                  # 用到的 FN 字段(含义见 docs/tdx-quant-docs/03-tqcenter-财务)
    "FN74": "营业收入(元)",
    "FN96": "归母净利润(元)",
}
PROFIT_YOY_MIN = 10.0       # 归母净利润同比% 下限
REVENUE_YOY_MIN = 0.0       # 营业收入同比% 下限
PROFIT_MIN = 0.0            # 最新归母净利润(元) 下限(>0 排除亏损股)
COUNT = 50                  # 最多列出前 N 只(按净利润同比从高到低)
WRITE_CSV = False           # True = 结果追加进 CSV(带日期戳), 便于长期跟踪每次选股
CSV_DIR = os.environ.get("TDX_PICKS_CSV_DIR",
                         str(Path(__file__).resolve().parent.parent / "picks_csv"))
# ========================================================================


def pick_two_periods(dates, values):
    """从报告期序列里取出(最新报告期值, 去年同期值)。

    dates 为 YYYYMMDD 报告期列表, values 平行数组(累计口径)。
    HTTP 通道的 FN 值是字符串, 这里统一转 float(转不了的丢弃)。
    去年同期 = 报告期月份日期相同、年份小 1 的那一期(无则 None)。
    """
    pairs = []
    for d, v in zip(dates, values):
        try:
            pairs.append((int(d), float(v)))
        except (TypeError, ValueError):
            continue
    if not pairs:
        return None, None
    pairs.sort()
    latest_d, latest_v = pairs[-1]
    prev_v = next((v for d, v in pairs if d == latest_d - 10000), None)
    return latest_v, prev_v


def yoy_pct(now, prev):
    """同比增速%; 上期为 0/负值时返回 None(负基数同比无意义)。"""
    if now is None or prev is None or prev <= 0:
        return None
    return (now / prev - 1) * 100


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    tq = TqClient()

    rows = tq.call("get_stock_list", market=UNIVERSE_LIST_TYPE,
                   list_type=1).get("Value") or []
    universe = {r["Code"]: r["Name"] for r in rows if r.get("Code")}
    if not universe:
        print("候选池为空 —— 请检查 UNIVERSE_LIST_TYPE 或本地数据")
        return
    print(f"候选池共 {len(universe)} 只, 拉取财报(FN: {'/'.join(FIELDS)})...")

    start_y = f"{date.today().year - 3}0101"
    end_y = f"{date.today().year}1231"
    hits, missing = [], {}
    codes = sorted(universe)
    for i in range(0, len(codes), 400):     # 财务接口按 400 只一批
        batch = codes[i:i + 400]
        r = tq.paged("get_financial_data", stock_list=batch,
                     field_list=list(FIELDS), table_list=list(FIELDS),
                     report_type="tag_time",
                     start_time=start_y, end_time=end_y)
        missing.update({c: "无财报" for c in batch
                        if c not in (r.get("Value") or {})})
        for code, per in (r.get("Value") or {}).items():
            tag_dates = per.get("tag_time") or []
            profit_now, profit_prev = pick_two_periods(
                tag_dates, per.get("FN96") or [])
            rev_now, rev_prev = pick_two_periods(
                tag_dates, per.get("FN74") or [])
            p_yoy = yoy_pct(profit_now, profit_prev)
            r_yoy = yoy_pct(rev_now, rev_prev)
            if profit_now is None or profit_now <= PROFIT_MIN:
                continue
            if p_yoy is None or p_yoy < PROFIT_YOY_MIN:
                continue
            if r_yoy is None or r_yoy < REVENUE_YOY_MIN:
                continue
            hits.append((code, universe.get(code, ""), profit_now, p_yoy, r_yoy))

    hits.sort(key=lambda x: -x[3])
    print(f"\n筛出 {len(hits)} 只(前 {COUNT} 只, 按归母净利润同比降序):")
    print(f"{'代码':<10}{'名称':<8}{'最新归母净利(亿)':>14}{'净利同比%':>10}{'营收同比%':>10}")
    for code, name, profit, p_yoy, r_yoy in hits[:COUNT]:
        print(f"{code:<10}{name:<8}{profit / 1e8:>14.2f}{p_yoy:>10.1f}{r_yoy:>10.1f}")
    if missing:
        print(f"\n[提示] {len(missing)} 只本地无财报数据被跳过")

    # ---- 结果落盘(可选): 每次运行追加一段带日期的行, 长期跟踪选股历史 ----
    if WRITE_CSV and hits:
        path = Path(CSV_DIR) / "pick_fundamental.csv"
        path.parent.mkdir(parents=True, exist_ok=True)
        is_new = not path.exists()
        with open(path, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if is_new:
                w.writerow(["run_date", "code", "name", "profit_yi",
                            "profit_yoy_pct", "rev_yoy_pct"])
            today = date.today().strftime("%Y%m%d")
            w.writerows([today, c, n, f"{p / 1e8:.2f}", f"{py:.1f}", f"{ry:.1f}"]
                        for c, n, p, py, ry in hits[:COUNT])
        print(f"结果已追加 -> {path}")


if __name__ == "__main__":
    try:
        main()
    except TqError as e:
        print(f"\n[出错] {e}")
        print("请确认通达信金融终端已启动并登录(TQ 服务 http://127.0.0.1:17709/),"
              "环境要求见 README『快速开始』。")
        sys.exit(1)
