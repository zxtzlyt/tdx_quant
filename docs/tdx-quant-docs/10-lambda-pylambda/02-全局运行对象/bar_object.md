<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hho9u0cbfe60/bar.html | 章节: 10-lambda-pylambda/02-全局运行对象 -->
# Bar对象

###  `context.bar`Bar对象

**获取示例策略**

```python
def init(context):
    context.stock = ["000001.SZ"]

def handle_bar(context, bar_dict):
    bar = bar_dict["000001.SZ"]
    log.info("symbol     : %s", bar.symbol)
    log.info("datetime   : %s", bar.datetime)
    log.info("open       : %s", bar.open)
    log.info("high       : %s", bar.high)
    log.info("low        : %s", bar.low)
    log.info("close      : %s", bar.close)
    log.info("volume     : %s", bar.volume)
    log.info("amount     : %s", bar.amount)
    log.info("money      : %s", bar.money)
    log.info("high_limit : %s", bar.high_limit)
    log.info("low_limit  : %s", bar.low_limit)
    log.info("paused     : %s", bar.paused)
    log.info("is_paused  : %s", bar.is_paused)
```

**日志输出**

```python
08-17 15:51:31
INFO
提交回测任务
08-17 15:51:31
INFO
回测任务状态：queued
08-17 15:51:31
INFO
回测任务状态：running
08-17 15:51:34
INFO
回测任务状态：succeeded
08-17 15:51:34
INFO
2026-08-17 15:51:32,208 INFO symbol : 000001.SZ
08-17 15:51:34
INFO
2026-08-17 15:51:32,208 INFO datetime : 2026-08-12 00:00:00
08-17 15:51:34
INFO
2026-08-17 15:51:32,208 INFO open : 11.260000228881836
08-17 15:51:34
INFO
2026-08-17 15:51:32,208 INFO high : 11.289999961853027
08-17 15:51:34
INFO
2026-08-17 15:51:32,208 INFO low : 11.199999809265137
08-17 15:51:34
INFO
2026-08-17 15:51:32,208 INFO close : 11.25
08-17 15:51:34
INFO
2026-08-17 15:51:32,209 INFO volume : 63295024.0
08-17 15:51:34
INFO
2026-08-17 15:51:32,209 INFO amount : 711612864.0
08-17 15:51:34
INFO
2026-08-17 15:51:32,209 INFO money : 711612864.0
08-17 15:51:34
INFO
2026-08-17 15:51:32,209 INFO high_limit : None
08-17 15:51:34
INFO
2026-08-17 15:51:32,209 INFO low_limit : None
08-17 15:51:34
INFO
2026-08-17 15:51:32,209 INFO paused : False
08-17 15:51:34
INFO
2026-08-17 15:51:32,209 INFO is_paused : False
08-17 15:51:34
INFO
回测任务结束：succeeded
```
