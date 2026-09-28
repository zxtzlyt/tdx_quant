<!-- source: https://help.tdx.com.cn/quant/docs/markdown/TdxQuant.md/mindoc-1h10mdt617qss.html | 章节: 03-tqcenter-财务 -->

#  获取指定日期专业财务数据get_financial_data_by_date

###  根据股票，获取指定日期的专业财务数据，与基础财务数据不同，需要先在客户端中下载专业财务数据

```python
get_financial_data_by_date(stock_list: List[str] = [],
                           field_list: List[str] = [],
                           year: int = 0,
                           mmdd: int = 0) -> Dict:
```

###  输入参数

| 参数 | 是否必选 | 参数类型 | 参数说明 |
| --- | --- | --- | --- |
| stock_list | Y | List[str] | 证券代码列表 |
| field_list | Y | List[str] | 字段筛选，不能为空（如 FN193 ） |
| year | Y | int | 指定年份 |
| mmdd | Y | int | 指定月日 |

  * 如果year和mmdd都为0,表示最新的财报;
  * 如果year为0,mmdd为小于300的数字,表示最近一期向前推mmdd期的数据,如果是331,630,930,1231这些,表示最近一期的对应季报的数据;
  * 如果mmdd为0,year为一数字,表示最近一期向前推year年的同期数据;
  * 季报分界点为:0331,0630,0930,1231
  * 需要先在客户端中下载财务数据包

###  输出数据

同get_financial_data一样。

###  接口使用

```python
from tqcenter import tq

tq.initialize(__file__)

fd = tq.get_financial_data_by_date(
        stock_list=['688318.SH'],
        field_list=['Fn193','Fn194','Fn195','Fn196','Fn197'],
        year=0,
        mmdd=0)
print(fd)
```

###  数据样本

```text
{'600519.SH':
{'FN193': '162.47',
'FN194': '69.67',
'FN195': '16.07',
'FN196': '8.71',
'FN197': '25.14'}}
```
