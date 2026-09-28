<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hhoaleti08f0/get_security_info.html | 章节: 10-lambda-pylambda/06-数据函数 -->
# 证券信息get_security_info

```python
get_security_info(symbol, date=None)
```

示例：

```python
get_security_info("000001.SZ")
```

###字段说明

###  数据样本

```text
SecurityInfo(
    code='000001.SZ',
    display_name='平安银行',
    name='平安银行',
    start_date=datetime.date(1990, 12, 19),
    end_date=datetime.date(9999, 12, 31),
    type='stock',
    security_type='stock',
    market='SZ',
    raw_code='SZ000001',
    raw=Stock(SZ, 000001, 平安银行, A, 1, 1990‑12‑19 00:00:00, 9999‑12‑31 00:00:00)
)
```
