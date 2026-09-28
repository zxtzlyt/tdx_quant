<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hibf3lo5qk7g/mindoc-1hibf4cf978ng.html | 章节: 10-lambda-pylambda/04-定时任务 -->
# 每日定时run_daily

###  每日定时运行函数

```python
run_daily(func, time_rule="every_bar", hours=None, minutes=None, reference_security=None)
```

参数：

| 参数 | 说明 |
| --- | --- |
| func | 要运行的函数 |
| time_rule | 运行时间规则，支持 "every_bar" 、 "open" 、 "close" 、 "after_open" 、 "before_close" 和 "HH:MM" |
| hours | 配合 "after_open" / "before_close" 使用的小时偏移 |
| minutes | 配合 "after_open" / "before_close" 使用的分钟偏移 |
| reference_security | 【迁移兼容】参数，当前只保留签名 |

时间规则：

| 规则 | 触发时机 |
| --- | --- |
| "every_bar" | 每根 bar 触发 |
| "open" / "market_open" | 每个交易日第一根 bar 触发 |
| "close" / "market_close" | 每个交易日最后一根 bar 触发 |
| "after_open" | 开盘后偏移触发，例如 minutes=30 表示 10:00；日线回测中退化为当日第一根 bar |
| "before_close" | 收盘前偏移触发，例如 minutes=10 表示 14:50；日线回测中退化为当日最后一根 bar |
| "HH:MM" | 精确匹配分钟时间，例如 "10:30" |

示例：

```python
def init(context):
    run_daily(trade, time_rule="every_bar")
    run_daily(open30, time_rule="after_open", minutes=30)
    run_daily(close10, time_rule="before_close", minutes=10)

def trade(context, bar_dict):
    pass
```
