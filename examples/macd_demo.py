# -*- coding: utf-8 -*-
"""示例: 从 TQ 本地服务取K线, 用 Python 自算 MACD(12,26,9)。

为什么不算公式引擎: 公式计算通路(formula_*)在 HTTP 模式下实测不生效,
指标一律 Python 自算 —— 详见 docs/LOCAL_NOTES.md。

用法: python examples/macd_demo.py [代码, 默认 600000.SH]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tdx_local import TqClient, TqError  # noqa: E402
from tdx_local.indicators import macd, macd_state  # noqa: E402


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

    dif, dea, hist = macd(closes)
    print(f"{'日期':<10}{'收盘':>8}{'DIF':>9}{'DEA':>9}{'MACD柱':>9}")
    for i in range(len(closes) - 5, len(closes)):
        print(f"{dates[i]:<10}{closes[i]:>8.2f}{dif[i]:>9.3f}{dea[i]:>9.3f}{hist[i]:>9.3f}")

    print("当前状态:", macd_state(closes))


if __name__ == "__main__":
    try:
        main()
    except TqError as e:
        print(f"\n[出错] {e}")
        print("请确认通达信金融终端已启动并登录(TQ 服务 http://127.0.0.1:17709/),"
              "环境要求见 README『快速开始』。")
        sys.exit(1)
