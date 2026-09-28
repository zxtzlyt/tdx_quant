<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1h139a4ckchkk/mindoc-1h10s7n863d50.html | 章节: 04-tqcenter-板块与自选股 -->

#  重命名自定义板块

###  重命名通达信客户端中的自定义板块

```python
rename_sector(block_code:str = '', block_name:str = ''):
```

###  输入参数

| 参数 | 是否必选 | 参数类型 | 参数说明 |
| --- | --- | --- | --- |
| block_code | Y | str | 自定义板块简称 |
| block_name | Y | str | 重命名后的自定义板块名称 |

###  接口使用

```python
from tqcenter import tq
tq.initialize(__file__)
rename_ptr = tq.rename_sector(block_code='CSBK', block_name='测试板块重命名')
print(rename_ptr)
```

###  数据样本

```text
{
   "Error" : "重命名CSBK板块成功",
   "ErrorId" : "0",
   "run_id" : "1"
}
```
