<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hho9u0cbfe60/position.html | 章节: 10-lambda-pylambda/02-全局运行对象 -->
# positions对象

###  `context.portfolio.positions` 持仓对象

**获取示例策略**

```python
def init(context):
    set_execution("close")
    # 设置股票池
    context.stock = ["000001.SZ", "600000.SH"]
    # 标记只下单一次
    context.traded = False

def handle_bar(context, bar_dict):
    # 第一根bar执行一次买入，生成持仓position
    if not context.traded:
        order_target_value("000001.SZ", 10000)
        context.traded = True

    port = context.portfolio

    for sym in context.universe:
        pos = port.positions.get(sym)
        log.info("===== Symbol: %s Position输出 =====", sym)
        if pos is None:
            log.info("%s 无持仓，pos = None", sym)
            continue

        # 全部公开属性逐个打印
        log.info("symbol           : %s", pos.symbol)
        log.info("amount           : %s", pos.amount)
        log.info("available_amount : %s", pos.available_amount)
        log.info("closeable_amount: %s", pos.closeable_amount)
        log.info("cost_basis       : %s", pos.cost_basis)
        log.info("avg_cost         : %s", pos.avg_cost)
        log.info("last_price       : %s", pos.last_price)
        log.info("market_value     : %s", pos.market_value)
        log.info("pnl              : %s", pos.pnl)
```

**日志输出**

```python
08-17 15:50:11
INFO
提交回测任务
08-17 15:50:11
INFO
回测任务状态：queued
08-17 15:50:11
INFO
回测任务状态：running
08-17 15:50:14
INFO
回测任务状态：succeeded
08-17 15:50:14
INFO
2026-08-17 15:50:12,343 INFO ===== Symbol: 000001.SZ Position输出 =====
08-17 15:50:14
INFO
2026-08-17 15:50:12,343 INFO symbol : 000001.SZ
08-17 15:50:14
INFO
2026-08-17 15:50:12,343 INFO amount : 800.0
08-17 15:50:14
INFO
2026-08-17 15:50:12,343 INFO available_amount : 0.0
08-17 15:50:14
INFO
2026-08-17 15:50:12,343 INFO closeable_amount: 0.0
08-17 15:50:14
INFO
2026-08-17 15:50:12,343 INFO cost_basis : 11.2663625
08-17 15:50:14
INFO
2026-08-17 15:50:12,343 INFO avg_cost : 11.2663625
08-17 15:50:14
INFO
2026-08-17 15:50:12,343 INFO last_price : 11.260000228881836
08-17 15:50:14
INFO
2026-08-17 15:50:12,343 INFO market_value : 9008.000183105469
08-17 15:50:14
INFO
2026-08-17 15:50:12,343 INFO pnl : -5.0898168945313955
08-17 15:50:14
INFO
2026-08-17 15:50:12,343 INFO ===== Symbol: 600000.SH Position输出 =====
08-17 15:50:14
INFO
2026-08-17 15:50:12,343 INFO 600000.SH 无持仓，pos = None
08-17 15:50:14
INFO
2026-08-17 15:50:12,345 INFO ===== Symbol: 000001.SZ Position输出 =====
08-17 15:50:14
INFO
2026-08-17 15:50:12,345 INFO symbol : 000001.SZ
08-17 15:50:14
INFO
2026-08-17 15:50:12,345 INFO amount : 800.0
08-17 15:50:14
INFO
2026-08-17 15:50:12,345 INFO available_amount : 800.0
08-17 15:50:14
INFO
2026-08-17 15:50:12,345 INFO closeable_amount: 800.0
08-17 15:50:14
INFO
2026-08-17 15:50:12,345 INFO cost_basis : 11.2663625
08-17 15:50:14
INFO
2026-08-17 15:50:12,345 INFO avg_cost : 11.2663625
08-17 15:50:14
INFO
2026-08-17 15:50:12,345 INFO last_price : 11.25
08-17 15:50:14
INFO
2026-08-17 15:50:12,345 INFO market_value : 9000.0
08-17 15:50:14
INFO
2026-08-17 15:50:12,345 INFO pnl : -13.090000000000146
08-17 15:50:14
INFO
2026-08-17 15:50:12,345 INFO ===== Symbol: 600000.SH Position输出 =====
08-17 15:50:14
INFO
2026-08-17 15:50:12,345 INFO 600000.SH 无持仓，pos = None
08-17 15:50:14
INFO
回测任务结束：succeeded
```
