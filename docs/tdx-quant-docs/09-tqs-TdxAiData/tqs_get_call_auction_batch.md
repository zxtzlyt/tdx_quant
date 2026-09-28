<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hjbidnohpjn4/mindoc-1hlsf010md5gg.html | 章节: 09-tqs-TdxAiData -->
# 集合竞价批量get_call_auction_batch

###  批量获取集合竞价get_call_auction_batch

####  根据证券代码列表批量获取当日集合竞价逐笔虚拟撮合数据

```python
get_call_auction_batch(
stock_list: list[str] = [],
field_list: list[str] = [],
return_df: bool = False
) -> Dict
```

####  输入参数

| 参数 | 是否必选 | 参数类型 | 参数说明 |
| --- | --- | --- | --- |
| stock_list | Y | list[str] | 证券代码列表，须带市场后缀，例如 ["688318.SH", "600000.SH"] |
| field_list | N | list[str] | 指定返回字段，为空 [] 返回全部字段，未知字段静默忽略 |
| return_df | N | bool | 为 True 且已安装 pandas 时返回 DataFrame（行索引为证券代码），否则返回 dict |

####  返回数据

| 数据字段 | 默认返回 | 数据类型 | 数据说明 |
| --- | --- | --- | --- |
| Time | Y | List[str] | 时间，格式 HHMMSS |
| Price | Y | List[str] | 虚拟匹配价 |
| Volume | Y | List[str] | 虚拟匹配量 |
| LeaveQty | Y | List[str] | 未匹配量(为正时,表示买单一侧,为负表示卖单一侧) |

> 外层结构为 {证券代码: {字段: 数组}}，键顺序与 stock_list 入参顺序一致，各代码下的字段与单只接口 get_call_auction 相同。

####  接口使用

批量获取 600000.SH 与 688318.SH 当日集合竞价数据。

```python
from tdxaidata import tqs
auction = tqs.get_call_auction_batch(
stock_list=["600000.SH", "688318.SH"],
)
print(auction)
```

####  数据样本

```json
{
"600000.SH": {
"InOutFlag": ["0", "0", "0", "0", "0", "0", "0", "0"],
"LeaveQty": ["1335", "84", "46", "333", "528", "84", "506", "503"],
"Price": ["9.01", "9.03", "9.03", "9.03", "9.03", "9.04", "9.03", "9.03"],
"Time": ["091504", "091507", "091510", "091513", "091516", "091519", "091528", "091531"],
"Volume": ["1050.00", "1074.00", "1174.00", "1186.00", "1186.00", "1189.00", "1285.00", "1285.00"]
},
"688318.SH": {
"InOutFlag": ["0", "0", "0", "0", "0", "0", "0", "0"],
"LeaveQty": ["-5", "-5", "-2", "10", "-7", "-2", "-4", "-8"],
"Price": ["79.00", "79.00", "78.68", "77.21", "78.20", "78.68", "78.60", "78.20"],
"Time": ["091505", "091511", "091517", "091544", "091617", "091629", "091638", "091650"],
"Volume": ["9.00", "12.00", "12.00", "17.00", "20.00", "12.00", "12.00", "20.00"]
}
}
```
