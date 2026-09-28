<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hib696p7b7gc/mindoc-1hib6nhrouuvg.html | 章节: 10-lambda-pylambda/08-账户查询 -->
# 获取单持仓get_position

###  查单只持仓 get_position

```python
get_position(symbol, refresh=True)
```

用途：

  * `get_position(symbol=None, order_book_id=None, refresh=True)` 返回单只证券 `Position`；无持仓返回 `None`；未传代码会报错。
