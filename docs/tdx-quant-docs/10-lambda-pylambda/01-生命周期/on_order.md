<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hho9d546pbhc/mindoc-1hib55063ha7o.html | 章节: 10-lambda-pylambda/01-生命周期 -->
# 订单回调on_order

###  委托回调函数 on_order

```python
def on_order(context, order):
    pass
```

用途：

  * 用于在委托状态更新后进行回调。

参数说明：
`order: Order对象，包含订单详情。`
