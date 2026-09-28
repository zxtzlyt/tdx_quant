<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1h7k4iqb1grk4/mindoc-1h7k5ar9kc508.html | 章节: 07-tqcenter-交易 -->

#  查询账户持仓信息

###  查询指定账户的持仓信息

```python
def query_stock_positions(account_id:int = 0):
```

###  输入参数

| 参数 | 是否必选 | 参数类型 | 参数说明 |
| --- | --- | --- | --- |
| account_id | Y | int | 资金账号句柄 |

###  返回数据

| 数据 | 默认返回 | 数据类型 | 数据说明 |
| --- | --- | --- | --- |
| Code | Y | str | 证券代码 |
| Cbj | Y | str | 成本价 |
| TotalVol | Y | str | 总持仓 |
| CanUseVol | Y | str | 可用持仓 |
| BuyPosition | Y | str | 多头持仓（期货或期权） |
| BuyAvgPrice | Y | str | 多头持仓均价（期货或期权） |
| BuyProfitLoss | Y | str | 多头持仓盈亏（期货或期权） |
| SellPosition | Y | str | 空头持仓（期货或期权） |
| SellAvgPrice | Y | str | 空头持仓均价（期货或期权） |
| SellProfitLoss | Y | str | 空头持仓盈亏（期货或期权） |
| TodayBuyPosition | Y | str | 当日买入持仓（期货或期权） |
| TodaySellPosition | Y | str | 当日卖出持仓（期货或期权） |

###  接口使用

```python
from tqcenter import tq
tq.initialize(__file__)
myAccount = tq.stock_account(account="1190008847", account_type="STOCK")
print(myAccount)
stock_positions = tq.query_stock_positions(account_id=myAccount)
print(stock_positions)
```

###  数据样本

```text
[{'Code': '000001.SZ', 'Cbj': '10.693', 'TotalVol': '100', 'CanUseVol': '100'},
{'Code': '000501.SZ', 'Cbj': '8.663', 'TotalVol': '1000', 'CanUseVol': '1000'},
{'Code': '000716.SZ', 'Cbj': '7.832', 'TotalVol': '100', 'CanUseVol': '100'},
{'Code': '000800.SZ', 'Cbj': '6.642', 'TotalVol': '1000', 'CanUseVol': '1000'},
{'Code': '000858.SZ', 'Cbj': '102.939', 'TotalVol': '500', 'CanUseVol': '500'},
{'Code': '002029.SZ', 'Cbj': '6.106', 'TotalVol': '100', 'CanUseVol': '100'},
{'Code': '002174.SZ', 'Cbj': '7.233', 'TotalVol': '10000', 'CanUseVol': '10000'},
{'Code': '002251.SZ', 'Cbj': '5.262', 'TotalVol': '100', 'CanUseVol': '100'},
{'Code': '002555.SZ', 'Cbj': '24.648', 'TotalVol': '100', 'CanUseVol': '100'},
{'Code': '002558.SZ', 'Cbj': '13.392', 'TotalVol': '100', 'CanUseVol': '100'},
{'Code': '002624.SZ', 'Cbj': '7.405', 'TotalVol': '10000', 'CanUseVol': '10000'},
{'Code': '159850.SZ', 'Cbj': '0.609', 'TotalVol': '100000', 'CanUseVol': '100000'},
{'Code': '160416.SZ', 'Cbj': '1.678', 'TotalVol': '100000', 'CanUseVol': '100000'},
{'Code': '300459.SZ', 'Cbj': '3.351', 'TotalVol': '10000', 'CanUseVol': '10000'},
{'Code': '603444.SH', 'Cbj': '163.975', 'TotalVol': '100', 'CanUseVol': '100'},
{'Code': '688318.SH', 'Cbj': '117.425', 'TotalVol': '4000', 'CanUseVol': '4000'}]
```
