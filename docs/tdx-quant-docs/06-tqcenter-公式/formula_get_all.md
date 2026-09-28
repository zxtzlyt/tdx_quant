<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1h3hrvkp4sc0g/mindoc-1hce2u769tljc.html | 章节: 06-tqcenter-公式 -->

#  获取指定种类的公式列表formula_get_all

###  获取指定种类的公式列表

```python
def formula_get_all(formula_type: int = 0):
```

###  输入参数

| 参数 | 是否必选 | 参数类型 | 参数说明 |
| --- | --- | --- | --- |
| formula_type | Y | int | 公式种类标识 |

  * 0 技术指标公式 1 条件选股公式 2 专家系统公式

###  输出数据

| 名称 | 类型 | 数值 | 说明 |
| --- | --- | --- | --- |
| acCode | Y | str | 公式代码 |
| acName | Y | str | 公式名称 |
| isSys | Y | int | 是否为系统公式 |

###  接口使用

```python
from tqcenter import tq

tq.initialize(__file__)
formule_all = tq.formula_get_all(formula_type=0)
print(formule_all)
```

###  数据样本

```text
[{'acCode': 'MA', 'acName': '均线', 'isSys': 1},
{'acCode': 'MA2', 'acName': '均线', 'isSys': 1},
{'acCode': 'ABI', 'acName': '绝对广量指标', 'isSys': 1},
{'acCode': 'ADL', 'acName': '腾落指标', 'isSys': 1},
{'acCode': 'ADR', 'acName': '涨跌比率', 'isSys': 1},...]
```
