<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hib696p7b7gc/mindoc-1hib6kkioc08g.html | 章节: 10-lambda-pylambda/08-账户查询 -->
# 获取持仓列表get_positions

###  查全部/指定持仓字典 get_positions

```python
get_positions(symbols=None, refresh=True)
```

用途：

  * `get_positions(symbols=None, order_book_id=None, refresh=True)` 返回 `dict[str, Position]`；不传过滤条件时返回全部持仓。
