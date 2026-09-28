<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hhoaleti08f0/mindoc-1hhoalokn8c6g.html | 章节: 10-lambda-pylambda/06-数据函数 -->
# 历史价格get_price

###  获取一个或多个标的的历史行情

```python
get_price(
    securities,
    start_date=None,
    end_date=None,
    frequency="1d",
    fields=None,
    count=None,
    skip_paused=False,
    fq="pre",
    panel=False,
    fill_paused=True,
)
```

参数：

| 参数 | 说明 |
| --- | --- |
| securities | 单个证券代码或证券代码列表 |
| start_date | 起始时间 |
| end_date | 结束时间 |
| frequency | 周期，支持 1d 、 1m 、 5m 、 15m 、 30m 、 60m 、 hour2 、 week 、 month 、 quarter 、 halfyear 、 year ；也支持相应别名 |
| fields | 字段列表，例如 ["open", "close"] |
| count | 向前取多少根 bar |
| skip_paused | 是否跳过停牌 |
| fq | 复权方式，支持 "pre" 、 "post" 、 None |
| panel | 是否返回 Panel，当前不建议使用 |
| fill_paused | 停牌时是否填充价格 |

示例：

```python
df = get_price(
    "000001.SZ",
    start_date="2024-01-01",
    end_date="2024-03-01",
    frequency="1d",
    fields=["open", "close", "volume"],
)
```

多标的示例：

```python
data = get_price(
    ["000001.SZ", "600000.SH"],
    count=20,
    end_date=context.current_dt,
    frequency="1d",
    fields=["close"],
)
```
