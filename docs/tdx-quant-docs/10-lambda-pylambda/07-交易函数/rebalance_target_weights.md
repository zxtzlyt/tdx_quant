<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hhobbn0nuedg/mindoc-1hhoberagvv8c.html | 章节: 10-lambda-pylambda/07-交易函数 -->
# 组合目标权重调仓

###  12.5 组合目标权重调仓

当前版本已支持多标的目标权重调仓：

```python
equal_weight(symbols, total_percent=1.0)
normalize_weights(weights, total_percent=1.0)
order_target_weights(weights, close_missing=False)
```

说明：

  * `equal_weight` 用于生成等权目标权重。
  * `normalize_weights` 用于把任意非负权重归一化到指定总仓位。
  * 回测阶段 `order_target_weights` 按账户总资产快照计算目标市值，并按先卖后买顺序提交订单。
  * 执行阶段 `order_target_weights` 只输出目标权重/目标仓位信号；有 `account_snapshot` 时换算差额，缺快照时输出 `blocked`，不在云端下单。
  * `close_missing=True` 时，会把当前持仓中未出现在 `weights` 里的标的目标权重视为 `0`。
  * 当前权重合计不能超过 `1`，不支持负权重和做空。

示例：

```python
stocks = ["000001.SH", "600000.SH"]
weights = equal_weight(stocks, total_percent=0.8)
order_target_weights(weights)

new_weights = normalize_weights({"000001.SH": 3, "600000.SH": 1}, total_percent=0.8)
order_target_weights(new_weights)
order_target_weights({"000001.SH": 0.5}, close_missing=True)
```
