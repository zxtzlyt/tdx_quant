<!-- source: https://help.tdx.com.cn/quant/docs/markdown/ctx.stock.md/mindoc-1cv85e8u9nb0c.html | 章节: 01-tqcenter-通用函数 -->

#  初始化initialize

```python
initialize(__file__) #所有策略连接通达信客户端都必须调用此函数进行初始化
```

###  调用方法:

```python
from tqcenter import tq

tq.initialize(__file__)
```

###  注意事项:

1.tqcenter本地客户端模式下，使用tq前需要调用这个函数进行初始化。
2."initialize"不可修改。
3.该函数用于初始化，任何一个策略都必须有该函数。
