<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hho9d546pbhc/mindoc-1hho9kq57km1c.html | 章节: 10-lambda-pylambda/01-生命周期 -->
# 盘后回调after_trading

###  收盘后函数

```python
def after_trading(context):
    pass
```

用途：

  * 每个交易日收盘后汇总日志。
  * 检查持仓。
  * 输出诊断信息。

兼容`after_trading_end(context, data)`函数名
