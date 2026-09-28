<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hho9u0cbfe60/order.html | 章节: 10-lambda-pylambda/02-全局运行对象 -->
# Order对象

###  Order对象

**获取示例策略**

```python
def init(context):
    context.stock = ["000001.SZ"]
    context.oid = None

def handle_bar(context, bar_dict):
    if not context.oid:
        context.oid = order_target_value("000001.SZ", 10000)

    order = get_order(context.oid)
    if order:
        try:
            log.info("order_id    : %s", order.order_id)
        except Exception as e:
            log.info("order_id    : ERR=%s", str(e))

        try:
            log.info("symbol      : %s", order.symbol)
        except Exception as e:
            log.info("symbol      : ERR=%s", str(e))

        try:
            log.info("amount      : %s", order.amount)
        except Exception as e:
            log.info("amount      : ERR=%s", str(e))

        try:
            log.info("price       : %s", order.price)
        except Exception as e:
            log.info("price       : ERR=%s", str(e))

        try:
            log.info("filled      : %s", order.filled)
        except Exception as e:
            log.info("filled      : ERR=%s", str(e))

        try:
            log.info("status      : %s", order.status)
        except Exception as e:
            log.info("status      : ERR=%s", str(e))

        try:
            log.info("side        : %s", order.side)
        except Exception as e:
            log.info("side        : ERR=%s", str(e))

        try:
            log.info("datetime    : %s", order.datetime)
        except Exception as e:
            log.info("datetime    : ERR=%s", str(e))

        try:
            log.info("filled_dt   : %s", order.filled_dt)
        except Exception as e:
            log.info("filled_dt   : ERR=%s", str(e))

        try:
            log.info("avg_price   : %s", order.avg_price)
        except Exception as e:
            log.info("avg_price   : ERR=%s", str(e))

        try:
            log.info("message     : %s", order.message)
        except Exception as e:
            log.info("message     : ERR=%s", str(e))

        try:
            log.info("cancelable  : %s", order.cancelable)
        except Exception as e:
            log.info("cancelable  : ERR=%s", str(e))
```

**日志输出**

```python
08-17 15:53:51
INFO
提交回测任务
08-17 15:53:51
INFO
回测任务状态：queued
08-17 15:53:51
INFO
回测任务状态：running
08-17 15:53:54
INFO
回测任务状态：succeeded
08-17 15:53:54
INFO
Order(order_id='L00000001', symbol='000001.SZ', amount=800.0, price=11.260000228881836, filled=0.0, remaining_amount=800.0, status='pending', side='buy', datetime=datetime.datetime(2026, 8, 11, 0, 0), submitted_dt=datetime.datetime(2026, 8, 11, 0, 0), updated_dt=datetime.datetime(2026, 8, 11, 0, 0), filled_dt=None, avg_price=None, order_type='market', limit_price=None, expire_bars=None, delay_bars=1, active_bars=0, message='委托数量已按板块规则调整为 800', raw=None)
08-17 15:53:54
INFO
2026-08-17 15:53:52,106 INFO order_id : L00000001
08-17 15:53:54
INFO
2026-08-17 15:53:52,107 INFO symbol : 000001.SZ
08-17 15:53:54
INFO
2026-08-17 15:53:52,107 INFO amount : 800.0
08-17 15:53:54
INFO
2026-08-17 15:53:52,107 INFO price : 11.260000228881836
08-17 15:53:54
INFO
2026-08-17 15:53:52,107 INFO filled : 0.0
08-17 15:53:54
INFO
2026-08-17 15:53:52,107 INFO status : pending
08-17 15:53:54
INFO
2026-08-17 15:53:52,107 INFO side : buy
08-17 15:53:54
INFO
2026-08-17 15:53:52,107 INFO datetime : 2026-08-11 00:00:00
08-17 15:53:54
INFO
2026-08-17 15:53:52,107 INFO filled_dt : None
08-17 15:53:54
INFO
2026-08-17 15:53:52,107 INFO avg_price : None
08-17 15:53:54
INFO
2026-08-17 15:53:52,107 INFO message : 委托数量已按板块规则调整为 800
08-17 15:53:54
INFO
2026-08-17 15:53:52,107 INFO cancelable : True
08-17 15:53:54
INFO
2026-08-17 15:53:52,108 INFO order_id : L00000001
08-17 15:53:54
INFO
2026-08-17 15:53:52,108 INFO symbol : 000001.SZ
08-17 15:53:54
INFO
2026-08-17 15:53:52,108 INFO amount : 800.0
08-17 15:53:54
INFO
2026-08-17 15:53:52,108 INFO price : 11.260000228881836
08-17 15:53:54
INFO
2026-08-17 15:53:52,108 INFO filled : 800.0
08-17 15:53:54
INFO
2026-08-17 15:53:52,108 INFO status : filled
08-17 15:53:54
INFO
2026-08-17 15:53:52,108 INFO side : buy
08-17 15:53:54
INFO
2026-08-17 15:53:52,108 INFO datetime : 2026-08-11 00:00:00
08-17 15:53:54
INFO
2026-08-17 15:53:52,108 INFO filled_dt : 2026-08-12 00:00:00
08-17 15:53:54
INFO
2026-08-17 15:53:52,108 INFO avg_price : 11.260000228881836
08-17 15:53:54
INFO
2026-08-17 15:53:52,108 INFO message :
08-17 15:53:54
INFO
2026-08-17 15:53:52,108 INFO cancelable : False
08-17 15:53:54
INFO
回测任务结束：succeeded
```
