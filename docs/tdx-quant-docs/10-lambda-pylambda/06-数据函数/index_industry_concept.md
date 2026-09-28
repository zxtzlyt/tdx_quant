<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hhoaleti08f0/mindoc-1hhob9ldbiqak.html | 章节: 10-lambda-pylambda/06-数据函数 -->
# 获取指数行业和概念成份

###  指数、行业和概念成分

```python
get_index_stocks(index_symbol, date=None)
get_industry_stocks(industry_code, date=None)
get_concept_stocks(concept_code, date=None)
get_index_weight(index_symbol, date=None)
```

说明：

  1. `get_index_stocks`用于获取指定指数在指定日期的成分股股票代码列表。
  2. `get_industry_stocks`用于获取指定行业指数代码在指定日期的成分股股票代码列表。
  3. `get_concept_stocks`用于获取指定概念下的成分股。
  4. `get_index_weight`用于获取指定指数在指定日期的成分股权重数据。

示例：

```python
hs300 = get_index_stocks("000300.SH")
food = get_industry_stocks("食品饮料")
cloud = get_concept_stocks("云计算")
```
