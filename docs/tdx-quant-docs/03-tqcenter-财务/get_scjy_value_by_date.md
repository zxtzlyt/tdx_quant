<!-- source: https://help.tdx.com.cn/quant/docs/markdown/TdxQuant.md/mindoc-1h10pe678ta04.html | 章节: 03-tqcenter-财务 -->

#  获取指定日期市场交易数据get_scjy_value_by_date

###  获取指定时间的市场交易数据，需要先在客户端中下载股票数据包

```python
get_scjy_value_by_date(field_list: List[str] = [],
                       year: int = 0,
                       mmdd: int = 0) -> Dict:
```

###  输入参数

| 参数 | 是否必选 | 参数类型 | 参数说明 |
| --- | --- | --- | --- |
| field_list | Y | List[str] | 字段筛选，不能为空 |
| year | Y | int | 指定年份 |
| mmdd | Y | int | 指定月日 |

  * 如果year为0,mmdd为0,表示最新数据,mmdd为1,2,3...,表示倒数第2,3,4...个数据。
  * 需要先在客户端中下载股票数据包

###  输出数据

同get_scjy_value一样。

###  接口使用

```python
from tqcenter import tq

tq.initialize(__file__)

sc_one = tq.get_scjy_value_by_date(field_list=['SC6','SC7','SC8','SC9','SC10'],year=0,mmdd=0)
print(sc_one)
```

###  数据样本

```text
{'SC10': ['0.00', '181415.13'], 'SC6': ['-30479.00', '0.00'], 'SC7': ['-26449.00', '0.00'], 'SC8': ['31752.86', '84.22'], 'SC9': ['993000.00', '2900.00']}
```
