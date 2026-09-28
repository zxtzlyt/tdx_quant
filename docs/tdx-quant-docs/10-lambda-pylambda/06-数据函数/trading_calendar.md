<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hhoaleti08f0/mindoc-1hhob115b5p0s.html | 章节: 10-lambda-pylambda/06-数据函数 -->
# 交易日历函数

###  交易日历

```python
get_trade_days(start_date=None, end_date=None, count=None)
get_all_trade_days()
```

说明：

  * `get_trade_days` 返回指定区间内的交易日列表，元素为 `datetime.date`。
  * `count` 非空时返回指定数量的交易日。
  * 当前默认使用沪市交易日历。

示例：

```python
days = get_trade_days("2000-01-01", "2000-01-10")
last_5_days = get_trade_days(end_date=context.current_dt, count=5)
```
