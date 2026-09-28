<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1h3hrvkp4sc0g/mindoc-1hce356csmgmo.html | 章节: 06-tqcenter-公式 -->

#  获取指定公式信息formula_get_info

###  获取指定公式信息

```python
def formula_get_info(formula_type: int = 0, formula_code: str = ''):
```

###  输入参数

| 参数 | 是否必选 | 参数类型 | 参数说明 |
| --- | --- | --- | --- |
| formula_type | Y | int | 公式种类标识 |
| formula_code | Y | int | 公式代码 |

  * 0 技术指标公式 1 条件选股公式 2 专家系统公式

###  输出数据

| 名称 | 类型 | 数值 | 说明 |
| --- | --- | --- | --- |
| acCode | Y | str | 公式代码 |
| acName | Y | str | 公式名称 |
| isSys | Y | int | 是否为系统公式 |
| ParaNum | Y | int | 入参数量 |
| Para | Y | Set | 公式入参参数 |
| ParaName | Y | Set | 公式入参名称 |
| Min | Y | Set | 公式入参最小值 |
| Max | Y | Set | 公式入参最大值 |
| Default | Y | Set | 公式入参默认值 |
| LineNum | Y | int | 出参数量 |
| Line | Y | Set | 公式出参参数 |
| LineName | Y | Set | 公式出参名称 |

###  接口使用

```python
from tqcenter import tq

tq.initialize(__file__)
formule_all = tq.formula_get_all(formula_type=0)
print(formule_all)
```

###  数据样本

```text
{'acCode': 'MACD',
'acName': '平滑异同平均线',
'isSys': 1,
'ParaNum': 3,
'Para': [
{'ParaName': 'SHORT','Min': '2.0000','Max': '200.0000','Default': '12.0000'},
{'ParaName': 'LONG','Min': '2.0000', 'Max': '200.0000', 'Default': '26.0000'},
{'ParaName': 'MID', 'Min': '2.0000', 'Max': '200.0000', 'Default': '9.0000'}],
'LineNum': 3,
'Line': [{'LineName': 'DIF'}, {'LineName': 'DEA'}, {'LineName': 'MACD'}]}
```
