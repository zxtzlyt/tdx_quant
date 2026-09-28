<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1ctuhthaq5qmg/mindoc-1hlnpjm512efk.html | 章节: 02-tqcenter-行情 -->
# 快照批量get_market_snapshot_batch

###  批量获取快照数据get_market_snapshot_batch

####  根据证券代码列表批量获取实时行情快照，含现价、买卖五档、内外盘、涨速等

```python
get_market_snapshot_batch(
stock_list: list[str] = [],
field_list: list[str] = [],
return_df: bool = False
) -> Dict
```

####  输入参数

| 参数 | 是否必选 | 参数类型 | 参数说明 |
| --- | --- | --- | --- |
| stock_list | Y | list[str] | 证券代码列表，须带市场后缀，例如 ["600000.SH", "688318.SH"] |
| field_list | N | list[str] | 指定返回字段，为空 [] 返回全部字段，未知字段静默忽略 |
| return_df | N | bool | 为 True 且已安装 pandas 时返回 DataFrame（行索引为证券代码），否则返回 dict |

####  返回数据

| 数据字段 | 默认返回 | 数据类型 | 数据说明 |
| --- | --- | --- | --- |
| ItemNum | Y | str | 快照笔数 |
| LastClose | Y | str | 前收盘价 |
| Open | Y | str | 开盘价 |
| Max | Y | str | 最高价 |
| Min | Y | str | 最低价 |
| Now | Y | str | 现价 |
| Volume | Y | str | 总手 |
| NowVol | Y | str | 现手（总手差） |
| RefreshTime | Y | str | 行情刷新时间，格式 HHMMSS |
| Amount | Y | str | 总成交金额 |
| Inside | Y | str | 内盘（板块指数时为跌停家数） |
| Outside | Y | str | 外盘（板块指数时为涨停家数） |
| TickDiff | Y | str | 笔涨跌（价位差） |
| InOutFlag | Y | str | 内外盘标志：0=Buy, 1=Sell, 2=Unknown |
| Jjjz | Y | str | 基金净值 |
| Buyp | Y | List[str] | 五档买价（5 个元素） |
| Buyv | Y | List[str] | 五档买盘量（5 个元素） |
| Sellp | Y | List[str] | 五档卖价（5 个元素） |
| Sellv | Y | List[str] | 五档卖盘量（5 个元素） |
| UpHome | Y | str | 上涨家数（对指数有效） |
| DownHome | Y | str | 下跌家数（对指数有效） |
| Before5MinNow | Y | str | 5 分钟前价格 |
| Average | Y | str | 均价 |
| XsFlag | Y | str | 小数位数 |
| Zangsu | Y | str | 涨速 |
| ZAFPre3 | Y | str | 3 日涨幅 |

> 外层结构为 {证券代码: {字段: 值}}，每个证券一条记录、键顺序与 stock_list 入参顺序一致。单只无行情时该代码的记录为空或字段返回 null。

####  接口使用

批量获取 600000.SH 与 688318.SH 的实时行情快照。

```python
snap = tq.get_market_snapshot_batch(
stock_list=["600000.SH", "688318.SH"],
)
print(snap)
```

####  数据样本

```json
{
"600000.SH": {
"Amount": "46996.94",
"Average": "9.08",
"Before5MinNow": "9.09",
"Buyp": ["9.07", "9.06", "9.05", "9.04", "9.03"],
"Buyv": ["4467", "11048", "7788", "5161", "4586"],
"DownHome": "0",
"InOutFlag": "2",
"Inside": "247892",
"ItemNum": "3716",
"Jjjz": "3330583.75",
"LastClose": "9.06",
"Max": "9.15",
"Min": "9.00",
"Now": "9.07",
"NowVol": "53978",
"Open": "9.05",
"Outside": "269701",
"RefreshTime": "153058",
"Sellp": ["9.08", "9.09", "9.10", "9.11", "9.12"],
"Sellv": ["2564", "1316", "2574", "5680", "6306"],
"TickDiff": "0.00",
"UpHome": "0",
"Volume": "517592",
"XsFlag": "2",
"ZAFPre3": "1.01",
"Zangsu": "-0.22"
},
"688318.SH": {
"Amount": "47346.57",
"Average": "79.40",
"Before5MinNow": "80.49",
"Buyp": ["80.50", "80.49", "80.48", "80.46", "80.44"],
"Buyv": ["5", "101", "10", "34", "20"],
"DownHome": "0",
"InOutFlag": "2",
"Inside": "26450",
"ItemNum": "3006",
"Jjjz": "35856.73",
"LastClose": "77.18",
"Max": "81.27",
"Min": "77.50",
"Now": "80.52",
"NowVol": "1027",
"Open": "78.60",
"Outside": "33178",
"RefreshTime": "153103",
"Sellp": ["80.52", "80.53", "80.55", "80.56", "80.57"],
"Sellv": ["41", "107", "12", "34", "7"],
"TickDiff": "0.00",
"UpHome": "0",
"Volume": "59628",
"XsFlag": "2",
"ZAFPre3": "9.53",
"Zangsu": "0.04"
}
}
```
