<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1h7k4iqb1grk4/mindoc-1h7k4k5tk6q64.html | 章节: 07-tqcenter-交易 -->

#  获取资金账户句柄

###  获取指定资金账户的句柄

```python
def stock_account(account:str = '',
                  account_type: str = 'stock') -> int:
```

###  输入参数

| 参数 | 是否必选 | 参数类型 | 参数说明 |
| --- | --- | --- | --- |
| account | Y | str | 资金账号 |
| account_type | Y | str | 账号类型 |

  * 获取句柄须先在客户端登陆指定账号
  * 返回值大于0时为有效句柄，小于0时为无效句柄
  * 涉及到交易函数的调用前，必须要先使用stock_account函数得到account句柄
  * account为空时，默认为当前登陆账户
  * account_type当前可选：'STOCK' 股票交易, 'CREDIT' 信用交易 'FUTURE' 期货交易 'OPTION' 期权交易。如果不设参数，就是'STOCK'。如果是期货通版本的期货账号，则必须要指定为'FUTURE'。

###  接口使用

```python
from tqcenter import tq
tq.initialize(__file__)
myAccount = tq.stock_account(account="1190008847", account_type="STOCK")
print(myAccount)
```

###  数据样本

```text
0
```
