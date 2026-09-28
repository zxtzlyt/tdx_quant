<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1ctuhthaq5qmg/mindoc-1h10hsiat36k4.html | 章节: 02-tqcenter-行情 -->

#  获取分红送配数据get_divid_factors

###  根据股票，获取指定时间段内的分红送配等数据

```python
get_divid_factors(stock_code: str,
                  start_time: str,
                  end_time: str) -> pd.DataFrame:
```

###  输入参数

| 参数 | 是否必选 | 参数类型 | 参数说明 |
| --- | --- | --- | --- |
| stock_code | Y | str | 证券代码 |
| start_time | N | str | 起始时间 |
| end_time | N | str | 结束时间 |

###  返回数据

| 数据 | 默认返回 | 数据类型 | 数据说明 |
| --- | --- | --- | --- |
| Type | Y | str | 类型 1:除权除息 11:扩缩股 15:重新调整 |
| Bonus | Y | str | 红利 |
| AlloPrice | Y | str | 配股价 |
| ShareBonus | Y | str | 送股/扩缩股比例 |
| Allotment | Y | str | 配股 |

###  接口使用

注：此接口只支持沪深京的分红送配数据

> 例如：获取688318.SH全部分红配送数据

```python
from tqcenter import tq
tq.initialize(__file__)
divid_factors = tq.get_divid_factors(
        stock_code='688318.SH',
        start_time='',
        end_time='')
print(divid_factors)
```

###  数据样本

```text
           Type  Bonus  AllotPrice  ShareBonus  Allotment
Date
2020-09-29    1    6.0         0.0         0.0        0.0
2021-05-27    1   10.0         0.0         0.0        0.0
2022-06-20    1   14.0         0.0         4.0        0.0
2023-06-13    1    5.0         0.0         4.0        0.0
2024-06-14    1    8.0         0.0         4.0        0.0
```
