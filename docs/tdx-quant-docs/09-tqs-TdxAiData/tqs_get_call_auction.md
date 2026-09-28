<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hjbidnohpjn4/mindoc-1hlsevg97ftug.html | 章节: 09-tqs-TdxAiData -->
# 集合竞价get_call_auction

###  获取集合竞价get_call_auction

####  根据证券代码获取当日集合竞价逐笔虚拟撮合数据，含开盘集合竞价（09:15-09:25）与收盘集合竞价（14:57-15:00）两段

```python
get_call_auction(
stock_code: str
) -> DataFrame
```

####  输入参数

| 参数 | 是否必选 | 参数类型 | 参数说明 |
| --- | --- | --- | --- |
| stock_code | Y | str | 单只证券代码，例如 688318.SH |

####  返回数据

| 数据字段 | 默认返回 | 数据类型 | 数据说明 |
| --- | --- | --- | --- |
| Time | Y | List[str] | 撮合时间，格式 HHMMSS |
| Price | Y | List[str] | 虚拟匹配价 |
| Volume | Y | List[str] | 虚拟匹配量 |
| LeaveQty | Y | List[str] | 未匹配量(为正时,表示买单一侧,为负表示卖单一侧) |

####  接口使用

获取 688318.SH 当日集合竞价数据。

```python
from tdxaidata import tqs
auction = tqs.get_call_auction(
stock_code="688318.SH",
)
print(auction)
```

####  数据样本

```json
{
"InOutFlag": ["0", "0", "0", "0", "0", "0", "0", "0"],
"LeaveQty": ["-5", "-5", "-2", "10", "-7", "-2", "-4", "-8"],
"Price": ["79.00", "79.00", "78.68", "77.21", "78.20", "78.68", "78.60", "78.20"],
"Time": ["091505", "091511", "091517", "091544", "091617", "091629", "091638", "091650"],
"Volume": ["9.00", "12.00", "12.00", "17.00", "20.00", "12.00", "12.00", "20.00"]
}
```

> 实际返回 127 条，为便于展示此处仅截取前 8 条；返回为以字段名为列的 DataFrame，未安装 pandas 时返回同结构的 dict。
