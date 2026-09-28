<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1ctuhthaq5qmg/mindoc-1hce2o96aktmk.html | 章节: 02-tqcenter-行情 -->

#  批量获取价量get_pricevol

###  批量获取指定股票集的前收盘价、现价、涨幅和总量

```python
def get_pricevol(stock_list: List[str] = []):
```

###  输入参数

| 参数 | 是否必选 | 参数类型 | 参数说明 |
| --- | --- | --- | --- |
| stock_list | Y | List[str] | 证券代码列表 |

###  输出数据

| 名称 | 类型 | 数值 | 说明 |
| --- | --- | --- | --- |
| LastClose | Y | str | 前收盘价 |
| Now | Y | str | 现价 |
| Zaf | Y | str | 涨幅(竞价期时用匹配价来计算涨幅) |
| Volume | Y | str | 总量 |

  * 对于沪深京品种，Volume的单位为手数

###  接口使用

```python
from tqcenter import tq
tq.initialize(__file__)
all_stocks = tq.get_stock_list(market='23')
pv_info = tq.get_pricevol(stock_list=all_stocks)
print(pv_info)
```

###  数据样本

```text
{'000001.SZ': {'LastClose': '10.70', 'Now': '10.71', 'Volume': '422239'},
'000002.SZ': {'LastClose': '3.47', 'Now': '3.46', 'Volume': '423677'},
'000063.SZ': {'LastClose': '34.83', 'Now': '34.99', 'Volume': '587361'},
'000100.SZ': {'LastClose': '4.37', 'Now': '4.17', 'Volume': '10003565'},
'000157.SZ': {'LastClose': '7.27', 'Now': '7.20', 'Volume': '227512'},
'000166.SZ': {'LastClose': '4.47', 'Now': '4.42', 'Volume': '445736'},
'000301.SZ': {'LastClose': '12.52', 'Now': '12.53', 'Volume': '100953'},
'000333.SZ': {'LastClose': '81.50', 'Now': '80.45', 'Volume': '99257'},
'000338.SZ': {'LastClose': '32.28', 'Now': '33.13', 'Volume': '422523'},
'000408.SZ': {'LastClose': '78.19', 'Now': '78.99', 'Volume': '36197'},
'000425.SZ': {'LastClose': '9.57', 'Now': '9.62', 'Volume': '418614'},
'000538.SZ': {'LastClose': '50.13', 'Now': '49.87', 'Volume': '33429'},...}
```
