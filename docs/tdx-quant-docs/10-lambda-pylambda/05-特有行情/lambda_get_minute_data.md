<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hi3n0rqkakt4/mindoc-1hi3n2jbg66bs.html | 章节: 10-lambda-pylambda/05-特有行情 -->
# 分钟数据get_minute_data

###  单日分时数据

```python
get_minute_data(stock_code, date, field_list=None)
```

说明：

  * `stock_code` 支持 `600000.SH`、`000001.SZ` 这类带市场后缀代码。
  * `date` 支持 `YYYYMMDD`、`YYYY-MM-DD` 或 `datetime/date`。
  * `get_minute_data` 返回 `Time / Price / Average / Volume / records / TotalNum`；传入 `field_list` 时只保留命中字段。

示例：

```python
minute = get_minute_data("600000.SH", "2026-08-04", ["Time", "Price", "Average", "Volume"])
print(minute["records"][:3])
```
