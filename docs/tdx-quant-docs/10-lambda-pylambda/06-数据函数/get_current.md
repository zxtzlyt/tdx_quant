<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hhoaleti08f0/mindoc-1hhoave9jakik.html | 章节: 10-lambda-pylambda/06-数据函数 -->
# 当前数据get_current

###  获取当前bar行情

```python
get_current(symbols=None)
```

示例：

```python
current = get_current(["000001.SZ", "600000.SH"])
price = current["000001.SZ"].close
```

###字段说明

| 字段 | 说明 |
| --- | --- |
| symbol | 证券代码 |
| datetime | bar 时间 |
| open | 开盘价 |
| high | 最高价 |
| low | 最低价 |
| close | 收盘价 |
| volume | 成交量 |
| amount | 成交额 |
| money | 【迁移兼容】 amount 的别名 |
| paused | 是否停牌 |
| is_st | 属性保留但当前数据层不注入真实 ST 状态，始终使用默认值 false ，不能作为 ST 判断依据 |
| high_limit | 涨停价，字段存在且大于 0 时会参与买入拒单判断 |
| low_limit | 跌停价，字段存在且大于 0 时会参与卖出拒单判断 |

###  数据样本

```text
{
    '000001.SZ': Bar(
        symbol='000001.SZ',
        datetime=datetime.datetime(2026, 8, 12, 0, 0),
        open=11.26,
        high=11.29,
        low=11.2,
        close=11.25,
        volume=63295024.0,
        amount=71161.29,
        money=71161.29,
        paused=False,
        is_st=False,
        high_limit=None,
        low_limit=None
    ),
    '600000.SH': Bar(
        symbol='600000.SH',
        datetime=datetime.datetime(2026, 8, 12, 0, 0),
        open=9.21,
        high=9.22,
        low=9.12,
        close=9.17,
        volume=46782492.0,
        amount=42921.22,
        money=42921.22,
        paused=False,
        is_st=False,
        high_limit=None,
        low_limit=None
    )
}
```
