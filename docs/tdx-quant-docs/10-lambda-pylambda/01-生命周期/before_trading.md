<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hho9d546pbhc/mindoc-1hho9irt0nu3s.html | 章节: 10-lambda-pylambda/01-生命周期 -->
# 盘前回调before_trading

###  开盘前函数

```python
def before_trading(context):
    pass
```

用途：

  * 每个交易日开盘前准备数据。
  * 重置当日临时变量。
  * 生成当日候选股票池。

兼容`before_trading_start(context, data)`函数名
