<!-- source: https://help.tdx.com.cn/quant/docs/markdown/ctx.stock.md/mindoc-1h1137r4k2mas.html | 章节: 01-tqcenter-通用函数 -->

#  获得订阅列表get_subscribe_hq_stock_list

###  获得当前策略订阅的股票列表

```python
get_subscribe_hq_stock_list():
```

###  接口使用

```python
from tqcenter import tq

tq.initialize(__file__)

sub_list = tq.get_subscribe_hq_stock_list()
print(sub_list)
```

###  数据样本

```text
['600519.SH']
```
