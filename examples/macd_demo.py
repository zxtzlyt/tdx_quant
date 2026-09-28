# -*- coding: utf-8 -*-
"""示例: 从 TQ 本地服务取K线, 用 Python 自算 MACD(12,26,9)。

为什么不算公式引擎: 公式计算通路(formula_*)在 HTTP 模式下实测不生效,
指标一律 Python 自算 —— 详见 docs/LOCAL_NOTES.md。

用法: python examples/macd_demo.py [代码, 默认 600000.SH]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tdx_local import TqClient  # noqa: E402


def ema(values, n):
    k = 2 / (n + 1)
    out = [values[0]]
    for v in values[1:]:
        out.append(v * k + out[-1] * (1 - k))
    return out


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    code = sys.argv[1] if len(sys.argv) > 1 else "600000.SH"
    tq = TqClient()

    names = tq.match(code.split(".")[0])
    if names:
        print(f"名称解析: {names[0].get('Name')} -> {names[0].get('Code')}")

    r = tq.market_data([code], count=120, period="1d", dividend_type="front")
    val = r["Value"][code]
    closes = [float(x) for x in val["Close"]]
    dates = val["Date"]
    print(f"{code} 本地取到 {len(closes)} 根日K, MACD(12,26,9):")

    dif = [a - b for a, b in zip(ema(closes, 12), ema(closes, 26))]
    dea = ema(dif, 9)
    hist = [(d - f) * 2 for d, f in zip(dif, dea)]
    print(f"{'日期':<10}{'收盘':>8}{'DIF':>9}{'DEA':>9}{'MACD柱':>9}")
    for i in range(len(closes) - 5, len(closes)):
        print(f"{dates[i]:<10}{closes[i]:>8.2f}{dif[i]:>9.3f}{dea[i]:>9.3f}{hist[i]:>9.3f}")

    if dif[-1] > dea[-1] and dif[-2] <= dea[-2]:
        state = "金叉"
    elif dif[-1] < dea[-1] and dif[-2] >= dea[-2]:
        state = "死叉"
    else:
        state = "多头" if dif[-1] > dea[-1] else "空头"
    print("当前状态:", state)


if __name__ == "__main__":
    main()
