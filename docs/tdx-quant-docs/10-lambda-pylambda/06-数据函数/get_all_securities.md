<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hhoaleti08f0/mindoc-1hhob255nqs7s.html | 章节: 10-lambda-pylambda/06-数据函数 -->
# 全部证券get_all_securities

###  证券基础信息

```python
get_all_securities(types=None, date=None)
get_security_info(symbol, date=None)
```

`get_all_securities` 返回 `DataFrame`，索引为证券代码，常用列包括：

| 字段 | 说明 |
| --- | --- |
| display_name | 证券名称 |
| name | 证券名称 |
| start_date | 上市或起始日期 |
| end_date | 结束日期，仍有效时为空 |
| type | 证券类型 |
| security_type | 证券类型别名 |
| market | 市场 |
| raw_code | 底层代码 |
| is_valid | 当前是否有效 |

当前 `types` 支持：

```python
stock
index
fund
etf
bond
block
all
```

示例：

```python
stocks = get_all_securities(["stock"], date="2000-01-01")
info = get_security_info("600000.SH")
```
