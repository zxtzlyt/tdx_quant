<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hi3n0rqkakt4/mindoc-1hhob7ou94li8.html | 章节: 10-lambda-pylambda/05-特有行情 -->
# 分笔数据get_tick_data

###  分笔成交数据

```python
get_tick_data(stock_code, date, startxh=0, wantnum=2000, field_list=None)
```

说明：

  * `stock_code` 支持 `600000.SH`、`000001.SZ` 这类带市场后缀代码。
  * `date` 支持 `YYYYMMDD`、`YYYY-MM-DD` 或 `datetime/date`。
  * `startxh` 为起始序号，从 `0` 开始；`wantnum` 为请求条数，当前按协议限制在 `1..2000`。
  * 默认返回 `Time / Price / Volume / BSFlag / records` 等字段；传入 `field_list` 时只保留命中字段。

示例：

```python
tick = get_tick_data("600000.SH", "20260720", startxh=0, wantnum=10)
print(tick["records"][:3])
```

注意：

  * 这组数据是分笔成交，不是 K 线数据；历史 K 线查询仍走 `get_price / get_market_data` 对应的数据驱动链路。
  * 缺少包含 `get_tick_data` 的新版 `pylambda.core` 时会抛出 `NotImplementedError`。
