# -*- coding: utf-8 -*-
"""盘中盯盘器 —— snapshot_batch 轮询关注池, 价格/涨速阈值触发提示。

零依赖(提示音用 Windows winsound), 只读不下单。触发条件按代码配置:
价格上下限(high/low)、相对本轮基准价的涨速(speed_pct, 按轮询周期)。
触发时终端打印 + 蜂鸣(BEEP 可关); Ctrl+C 退出。

用法: 盘中跑 python examples/watchtower.py, 每轮间隔 POLL 秒。
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tdx_local import TqClient, TqError

# ============================ 参数区(按需修改) ============================
WATCH = {
    "600000.SH": {"high": 13.0, "low": 11.5},
    "600519.SH": {"speed_pct": 1.0},        # 相对首轮快照价变动超 1% 提示
}
POLL = 5.0          # 轮询间隔秒(盘中别低于 3s, 快照接口按轮询拉全量)
BEEP = True         # 触发提示音(winsound, 仅 Windows)
MAX_ROUNDS = 0      # 调试用轮数上限; 0 = 一直轮询
# =========================================================================


def check_one(code, rule, snap, baseline) -> list:
    """单只单轮检查 -> [触发描述]; snap 为空(停牌/无数据)返回 []。"""
    out = []
    price = snap.get("price")
    if not price:
        return out
    if rule.get("high") and price >= rule["high"]:
        out.append(f"≥上限 {rule['high']}")
    if rule.get("low") and price <= rule["low"]:
        out.append(f"≤下限 {rule['low']}")
    speed = rule.get("speed_pct")
    if speed and baseline:
        chg = (price / baseline - 1) * 100
        if abs(chg) >= speed:
            out.append(f"涨速 {chg:+.2f}% ≥ {speed}%")
    return out


def poll_round(tq, watch, baselines, beep=True) -> int:
    """一轮批量快照 + 阈值检查 -> 触发条数; 更新 baselines。"""
    snaps = tq.snapshot_batch(list(watch))
    n_hit = 0
    for code, snap in snaps.items():
        if not isinstance(snap, dict):
            continue
        price = snap.get("Now")                      # 标准版快照现价字段(2026-10-27 实测)
        try:
            price = float(price)
        except (TypeError, ValueError):
            continue                                 # 停牌/无行情
        hits = check_one(code, watch.get(code, {}), {"price": price},
                         baselines.get(code))
        if hits:
            n_hit += len(hits)
            stamp = time.strftime("%H:%M:%S")
            line = f"[{stamp}] {code} {price:.2f}: " + "; ".join(hits)
            print(line, flush=True)
            if beep:
                try:
                    import winsound
                    winsound.Beep(1200, 200)
                except (ImportError, RuntimeError):
                    pass
        baselines.setdefault(code, price)
    return n_hit


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    tq = TqClient()
    baselines = {}
    print(f"盯盘启动: {len(WATCH)} 只, 间隔 {POLL}s, Ctrl+C 退出")
    rounds = 0
    while True:
        try:
            n = poll_round(tq, WATCH, baselines, BEEP)
            rounds += 1
            if rounds % 60 == 0:
                print(f"  …已轮询 {rounds} 轮, 触发累计见上")
            if MAX_ROUNDS and rounds >= MAX_ROUNDS:
                break
        except TqError as e:
            print(f"[TqError] {e} —— {POLL}s 后重试", flush=True)
        except KeyboardInterrupt:
            print("\n手动退出")
            return 0
        time.sleep(POLL)
    return 0


if __name__ == "__main__":
    sys.exit(main())
