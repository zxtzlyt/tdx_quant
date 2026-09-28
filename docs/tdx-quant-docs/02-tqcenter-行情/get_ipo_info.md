<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1ctuhthaq5qmg/mindoc-1h137jr3khrqo.html | 章节: 02-tqcenter-行情 -->

#  获取新股申购信息get_ipo_info

###  获取今天及未来的新股或新发债申购信息

```python
get_ipo_info(ipo_type:int = 0,
             ipo_date:int = 0):
```

###  输入参数

| 参数 | 是否必选 | 参数类型 | 参数说明 |
| --- | --- | --- | --- |
| ipo_type | Y | str | 自定义板块简称 |
| ipo_date | Y | int | 自定义板块名称 |

  * ipo_type=0 表示获取新股申购信息
  * ipo_type=1 表示获取新发债信息
  * ipo_type=2 表示获取新股和新发债信息
  * ipo_date=0 表示只获取今天信息
  * ipo_date=1 表示获取今天及以后信息

###  返回数据

| 数据 | 默认返回 | 数据类型 | 数据说明 |
| --- | --- | --- | --- |
| Code | Y | str | 证券代码 |
| Name | Y | str | 证券名称 |
| SGDate | Y | str | 申购日期 |
| SGPrice | Y | str | 申购价格 |
| SGCode | Y | str | 申购代码 |
| MaxSG | Y | str | 申购上限 |
| PE_Issue | Y | str | 发行市盈率 |

###  接口使用

```python
from tqcenter import tq
tq.initialize(__file__)
ipo_info = tq.get_ipo_info(ipo_type=2, ipo_date=1)
print(ipo_info)
```

###  数据样本

```text
[{'Code': '001248.SZ', 'Name': '华润新能源', 'SGDate': '20260622', 'SGPrice': '0.00', 'SGCode': '1248', 'MaxSG': '0.00', 'PE_Issue': '0.00'},
{'Code': '920072.BJ', 'Name': '科莱瑞迪', 'SGDate': '20260615', 'SGPrice': '0.00', 'SGCode': '920072', 'MaxSG': '0.00', 'PE_Issue': '0.00'},
{'Code': '001399.SZ', 'Name': '惠科股份', 'SGDate': '20260612', 'SGPrice': '10.12', 'SGCode': '1399', 'MaxSG': '21.85', 'PE_Issue': '25.45'},
{'Code': '688797.SH', 'Name': '臻宝科技', 'SGDate': '20260612', 'SGPrice': '44.56', 'SGCode': '787797', 'MaxSG': '0.90', 'PE_Issue': '31.31'},
{'Code': '603270.SH', 'Name': '金帝转债', 'SGDate': '20260615', 'SGPrice': '100.00', 'SGCode': '754270', 'MaxSG': '0.00', 'PE_Issue': '0.00'},
{'Code': '603809.SH', 'Name': '豪26转债', 'SGDate': '20260615', 'SGPrice': '100.00', 'SGCode': '754809', 'MaxSG': '0.00', 'PE_Issue': '0.00'}]
```
