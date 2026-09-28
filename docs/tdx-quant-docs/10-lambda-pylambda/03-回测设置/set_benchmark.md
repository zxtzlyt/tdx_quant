<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hhoa58m7i93s/mindoc-1hhoa5ki6fpkk.html | 章节: 10-lambda-pylambda/03-回测设置 -->
# 设置基准set_benchmark

###  设置回测基准

```python
set_benchmark(symbol)
```

回测结束后，`run_backtest` 会返回 `result.benchmark`、`result.strategy_returns`、`result.benchmark_returns`、`result.return_comparison` 和 `result.drawdowns`。其中 `benchmark_returns` 是基准代码在本次回测区间内的逐 bar 收益率序列；策略收益率仍以 `result.funds[*].returns` 为准，`result.strategy_returns` 是面向前端画图的策略逐 bar 收益率序列，`result.return_comparison` 会把策略收益率和基准收益率按时间对齐，`result.drawdowns` 是策略资金曲线的逐 bar 回撤序列。

示例：

```python
def init(context):
    context.stock = ["000001.SZ"]
    set_benchmark("000300.SH")
    set_execution("close")
def handle_bar(context, bar_dict):
    for sym in context.stock:
        order_target_percent(sym,0.2)
```

示例说明：
![](https://help.tdx.com.cn/quant/uploads/mindoc/images/m_d993c1d619296642524cd7265c5bd6c7_r.png)
100万初始资金的设置，调整股票目标仓位到总资产的20% 首次下单如图。
![](https://help.tdx.com.cn/quant/uploads/mindoc/images/m_72bb5b0beef99c2da6e62217d86defa3_r.png)
基准沪深300的收益和其当日涨幅一致。标准设置正常。
