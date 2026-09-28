<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1h7k4iqb1grk4/mindoc-1h84fvcjulrnc.html | 章节: 07-tqcenter-交易 -->

#  查询账户资产信息

###  查询指定账户的今日委托信息

```python
def query_stock_asset(account_id:int = 0):
```

###  输入参数

| 参数 | 是否必选 | 参数类型 | 参数说明 |
| --- | --- | --- | --- |
| account_id | Y | int | 资金账号句柄 |

###  返回数据

| 数据 | 默认返回 | 数据类型 | 数据说明 |
| --- | --- | --- | --- |
| Currency | Y | str | 币种 |
| Balance | Y | str | 余额 |
| Cash | Y | str | 可用余额 |
| Asset | Y | str | 资产 |
| MarketValue | Y | str | 总市值 |
| TotalFreeze | Y | str | 期货冻结资金 |
| CloseProfit | Y | str | 期货平仓盈亏 |
| CurrentEquity | Y | str | 期货动态权益 |
| PreviousEquity | Y | str | 期货静态权益 |
| ProfitLoss | Y | str | 期货持仓盈亏 |
| TotalMargin | Y | str | 期货持仓保证金 |

###  接口使用

```python
from tqcenter import tq
tq.initialize(__file__)
myAccount = tq.stock_account(account="1190008847", account_type="STOCK")
print(myAccount)
zc_res = tq.query_stock_asset(account_id=myAccount)
print(zc_res)
```

###  数据样本

```text
{'Currency': '人民币', 'Balance': '30234.070', 'Cash': '30234.070', 'Asset': '1233041.070', 'MarketValue': '1201690.000', 'ErrorId': '0'}
```
