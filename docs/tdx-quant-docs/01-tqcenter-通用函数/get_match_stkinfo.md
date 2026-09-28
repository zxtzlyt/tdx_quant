<!-- source: https://help.tdx.com.cn/quant/docs/markdown/ctx.stock.md/mindoc-1hdguaia2v4bo.html | 章节: 01-tqcenter-通用函数 -->

#  检索证券信息get_match_stkinfo

###  检索证券信息

```python
def get_match_stkinfo(key_word:str = ''):
```

###  输入参数

| 参数 | 是否必选 | 参数类型 | 参数说明 |
| --- | --- | --- | --- |
| key_word | Y | str | 关键词 |

###  输出数据

| 名称 | 类型 | 数值 | 说明 |
| --- | --- | --- | --- |
| Code | Y | str | 证券代码 |
| Name | Y | str | 证券名称 |

###  接口使用

```python
from tqcenter import tq
tq.initialize(__file__)
match_stkinfo = tq.get_match_stkinfo(key_word='通达信')
print(match_stkinfo)
```

###  数据样本

```text
[{'Code': '880515.SH', 'Name': '通达信88'},
{'Code': '880818.SH', 'Name': '通达信热股'},
{'Code': '688318.SH', 'Name': '财富趋势'}]
```
