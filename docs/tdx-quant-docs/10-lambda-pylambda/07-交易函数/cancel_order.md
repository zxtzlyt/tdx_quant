<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hhobbn0nuedg/mindoc-1hhobgp6ravs4.html | 章节: 10-lambda-pylambda/07-交易函数 -->
# 提交撤单

###  提交撤单

```python
cancel_order(order)
cancel_order_all()
```

当前版本同时支持同步市价成交和Python最小版挂单撮合。

  * `price=None` 的普通订单默认仍按当前 bar 同步成交。
  * 显式传入 `price` 时按限价单进入挂单队列。
  * `set_trade_delay(value)` 大于 0 时，市价单会延迟到后续 bar 撮合。
  * `get_open_orders()` 返回 `open / pending / partial_filled` 订单。
  * `cancel_order()` 可撤销未完成订单；已成交、已拒绝、已过期订单不可撤。
  * `cancel_order_all()` 会批量撤销当前未完成订单。
