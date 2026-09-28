<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1h7k4iqb1grk4/mindoc-1h7k4rp481gt4.html | 章节: 07-tqcenter-交易 -->

#  查询账户委托信息

###  查询指定账户的今日委托信息

```python
def query_stock_orders(account_id:int = 0,
                       stock_code: str = '',
                       cancelable_only: bool = False):
```

###  输入参数

| 参数 | 是否必选 | 参数类型 | 参数说明 |
| --- | --- | --- | --- |
| account_id | Y | int | 资金账号句柄 |
| stock_code | Y | str | 证券代码 |
| cancelable_only | N | bool | 是否仅查询可撤委托 |

  * Status
WTSTATUS_NULL 无效单(0)
WTSTATUS_NOCJ 未成交(1)
WTSTATUS_PARTCJ 部分成交(2)
WTSTATUS_ALLCJ 全部成交(3)
WTSTATUS_BCBC 部分成交部分撤单(4)
WTSTATUS_ALLCD 全部撤单(5)
  * 委托查询只能查询当日委托

###  返回数据

| 数据 | 默认返回 | 数据类型 | 数据说明 |
| --- | --- | --- | --- |
| Wtbh | Y | str | 委托编号 |
| Code | Y | str | 股票代码 |
| Time | Y | str | 时间，HHMMSS |
| BSFlag | Y | int | 买卖标志,0买 1卖 -1撤单 |
| KPFlag | Y | int | 开平标志，0开仓1平仓2平今 |
| WTFS | Y | str | 市价方式，根据沪深市场不一样 |
| Status | Y | int | 委托状态 |
| WtDate | Y | int | 撤单标志，为1表示已撤,为2表示是夜盘单 |
| CjPrice | Y | str | 成交价 |
| CjVol | Y | str | 成交数量 如果是撤,则为负值 |
| WtPrice | Y | str | 委托价 |
| WtVol | Y | str | 委托数量 如果是撤,则为负值 |

###  接口使用

```python
from tqcenter import tq
tq.initialize(__file__)
myAccount = tq.stock_account(account="1190008847", account_type="STOCK")
print(myAccount)
stock_orders = tq.query_stock_orders(account_id=myAccount, stock_code="")
print(stock_orders)
```

###  数据样本

```text
[{'Wtbh': '48957', 'Code': '688318.SH', 'Time': '93605', 'BSFlag': -1, 'KPFlag': 0, 'WTFS': 0, 'Status': 0, 'WtPrice': '125.000', 'CjPrice': '0.000', 'CjVol': '0', 'WtVol': '1000'},
{'Wtbh': '58545', 'Code': '688318.SH', 'Time': '93853', 'BSFlag': -1, 'KPFlag': 0, 'WTFS': 0, 'Status': 0, 'WtPrice': '125.000', 'CjPrice': '0.000', 'CjVol': '0', 'WtVol': '1000'}]
```
