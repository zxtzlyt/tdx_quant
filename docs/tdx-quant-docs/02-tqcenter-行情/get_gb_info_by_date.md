<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1ctuhthaq5qmg/mindoc-1hc4303vsv1fk.html | 章节: 02-tqcenter-行情 -->

#  根据时间段获取股本数据get_gb_info_by_date

###  获取指定股票的股本数据

```python
def get_gb_info_by_date( stock_code:str = '',
                start_date: str = '',
                end_date: str = ''):
```

###  输入参数

| 参数 | 是否必选 | 参数类型 | 参数说明 |
| --- | --- | --- | --- |
| stock_code | Y | str | 股票代码 |
| start_date | Y | str | 开始日期 |
| end_date | Y | str | 截止日期 |

  * 须通过客户端或refresh_kline下载对应股票的日K线数据

###  输出数据

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| Date | double | 日期 |
| Zgb | double | 总股本 |
| Ltgb | double | 流通股本 |

###  接口使用

```python
from tqcenter import tq
tq.initialize(__file__)
gb_info_date = tq.get_gb_info_by_date(stock_code='688318.SH', start_date='20260101', end_date='')
print(gb_info_date)
```

###  数据样本

```text
[{'Date': 20260105, 'Ltgb': 256119392.0, 'Zgb': 256119392.0},
{'Date': 20260106, 'Ltgb': 256119392.0, 'Zgb': 256119392.0},
...,{'Date': 20260513, 'Ltgb': 256119392.0, 'Zgb': 256119392.0},
{'Date': 20260514, 'Ltgb': 256119392.0, 'Zgb': 256119392.0},
{'Date': 20260518, 'Ltgb': 256119392.0, 'Zgb': 256119392.0}]
```
