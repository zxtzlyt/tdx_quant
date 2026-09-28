<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1h139a4ckchkk/mindoc-1h10sbcnl1c94.html | 章节: 04-tqcenter-板块与自选股 -->

#  清空自定义板块成份股

###  清空指定通达信客户端自定义板块的成份股

```python
clear_sector(block_code:str = ''):
```

###  输入参数

| 参数 | 是否必选 | 参数类型 | 参数说明 |
| --- | --- | --- | --- |
| block_code | Y | str | 自定义板块简称 |

###  接口使用

```python
from tqcenter import tq
tq.initialize(__file__)
clear_ptr = tq.clear_sector(block_code='CSBK')
print(clear_ptr)
```

###  数据样本

```text
{
   "Error" : "清空CSBK板块成功",
   "ErrorId" : "0",
   "run_id" : "1"
}
```
