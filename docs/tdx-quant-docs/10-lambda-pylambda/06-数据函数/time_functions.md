<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hhoaleti08f0/mindoc-1hhob071fp9s4.html | 章节: 10-lambda-pylambda/06-数据函数 -->
# 时间函数

###  时间函数

```python
get_datetime()
get_last_datetime()
```

说明：

  1. `get_datetime`用于获取当前bar的时间。
  2. `get_last_datetime`用于获取上一个bar的时间。

示例：

```python
now = get_datetime()
last_dt = get_last_datetime()
```
