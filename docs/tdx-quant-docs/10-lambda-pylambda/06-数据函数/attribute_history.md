<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hhoaleti08f0/mindoc-1hhoarm6i3eek.html | 章节: 10-lambda-pylambda/06-数据函数 -->
# 属性历史attribute_history

###  获取单个标的的多个字段历史数据

```python
attribute_history(
    security,
    count,
    unit="1d",
    fields=None,
    skip_paused=True,
    df=True,
    fq="pre",
)
```

示例：

```python
hist = attribute_history("000001.SZ", 5, "1d", ["open", "close", "volume"])
ma5 = hist["close"].mean()
```
