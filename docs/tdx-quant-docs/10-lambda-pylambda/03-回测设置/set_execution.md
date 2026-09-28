<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hhoa58m7i93s/mindoc-1hhoae0q7sqok.html | 章节: 10-lambda-pylambda/03-回测设置 -->
# 设置执行方式set_execution

###  10.5 设置市价单回测成交机制

```python
set_execution(mode)
```

该函数只影响本地回测撮合。

参数：

| 参数 | 说明 |
| --- | --- |
| mode | 只能传字符串 "close" 或 "next_open" |

可选值：

| 值 | 说明 |
| --- | --- |
| "close" | 当前 bar 收盘价撮合 |
| "next_open" | 下一根 bar 开盘价撮合 |

使用要求：

  * 建议在 `init(context)` 中调用。
  * 当前 Lambda 默认成交机制为 `"next_open"`；用户不调用 `set_execution()` 时，市价单默认下一根 bar 开盘价成交。
  * `set_execution("next_open")` 会同时设置市价单延迟 1 根 bar，并在下一根 bar 使用 `open` 撮合。
  * `set_trade_delay(value)` 是低层延迟参数，只控制延迟 bar 数，不改变当前 execution 使用的成交价格字段。

示例：

```python
def init(context):
    context.stock = "000001.SZ"
    # "next_open"：下一根 bar 开盘价撮合（默认值）
    # "close"：当前 bar 收盘价撮合
    set_execution("next_open")

def handle_bar(context, bar_dict):
    order_target_percent(context.stock, 1)
```

**注意**
set_execution本身包含了set_trade_delay的默认设置。
set_execution 里面，close时delay=0,next_open时delay=1；所以会出现set_trade_delay后再设置set_execution时set_trade_delay会被覆盖掉。 建议如果要延迟信号，set_trade_delay在set_execution后面。
