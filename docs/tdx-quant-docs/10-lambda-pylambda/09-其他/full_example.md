<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hhodeob36hi4.html | 章节: 10-lambda-pylambda/09-其他 -->

#  完整示例

双均线策略：

```python
def init(context):
    context.stock = "000001.SZ"
    set_benchmark("000300.SH")
    set_commission(open_commission=0.0003, close_commission=0.0003, close_tax=0.001)
    run_daily(trade, time_rule="every_bar")

def trade(context, bar_dict):
    hist = attribute_history(context.stock, 20, "1d", ["close"])
    if len(hist) < 20:
        return

    close = hist["close"]
    ma5 = close.tail(5).mean()
    ma20 = close.tail(20).mean()
    price = bar_dict[context.stock].close

    has_position = context.stock in context.portfolio.positions

    if ma5 > ma20 and not has_position:
        order_value(context.stock, context.portfolio.available_cash)
        log.info("buy %s price=%s", context.stock, price)
    elif ma5 < ma20 and has_position:
        order_target(context.stock, 0)
        log.info("sell %s price=%s", context.stock, price)

    record(price=price, ma5=ma5, ma20=ma20)
```

因子轮动策略：

```python
FACTOR_IDS = ["momentum_20d", "volume_ratio"]
DEFAULT_INDEXES = ["000300.SH"]
TOP_N = 10
LOOKBACK = 320
REBALANCE_DAYS = 20
BENCHMARK = "000300.SH"

def _n(x):
    try:
        y = float(x)
        if y == y and abs(y) < 1e100:
            return y
    except Exception:
        pass
    return None

def _v(f, c):
    try:
        raw = f[c].tolist()
    except Exception:
        try:
            raw = list(f[c])
        except Exception:
            raw = []
    return [_n(x) for x in raw if _n(x) is not None]

def _ma(a, n):
    return sum(a[-n:]) / float(n) if len(a) >= n else None

def _ret(c, n):
    return c[-1] / c[-n - 1] - 1.0 if len(c) > n and c[-n - 1] else None

def _div(a, b):
    return None if a is None or b in (None, 0) else a / b

def _universe():
    r, s = [], set()
    for idx in DEFAULT_INDEXES:
        try:
            items = get_stock_list_in_sector(idx, block_type=0)
        except Exception:
            items = []
        for x in items or []:
            y = str(x)
            if y and y not in s:
                s.add(y)
                r.append(y)
    return r or ["000300.SH"]

def _calc(fid, c, v):
    if not c:
        return None
    if fid.startswith("momentum_") and fid.endswith("d"):
        return _ret(c, int(fid.split("_")[1][:-1]))
    if fid == "volume_ratio":
        return _div(v[-1] if v else None, _ma(v, 20))
    return None

def _rank(rows):
    for fid in FACTOR_IDS:
        vv = [x for x in rows if x.get(fid) is not None]
        vv.sort(key=lambda x: x.get(fid))
        n = len(vv)
        for i, x in enumerate(vv, 1):
            x[fid + "_rank"] = i / float(n)
    for x in rows:
        vals = [x.get(fid + "_rank") for fid in FACTOR_IDS if x.get(fid + "_rank") is not None]
        x["factor_score"] = sum(vals) / float(len(vals)) if vals else None

def init(context):
    context.rebalance_counter = 0
    context.current_targets = []
    context.stock = _universe()
    run_daily(check, time_rule="every_bar")
    set_benchmark(BENCHMARK)

def check(context, bar_dict):
    context.rebalance_counter += 1
    if context.rebalance_counter % REBALANCE_DAYS != 1:
        return

    universe = list(context.stock) if context.stock else _universe()
    if not universe:
        return

    data = get_bars_batch(universe, count=LOOKBACK, fields=["close", "volume"], frequency="1d")
    rows = []
    for sym, frame in data.items():
        c = _v(frame, "close")
        v = _v(frame, "volume")
        row = {"symbol": sym, "close": c[-1] if c else None}
        for fid in FACTOR_IDS:
            row[fid] = _calc(fid, c, v)
        rows.append(row)

    _rank(rows)
    rows.sort(key=lambda x: x.get("factor_score") if x.get("factor_score") is not None else -1e100, reverse=True)
    selected = [x.get("symbol") for x in rows[:TOP_N] if x.get("symbol")]
    w = 1.0 / float(len(selected)) if selected else 0.0

    # ── 先卖：不在新列表里的旧持仓 ──
    for old in context.current_targets:
        if old not in selected:
            order_target_percent(old, 0)
            log.info(f"【卖出】{old}")

    # ── 再买：新列表 ──
    for sym in selected:
        order_target_percent(sym, w)
        log.info(f"【买入】{sym} 目标权重={w:.2%}")

    context.current_targets = selected

def after_trading(context):
    log.info("盘后运行结束")
```
