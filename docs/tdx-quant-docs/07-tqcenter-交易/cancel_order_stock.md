<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1h7k4iqb1grk4/mindoc-1h84elp5atr6o.html | 章节: 07-tqcenter-交易 -->

#  撤单

###  根据委托编号撤单

```python
def cancel_order_stock(account_id:int = 0,
                       stock_code:str = '',
                       order_id:str = ''):
```

###  输入参数

| 参数 | 是否必选 | 参数类型 | 参数说明 |
| --- | --- | --- | --- |
| account_id | Y | int | 资金账号句柄 |
| stock_code | Y | str | 证券代码 |
| order_id | Y | int | 委托编号 |

###  返回数据

| 数据 | 默认返回 | 数据类型 | 数据说明 |
| --- | --- | --- | --- |
| Value | Y | int | 成功标志，0失败，1成功 |
| Msg | Y | str | 返回提示信息 |

  * 撤单成功后Status状态会变成WTSTATUS_NULL无效单(0)、WTSTATUS_BCBC部分成交部分撤单(4)或WTSTATUS_ALLCD全部撤单(5)

###  接口使用

```python
from tqcenter import tq
from tqcenter import tqconst
tq.initialize(__file__)

myAccount = tq.stock_account(account="1190008847", account_type="STOCK")
print(myAccount)

stock_orders = tq.query_stock_orders(account_id=myAccount, stock_code="")
print(stock_orders)

cancel_res = tq.cancel_order_stock(account_id=myAccount,
                            stock_code=stock_orders[0]['Code'],
                            order_id=stock_orders[0]['Wtbh'])
print(cancel_res)
```

###  数据样本

```text
{'Value': 1, 'ErrorId': '0', 'Msg': '提交撤单成功！'}
```
