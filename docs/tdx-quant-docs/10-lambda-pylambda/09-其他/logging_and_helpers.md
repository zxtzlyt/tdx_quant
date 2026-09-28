<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hhoc0a5b29v0.html | 章节: 10-lambda-pylambda/09-其他 -->

#  记录和日志

###  记录指标

记录自定义指标，用于回测结果展示和导出：

```python
record(**kwargs)
get_recorded_data()
```

说明：

  1. `record`用于记录自定义指标。
  2. `get_recorded_data`用于获取已记录指标。

例如：

```python
record(price=price, ma5=ma5, cash=context.portfolio.available_cash)
```

###  日志log

日志对象支持常用方法：

```python
log.info("message")
log.warn("message")
log.error("message")

print(..., flush=True)
```

说明：

  * `print`远程 stdout 有缓冲，必须带`flush`，不可用`sys`。

例如：

```python
log.info("当前时间: %s", context.current_dt)
log.info("当前总资产: %s", context.portfolio.total_value)
```

###  全局变量

平台提供全局变量对象 `g`，用于保存用户自定义状态。

示例：

```python
def init(context):
    g.stock = "000001.SZ"
    g.buy_count = 0

def handle_bar(context, bar_dict):
    if g.buy_count == 0:
        order(g.stock, 1000)
        g.buy_count += 1
```

建议：

  * 简单策略可以使用 `context` 保存变量。
  * 需要跨函数共享的变量可以使用 `g`。
  * 不要覆盖系统字段，例如 `context.portfolio`、`context.run_info`。

###  查询运行态诊断

```python
info = get_runtime_info()
print(info["run"]["symbols"])
print(info["execution"]["order_execution"])
```

`get_runtime_info()` 返回只读的 `lambda-runtime-info/v1` 字典，可在 `init/handle_bar` 内供策略和云平台排查。本接口不触发行情读取、不改变订单、持仓或回测执行状态。`run_backtest/run_signal` 返回后会将 `active` 置为 `false`；调用方必须先检查该字段，不能把残留诊断当作活动任务状态。

| 字段 | 说明 |
| --- | --- |
| active / execution_mode | 当前是否存在活动任务，以及 backtest 或 signal 执行模式 |
| strategy_id / job_id | 信号任务身份；普通回测未设置时为 null |
| run.symbols / run.universe_source / run.universe_finalized | 当前股票池、来源和是否已定稿。回测和信号执行均在 init(context) 返回前保持候选状态；随后以 context.stock 定稿， universe_source 固定为 context.stock ，后续回调中 universe_finalized=true |
| run.benchmark | 实际生效基准，包含策略内 set_benchmark() 修改 |
| run.current_datetime / previous_datetime | 当前和上一根策略事件时间；未进入 bar 时为 null |
| execution | 初始资金、执行价模式、延迟 bar、滑点、手续费、限量和未来数据策略 |
| data.latest_bar_datetime / current_bars | 当前已可见行情的最近时间及各标的当前收盘价快照 |
| data.data_context | SignalJob 预检后已有的数据来源诊断；普通回测或尚未预检时为 null |
