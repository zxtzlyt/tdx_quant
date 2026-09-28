<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hhobbn0nuedg/mindoc-1hhobbvteo4ds.html | 章节: 10-lambda-pylambda/07-交易函数 -->
# 下单order

###  按数量下单

```python
order(symbol, amount, price=None)
```

参数：

| 参数 | 说明 |
| --- | --- |
| symbol | 证券代码 |
| amount | 数量，正数买入，负数卖出 |
| price | 限价价格； None 表示市价 |

示例：

```python
order("000001.SZ", 1000)
order("000001.SZ", -500)
```
