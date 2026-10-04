# -*- coding: utf-8 -*-
"""回测配方: 用历史数据验证"金叉+多头排列"策略到底管不管用。

做法: 每隔 STEP 个交易日设一个调仓日 T, 策略只看截至 T 的K线选票
(构造上杜绝未来函数), 然后统计持有 5/20/60 日的分红再投回报, 与上证指数
对比超额。数据走 kcache 日线缓存(不复权原始价, point-in-time 保真)。

用法: python examples/backtest_picker.py
首次运行会先把候选池全历史拉进缓存(kcache/), 之后跑得很快。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tdx_local import TqClient, TqError, backtest, kcache  # noqa: E402
from tdx_local.indicators import is_bull_align, is_golden_cross  # noqa: E402

# ============================ 参数区(按需修改) ============================
SECTOR = "银行"           # 候选板块名; 改成 "" 则沪深A股全市场(首次建缓存很慢)
BENCHMARK = "999999.SH"   # 超额基准(上证指数)
LOOKBACK = 500            # 回看最近多少个交易日
STEP = 10                 # 每隔多少个交易日调仓一次
HORIZONS = (5, 20, 60)    # 前向持有期(交易日)
WANT_GOLDEN_CROSS = True  # 策略条件1: 金叉(与 pick_technical 同口径)
WANT_BULL_ALIGN = True    # 策略条件2: 均线多头排列
# ========================================================================


def make_strategy(universe):
    """把参数区开关包成 pick(asof_bars) -> [code] 纯函数。

    只用入参 asof(截至调仓日的切片) —— 闭包里除 universe(静态名单)外
    不引用任何实时数据, 这是防未来函数的前提。
    """
    def pick(asof):
        out = []
        for code in universe:
            closes = (asof.get(code) or {}).get("Close") or []
            if len(closes) < 21:                     # 不复权原始价上算指标
                continue
            if WANT_GOLDEN_CROSS and not is_golden_cross(closes):
                continue
            if WANT_BULL_ALIGN and not is_bull_align(closes):
                continue
            out.append(code)
        return out
    return pick


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    tq = TqClient()

    # ---- 1. 候选池(与 pick_technical 同源) ----
    if SECTOR:
        rows = tq.call("get_stock_list_in_sector", block_code=SECTOR,
                       list_type=1).get("Value") or []
        universe = {r["Code"]: r["Name"] for r in rows if r.get("Code")}
    else:
        rows = tq.call("get_stock_list", market="50", list_type=1).get("Value") or []
        universe = {r["Code"]: r["Name"] for r in rows if r.get("Code")}
    universe.pop(BENCHMARK, None)
    if not universe:
        print("候选池为空 —— 请检查板块名拼写或本地数据")
        return
    print(f"候选池 {len(universe)} 只, 基准 {BENCHMARK}; "
          f"回看 {LOOKBACK} 交易日, 每 {STEP} 日调仓")

    # ---- 2. 建缓存(首次全量, 之后秒级增量)并读出全历史 ----
    codes = sorted(universe) + [BENCHMARK]
    stats = kcache.update(tq, codes)
    n_new = sum(v["added"] for k, v in stats.items() if k != "_missing")
    print(f"缓存同步: 新增 {n_new} 根K线")

    cache_dir = kcache.default_dir()
    bars = kcache.read_many(cache_dir, codes)
    if BENCHMARK not in bars:
        print("[出错] 基准指数无本地数据, 无法定调仓日历")
        return
    missing = [c for c in codes if c not in bars]
    if missing:
        print(f"[提示] {len(missing)} 只无缓存数据, 不参与回测")

    # ---- 3. 调仓日 + 分红事件(收益口径: 不复权+分红再投) ----
    rebal = backtest.make_rebalances(bars[BENCHMARK]["Date"],
                                     last_n=LOOKBACK, step=STEP)
    print(f"调仓日 {len(rebal)} 个: {rebal[0]} ~ {rebal[-1]}")

    div_memo = {}

    def dividends_of(code):
        if code not in div_memo:
            try:
                div_memo[code] = tq.divid_factors(code)
            except TqError:
                div_memo[code] = {}
        return div_memo[code]

    # ---- 4. 重放 + 报告 ----
    result = backtest.run(bars, rebal, make_strategy(sorted(universe)),
                          horizons=HORIZONS, dividends_by_code=dividends_of,
                          benchmark=BENCHMARK)
    print()
    print(backtest.report(result))
    print("\n[口径] 原始不复权价上算指标与收益(见 LOCAL_NOTES: 前复权不能算"
          "收益; 当时的复权价无法复原), 与实盘前复权信号在除息日附近略有差异。")
    print("[提醒] 历史统计不代表未来, 本结果不构成投资建议。")


if __name__ == "__main__":
    try:
        main()
    except TqError as e:
        print(f"\n[出错] {e}")
        print("请确认通达信金融终端已启动并登录(TQ 服务 http://127.0.0.1:17709/),"
              "环境要求见 README『快速开始』。")
        sys.exit(1)
