# -*- coding: utf-8 -*-
"""配方1: 技术面选股 —— 均线金叉 / 多头排列 / 放量, 一个脚本全干完。

数据通路: TQ HTTP 取日线 -> Python 自算指标(公式引擎 HTTP 不可用, 指标一律自算)。
筛中的股票打印成表, 并可选写回通达信自定义板块(客户端里直接看)。

用法: python examples/pick_technical.py
把下面"参数区"里的板块名 / 开关改一改, 再跑一次就是新策略。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tdx_local import TqClient  # noqa: E402

# ============================ 参数区(按需修改) ============================
SECTOR = "银行"          # 候选板块名(通达信板块/行业名均可); 改成 "" 则用全部沪深A股(慢)
BARS = 60                # 取最近多少根日K(够算 20 日均线即可)
MA_FAST, MA_SLOW = 5, 10 # 金叉判定的两条均线
WANT_GOLDEN_CROSS = True # 只要"今天刚金叉"的
WANT_BULL_ALIGN = True   # 只要均线多头排列(MA5>MA10>MA20)
WANT_VOLUME_SURGE = False# 只要放量(今日量 > 5日均量的 1.5 倍)
VOLUME_RATIO = 1.5
COUNT = 120              # 最多列出前 N 只(按代码序)
SEND_TO_TDX = True       # True = 把结果写进通达信自定义板块 BLOCK_CODE
BLOCK_CODE = "JXG"       # 板块简称(必须英文: HTTP 通道写中文板块名会损坏客户端板块表)
BLOCK_NAME = "JXG"       # 板块名称(同样用英文; 可在客户端"自定义板块设置"里手动改名)
# ========================================================================


def sma(values, n):
    """简单均线序列: 前n-1个位置为 None。"""
    out, s = [], 0.0
    for i, v in enumerate(values):
        s += v
        if i >= n:
            s -= values[i - n]
        out.append(s / n if i >= n - 1 else None)
    return out


def is_golden_cross(closes, fast=MA_FAST, slow=MA_SLOW):
    """最后一根K线上, fast 均线上穿 slow 均线(今天>昨, 且昨天<=前)。"""
    ma_f, ma_s = sma(closes, fast), sma(closes, slow)
    a, b = len(closes) - 1, len(closes) - 2
    if min(ma_f[a], ma_s[a], ma_f[b], ma_s[b]) is None:
        return False
    return ma_f[a] > ma_s[a] and ma_f[b] <= ma_s[b]


def is_bull_align(closes, n1=5, n2=10, n3=20):
    """均线多头排列: MA5 > MA10 > MA20。"""
    if len(closes) < n3:
        return False
    m5, m10, m20 = sma(closes, n1)[-1], sma(closes, n2)[-1], sma(closes, n3)[-1]
    return None not in (m5, m10, m20) and m5 > m10 > m20


def is_volume_surge(volumes, ratio=VOLUME_RATIO, base=5):
    """今日成交量 > 前 base 日均量的 ratio 倍。"""
    if len(volumes) < base + 1:
        return False
    avg = sum(float(v) for v in volumes[-base - 1:-1]) / base
    return avg > 0 and float(volumes[-1]) > avg * ratio


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    tq = TqClient()

    # ---- 1. 候选池: 板块成份股, 或全部沪深A股 ----
    if SECTOR:
        rows = tq.call("get_stock_list_in_sector", block_code=SECTOR,
                       list_type=1).get("Value") or []
        universe = {r["Code"]: r["Name"] for r in rows if r.get("Code")}
        print(f"候选板块[{SECTOR}] 共 {len(universe)} 只")
    else:
        rows = tq.call("get_stock_list", market="50", list_type=1).get("Value") or []
        universe = {r["Code"]: r["Name"] for r in rows if r.get("Code")}
        print(f"候选=沪深A股 共 {len(universe)} 只(全市场模式较慢, 请耐心)")
    if not universe:
        print("候选池为空 —— 请检查板块名拼写或本地数据")
        return

    # ---- 2. 分批取日K(单次约 24000 行上限, 150只x120根稳妥) ----
    hits, missing = [], {}
    codes = sorted(universe)
    for i in range(0, len(codes), 150):
        batch = codes[i:i + 150]
        r = tq.market_data(batch, count=BARS, period="1d", dividend_type="front",
                           field_list=["Date", "Close", "Volume"])
        missing.update(r.get("_missing") or {})
        for code, val in (r.get("Value") or {}).items():
            closes = [float(x) for x in val.get("Close") or []]
            vols = val.get("Volume") or []
            if len(closes) < max(MA_SLOW + 2, 21):
                continue
            if WANT_GOLDEN_CROSS and not is_golden_cross(closes):
                continue
            if WANT_BULL_ALIGN and not is_bull_align(closes):
                continue
            if WANT_VOLUME_SURGE and not is_volume_surge(vols):
                continue
            chg = (closes[-1] / closes[-2] - 1) * 100 if closes[-2] else 0.0
            hits.append((code, universe.get(code, ""), closes[-1], chg))

    # ---- 3. 输出 ----
    print(f"\n筛出 {len(hits)} 只(前 {COUNT} 只):")
    print(f"{'代码':<10}{'名称':<8}{'现价':>8}{'今日%':>8}")
    for code, name, close, chg in hits[:COUNT]:
        print(f"{code:<10}{name:<8}{close:>8.2f}{chg:>+8.2f}")
    if missing:
        print(f"\n[提示] {len(missing)} 只无本地K线已跳过(可在客户端打开该股页面补数据)")

    # ---- 4. 写回通达信自定义板块(可选) ----
    if SEND_TO_TDX and hits:
        tq.call("create_sector", block_code=BLOCK_CODE, block_name=BLOCK_NAME)
        r = tq.call("send_user_block", block_code=BLOCK_CODE,
                    stock_list=[h[0] for h in hits])
        ok = r.get("ErrorId") == "0"
        print(f"\n已{'写入' if ok else '尝试写入'}通达信自定义板块[{BLOCK_CODE}]"
              f"(客户端自定义板块里查看): {r.get('Error') or r.get('ErrorId')}")


if __name__ == "__main__":
    main()
