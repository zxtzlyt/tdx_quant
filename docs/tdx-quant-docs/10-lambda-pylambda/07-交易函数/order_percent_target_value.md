<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hhobbn0nuedg/mindoc-1hhobe5d2u5e8.html | 章节: 10-lambda-pylambda/07-交易函数 -->
# 比例目标市值下单

###  比例和目标市值下单

当前版本已支持以下交易函数：

```python
order_percent(symbol, percent, price=None)
order_target_value(symbol, cash_amount, price=None)
order_target_percent(symbol, percent, price=None)
```

说明：

  * `order_percent` 表示按账户总资产比例发出本次买卖金额，例如 `0.2` 表示买入约 20% 总资产对应的金额。
  * `order_target_value` 表示把单个标的调整到目标市值。
  * `order_target_percent` 表示把单个标的调整到账户总资产的目标比例。

示例：

```python
order_target_percent("000001.SZ", 0.5)
order_target_value("000001.SZ", 100000)
order_percent("000001.SZ", 0.1)
```
