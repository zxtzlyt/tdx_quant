<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1ctuhthaq5qmg/mindoc-1h84ec4p26qus.html | 章节: 02-tqcenter-行情 -->

#  获取股票所属板块

###  获取指定股票所属板块信息

```python
def get_relation(stock_code:str = ''):
```

###  输入参数

| 参数 | 是否必选 | 参数类型 | 参数说明 |
| --- | --- | --- | --- |
| stock_code | Y | str | 股票代码 |

###  返回数据

| 数据 | 默认返回 | 数据类型 | 数据说明 |
| --- | --- | --- | --- |
| BlockCode | Y | str | 板块代码 |
| BlockName | Y | str | 板块名称 |
| BlockType | Y | str | 板块类型 |
| GPNume | Y | str | 成份股数量 |

  * 没有板块代码的板块的BlockCode字段返回"0"

###  接口使用

```python
from tqcenter import tq
from tqcenter import tqconst
tq.initialize(__file__)

gp_block_res = tq.get_relation(stock_code='688318.SH')
print(gp_block_res)
```

###  数据样本

```text
[{'BlockCode': '881355.SH', 'BlockName': '软件服务', 'BlockType': '行业', 'GPNume': '234'},
{'BlockCode': '880218.SH', 'BlockName': '深圳板块', 'BlockType': '地区', 'GPNume': '427'},
{'BlockCode': '880592.SH', 'BlockName': '互联金融', 'BlockType': '概念', 'GPNume': '211'},
{'BlockCode': '880722.SH', 'BlockName': '华为鸿蒙', 'BlockType': '概念', 'GPNume': '262'},
{'BlockCode': '880916.SH', 'BlockName': '国产软件', 'BlockType': '概念', 'GPNume': '266'},
{'BlockCode': '880948.SH', 'BlockName': '人工智能', 'BlockType': '概念', 'GPNume': '1049'},
{'BlockCode': '880956.SH', 'BlockName': '腾讯概念', 'BlockType': '概念', 'GPNume': '295'},
{'BlockName': '沪股通标的', 'BlockType': '风格', 'GPNume': '1763'},
{'BlockName': '融资融券', 'BlockType': '风格', 'GPNume': '4354'},
{'BlockCode': '880805.SH', 'BlockName': '保险重仓', 'BlockType': '风格', 'GPNume': '200'},
{'BlockCode': '880878.SH', 'BlockName': '百元股', 'BlockType': '风格', 'GPNume': '220'},
{'BlockName': '中证500', 'BlockType': '指数', 'GPNume': '500'},
{'BlockName': '中证800', 'BlockType': '指数', 'GPNume': '800'},
{'BlockName': '上证380', 'BlockType': '指数', 'GPNume': '380'},
{'BlockName': '金融科技', 'BlockType': '指数', 'GPNume': '59'},
{'BlockName': '科创100', 'BlockType': '指数', 'GPNume': '100'},
{'BlockName': '科创信息', 'BlockType': '指数', 'GPNume': '50'}]
```
