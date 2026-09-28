<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hhobbn0nuedg/mindoc-1hhobfk2rmg84.html | 章节: 10-lambda-pylambda/07-交易函数 -->
# 订单和成交查询

###  订单和成交查询

```python
get_order(order_id=None, symbol=None, status=None, order_book_id=None)
get_orders(order_id=None, symbol=None, status=None, order_book_id=None)
get_open_orders(order_id=None, symbol=None, order_book_id=None)
get_trades(order_id=None, symbol=None, order_book_id=None)
get_tradelogs(order_id=None, symbol=None, order_book_id=None)
get_trade_signals(order_id=None, symbol=None, signal_type=None, event=None)
get_match_logs(order_id=None, symbol=None)
emit_signal(symbol, side, message="", price=None)
```

参数：

| 参数 | 说明 |
| --- | --- |
| order_id | 订单编号；也可以直接传 Order 对象 |
| symbol | Lambda 标准证券代码，例如 "000001.SZ" |
| order_book_id | 兼容参数，等同于 symbol ；如果和 symbol 同时传入且不一致，会抛出 ValueError |
| status | 订单状态过滤，例如 "open" 、 "filled" 、 "rejected" 、 "canceled" |

返回：

| API | 返回 |
| --- | --- |
| get_order | 第一条匹配的 Order ，没有匹配时返回 None |
| get_orders | 匹配的订单列表 |
| get_open_orders | 当前仍可撤销的未完成订单列表 |
| get_trades | 匹配的成交列表 |
| get_tradelogs | get_trades 的兼容别名 |
| get_match_logs() | 可查看订单提交、等待、部分成交、成交、撤单和过期日志，排查拒单用 |
| emit_signal | 一条标准方向信号字典；仅可在 run_signal(...) 的策略生命周期内调用 |

示例：

```python
order_obj = get_order(order_book_id="000001.SZ")
orders = get_orders(symbol="000001.SZ")
trades = get_trades(order_book_id="000001.SZ")
trade_logs = get_tradelogs(order_book_id="000001.SZ")
signals = get_trade_signals(symbol="000001.SZ")
filled_signals = get_trade_signals(event="filled")
```
