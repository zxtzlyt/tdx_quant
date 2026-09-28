<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hhoaleti08f0/mindoc-1hhoaqrp4i0ic.html | 章节: 10-lambda-pylambda/06-数据函数 -->
# 历史数据history

###  获取多个标的的历史数据

```python
history(
    symbol_list,
    fields,
    bar_count,
    frequency="1d",
    skip_paused=False,
    fq="pre",
    df=True,
)
```

示例：

```python
close_df = history(
    ["000001.SZ", "600000.SH"],
    ["close"],
    20,
    "1d",
)
```
