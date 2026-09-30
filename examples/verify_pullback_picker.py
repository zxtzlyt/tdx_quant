# -*- coding: utf-8 -*-
"""DLL 选股器交叉验证 —— 用 Python 同口径复算"缩量回踩MA支撑"，对账插件选股结果。

用法(三步):
  1. 通达信 公式菜单 → 插件选股 → 选"缩量回踩MA支撑"(参数保持默认) → 执行选股
  2. 点"选股入板块", 保存到自定义板块(简称用英文, 如 HJ)
  3. 本脚本把 BLOCK_CODE 改成那个简称后运行:
       python examples/verify_pullback_picker.py HJ
     输出 DLL 与 Python 双方判定的一致性对账表。

判定口径(与 dll/src/MyPicker/MyPicker.cpp 完全一致):
  MA(20)较5天前上行; 今日量<=前5日均量*60%; 收盘价在MA20的±2%内。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tdx_local import TqClient  # noqa: E402

# ============ 参数区(与插件界面填的参数保持一致) ============
TOL_PCT = 2.0      # 回踩幅度%
VOL_PCT = 60.0     # 缩量至%
MA_N = 20          # 均线天数
SLOPE_N = 5        # 上行回看天数
BARS = 80          # 取K线根数(需 > MA_N + SLOPE_N + 6)
# ==========================================================


def judge(closes, vols, tol_pct=TOL_PCT, vol_pct=VOL_PCT, ma_n=MA_N, slope_n=SLOPE_N):
    """与 MyPicker.cpp 的 JudgeLast 同口径: 对最后一张K线判定。"""
    n = len(closes)
    if n < ma_n + slope_n + 6:
        return False, "数据不足"
    close = closes[-1]
    if close <= 0:
        return False, "价格无效"
    ma_now = sum(closes[-ma_n:]) / ma_n
    ma_before = sum(closes[-slope_n - ma_n:-slope_n]) / ma_n
    if ma_now <= ma_before:
        return False, "MA未上行"
    if abs(close / ma_now - 1.0) > tol_pct / 100.0:
        return False, f"偏离MA {abs(close / ma_now - 1.0) * 100:.1f}%"
    v_avg = sum(vols[-6:-1]) / 5.0
    if v_avg <= 0:
        return False, "量数据无效"
    if vols[-1] > v_avg * vol_pct / 100.0:
        return False, f"未缩量(今日{vols[-1] / v_avg * 100:.0f}%均量)"
    return True, "符合"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    block = sys.argv[1].upper() if len(sys.argv) > 1 else "HJ"
    tq = TqClient()

    rows = tq.call("get_stock_list_in_sector", block_code=block, block_type=1,
                   list_type=1).get("Value") or []
    stocks = {r["Code"]: r["Name"] for r in rows if r.get("Code")}
    if not stocks:
        print(f"板块[{block}]为空或不存在 —— 先在插件选股里'选股入板块'")
        return
    print(f"板块[{block}] 共 {len(stocks)} 只(DLL 选股结果), Python 复算对账:")

    agree, conflict, skipped = 0, 0, 0
    codes = sorted(stocks)
    for i in range(0, len(codes), 150):
        batch = codes[i:i + 150]
        r = tq.market_data(batch, count=BARS, period="1d", dividend_type="none",
                           field_list=["Date", "Close", "Volume"])
        for code in batch:
            val = (r.get("Value") or {}).get(code) or {}
            closes = [float(x) for x in val.get("Close") or []]
            vols = [float(x) for x in val.get("Volume") or []]
            if len(closes) < BARS - 5:                    # 本地K线不足, 无法复算
                skipped += 1
                print(f"  [跳过] {code:<10}{stocks[code]:<8}本地K线不足")
                continue
            ok, why = judge(closes, vols)
            if ok:
                agree += 1
                print(f"  [一致√] {code:<10}{stocks[code]:<8}Python 同样判定符合")
            else:
                conflict += 1
                print(f"  [不一致] {code:<10}{stocks[code]:<8}Python 判定: {why}")

    print(f"\n对账结果: 一致 {agree} / 不一致 {conflict} / 无法复算 {skipped}")
    if conflict == 0 and skipped == 0:
        print("DLL 与 Python 完全一致 —— 插件判定逻辑验证通过。")
    elif conflict:
        print("存在不一致 —— 检查: ①插件参数与本脚本参数区是否一致 "
              "②执行选股时用的是日线 ③选股入板块后有没有再跑新数据")


if __name__ == "__main__":
    main()
