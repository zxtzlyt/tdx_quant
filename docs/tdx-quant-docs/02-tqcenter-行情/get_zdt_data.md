<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1ctuhthaq5qmg/mindoc-1hh9i0av0gtok.html | 章节: 02-tqcenter-行情 -->

#  获取股票涨跌停数据get_zdt_data

###  获取指定股票集的涨跌停数据

```python
def get_zdt_data(stock_list: List[str] = []):
```

###  输入参数

| 参数 | 是否必选 | 参数类型 | 参数说明 |
| --- | --- | --- | --- |
| stock_list | Y | List[str] | 股票代码列表 |

  * 此函数需要通达信客户端有短线宝权限（普及增强版、财富版、专业版等）
  * tqcenter本地客户端模式下，首次调用此接口，客户端需要缓存数据，首次取到的数据可能为空

###  输出数据

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| Code | str | 标准证券代码 |
| TimeNow | str | 当前时间 |
| ZDTStatusNow | str | 当前涨跌停状态：1 自然涨停，2 一字涨停，3 曾涨停，4 自然跌停，5 一字跌停，6 曾跌停，7 涨超 10%，8 跌超 10% |
| ZDTStatusOri | str | 历史涨跌停状态：3 曾涨停，6 曾跌停 |
| FirstTimeZT / FirstTimeDT | str | 首次涨停 / 跌停时间 |
| LastOpenTimeZT / LastOpenTimeDT | str | 最后涨停 / 跌停打开时间 |
| LastTimeZT / LastTimeDT | str | 最近一次涨停 / 跌停时间 |
| OpenTimesZT / OpenTimesDT | str | 涨停 / 跌停打开次数 |
| FDVolMaxZT / FDVolMaxDT | str | 最高涨停 / 跌停封单量 |
| VolZT | str | 涨停时累计成交量 |

###  接口使用

```python
from tqcenter import tq
tq.initialize(__file__)
zdt_data = tq.get_zdt_data(stock_list=['603221.SH'])
print(zdt_data)
```

###  数据样本

```text
{'603221.SH': {'Code': '603221.SH', 'TimeNow': '150016', 'ZDTStatusNow': '2', 'ZDTStatusOri': '0', 'FirstTimeZT': '92501', 'FirstTimeDT': '0', 'LastOpenTimeZT': '0', 'LastOpenTimeDT': '0', 'LastTimeZT': '92501', 'LastTimeDT': '0', 'OpenTimesZT': '0', 'OpenTimesDT': '0', 'FDVolMaxZT': '2064643.00', 'FDVolMaxDT': '0.00', 'VolZT': '9867.00'}}
```
