<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1ctuhthaq5qmg/mindoc-1h10iig4pb6e0.html | 章节: 02-tqcenter-行情 -->

#  获取快照数据get_market_snapshot

###  根据股票，获取最新行情数据

```python
def get_market_snapshot(stock_code: str,
                        field_list: List = []) -> Dict:
```

###  输入参数

| 参数 | 是否必选 | 参数类型 | 参数说明 |
| --- | --- | --- | --- |
| stock_code | Y | str | 证券代码 |
| field_list | N | List[str] | 字段筛选，传空则返回全部 |

  * stock_code为单个证券代码，而不是列表。

提示：

  * 对于本地TQ模式下，客户端若在非报价界面下，买二至买五，卖二至卖五等买卖盘的数据，可能是空的。

###  返回数据

| 数据 | 默认返回 | 数据类型 | 数据说明 |
| --- | --- | --- | --- |
| RefreshNum | Y | str | 行情时间HHMMSS，后台数据模式下支持 |
| ItemNum | Y | str | 快照笔数(即活跃度 |
| LastClose | Y | str | 前收盘价 |
| Open | Y | str | 开盘价 |
| Max | Y | str | 最高价 |
| Min | Y | str | 最低价 |
| Now | Y | str | 现价 |
| Volume | Y | str | 总量 |
| NowVol | Y | str | 现量 |
| Amount | Y | str | 总金额 |
| Inside | Y | str | 内盘 板块指数时为跌停家数 |
| Outside | Y | str | 外盘 板块指数时为涨停家数 |
| TickDiff | Y | str | 笔涨跌 |
| InOutFlag | Y | str | 内外盘标志 0:Buy 1:Sell 2:Unknown |
| Jjjz | Y | str | 基金净值 |
|  |  |  |  |
| Buyp | Y | List[str] | 五个买价 |
| Buyv | Y | List[str] | 对应的五个买盘量 |
| Sellp | Y | List[str] | 五个卖价 |
| Sellv | Y | List[str] | 对应的五个卖盘量 |
| UpHome | Y | str | 上涨家数 对于指数有效 |
| DownHome | Y | str | 下跌家数 对于指数有效 |
|  |  |  |  |
| Before5MinNow | Y | str | 5分钟前价格 |
| Average | Y | str | 均价 |
| XsFlag | Y | str | 小数位数 |
| Zangsu | Y | str | 涨速 |
| ZAFPre3 | Y | str | 3日涨幅 |

  * 对于沪深京品种，Volume，NowVol的单位为手数

###  接口使用

> 例如：获取688318.SH从2025-12-20到今为止最新一条日K线的不复权数据

```python
from tqcenter import tq

tq.initialize(__file__)

market_snapshot = tq.get_market_snapshot(stock_code = '688260.SH', field_list=[])
print(market_snapshot)
```

###  数据样本

```text
{'ItemNum': '3342',
'LastClose': '34.21',
'Open': '33.78',
'Max': '36.49',
'Min': '32.50',
'Now': '35.06',
'Volume': '122881',
'NowVol': '1449',
'Amount': '43068.48',
'Inside': '60373',
'Outside': '62509',
'TickDiff': '0.00',
'InOutFlag': '2',
'Jjjz': '0.00',
'Buyp': ['35.05', '35.04', '35.02', '35.01', '35.00'],
'Buyv': ['154', '9', '49', '136', '154'],
'Sellp': ['35.06', '35.07', '35.08', '35.09', '35.10'],
'Sellv': ['4', '31', '139', '4', '4'],
'UpHome': '0',
'DownHome': '0',
'Before5MinNow': '35.15',
'Average': '35.05',
'XsFlag': '2',
'Zangsu': '-0.25',
'ZAFPre3': '-1.83',
'ErrorId': '0'}
```
