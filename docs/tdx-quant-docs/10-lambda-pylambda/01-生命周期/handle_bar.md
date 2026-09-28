<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hho9d546pbhc/mindoc-1hho9jic0qbu8.html | 章节: 10-lambda-pylambda/01-生命周期 -->
# K线回调handle_bar

###  Bar 回调函数

```python
def handle_bar(context, bar_dict):
    pass
```

用途：

  * 每个回测时间点执行策略逻辑。
  * 读取当前 bar 行情。
  * 查询历史行情。
  * 发出下单指令。
  * 记录自定义指标。

`bar_dict` 是当前时间点的行情字典，key 是证券代码，value 是 `Bar` 对象。

示例：

```python
def handle_bar(context, bar_dict):
    price = bar_dict["000001.SZ"].close
    record(price=price)
```

兼容`handle_data(context, data)`函数名
