<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hibf3lo5qk7g/mindoc-1hibf6bvaogfo.html | 章节: 10-lambda-pylambda/04-定时任务 -->
# 按周月定时

###  按周、按月定时运行函数

```python
run_weekly(func, date_rule=1, reference_security=None, time_rule="open", hours=None, minutes=None, weekday=None)
run_monthly(func, date_rule=1, reference_security=None, time_rule="open", hours=None, minutes=None, tradingday=None)
```

参数：

| 参数 | 说明 |
| --- | --- |
| func | 要运行的函数 |
| date_rule | 交易日位置规则；正数表示第 N 个交易日，负数表示倒数第 N 个交易日，不能为 0 |
| weekday | 【迁移兼容】 run_weekly 的 date_rule 别名 |
| tradingday | 【迁移兼容】 run_monthly 的 date_rule 别名 |
| time_rule | 与 run_daily 相同，默认 "open" |
| hours / minutes | 配合 after_open / before_close 使用的偏移 |
| reference_security | 【迁移兼容】参数，当前只保留签名 |

示例：

```python
def init(context):
    run_weekly(rebalance_week_start, date_rule=1)
    run_weekly(rebalance_week_end, date_rule=-1)
    run_monthly(rebalance_month_start, date_rule=1)
    run_monthly(rebalance_month_end, tradingday=-1)
```

说明：`run_weekly / run_monthly` 基于完整交易日历判断周/月第 N 个交易日，不把回测窗口起止日误认为周初、月初、周末或月末；不按自然日触发。若完整交易日历不可读取，runner 会抛出 `RuntimeError`，避免错误触发周/月调度。`run_daily / run_weekly / run_monthly` 都在 `handle_bar` 前执行。
