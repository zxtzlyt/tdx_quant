<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hhodgohoq4j0.html | 章节: 10-lambda-pylambda/09-其他 -->

#  常见问题

###  为什么下单数量和传入数量不同？

平台会按 A 股交易规则、现金、持仓和成交规则调整订单数量。

常见原因：

  * 买入资金不足。
  * 卖出数量超过可卖持仓。
  * 当日买入数量受 T+1 规则限制，不能同日卖出。
  * 买入数量不是 100 股整数倍。
  * 标的停牌或涨跌停。

###  为什么历史数据取不到？

常见原因：

  * 证券代码格式错误。
  * 数据源中没有该标的。
  * 查询时间超出数据范围。
  * 查询了当前回测时间之后的数据。

###  为什么某些 API 提示不支持？

当前版本优先支持股票日线和分钟回测。Tick、期货、期权、融资融券、完整撤单和盘口撮合属于后续扩展能力。

###  客户策略应该使用哪个入口？

新策略建议使用：

```python
def init(context):
    pass

def handle_bar(context, bar_dict):
    pass
```

兼容旧写法时也可以使用：

```python
def initialize(context):
    pass

def handle_data(context, data):
    pass
```
