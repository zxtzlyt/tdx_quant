<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hhoa58m7i93s/mindoc-1hhoak9m7p5io.html | 章节: 10-lambda-pylambda/03-回测设置 -->
# 其他设置函数

###  其他设置函数

```python
set_trade_delay(value)
set_volume_limit(value)
set_volume_limit(daily=0.25, minute=0.5)
set_holding_stocks(holdings)
enable_open_bar()
set_log_level(level, is_limit=True, filename=None)
```

兼容补充：

  * `set_volume_limit(daily=..., minute=...)` 表示日线和分钟线使用不同的单 bar 最大成交比例；日线回测使用 `daily`，分钟回测使用 `minute`。
  * `set_holding_stocks({"600000.SH": 1000})` 设置初始持仓数量；也可写成 `{"600000.SH": {"amount": 1000, "price": 9.8}}` 指定初始成本价。当前初始持仓代码必须属于本次最终回测股票池，否则 `run_backtest` 会报错。
  * `enable_open_bar()` 只调整日线回测中 `handle_bar`、定时任务和下单看到的事件时间为 09:30，不额外生成开盘 K 线。

说明：

  * `set_volume_limit` 设置单个 bar 最大成交比例，取值范围为 `0` 到 `1`，`None` 表示关闭限制。
  * `set_trade_delay` 设置下单延迟成交规则；该函数不改变当前 execution 使用的成交价格字段。
  * `set_log_level` 设置日志级别；`filename` 非空时额外输出文件日志；`is_limit` 为兼容参数，当前只保存设置值。

当前同步成交模式下：

  * `set_volume_limit` 已按当前 bar 成交量限制最大成交数量。
  * 买入数量仍按 A 股 100 股整数倍处理。
  * `set_trade_delay` 已对市价单生效，`value > 0` 时订单会进入延迟撮合队列。

**示例1：set_trade_delay市价延迟设置**

```python
def init(context):
    context.stock = "000001.SZ"
    # 下单后延迟 2 根 bar 撮合（日线=2个交易日，分钟线=2分钟）
    set_execution("next_open")
    set_trade_delay(2)

def handle_bar(context, bar_dict):
    order(context.stock, 100)
```

**示例1说明**
运行结果是延迟两bar，开盘价成交。
![](https://help.tdx.com.cn/quant/uploads/mindoc/images/m_723c476a7877c14a3a3eba0ee2487175_r.png)

**示例2：set_volume_limit下单量限制设置**

```python
def init(context):
    set_execution("close")
    context.stock = "000001.SZ"
    # 方式一：单一比例
    set_volume_limit(0.00003)
    # 方式二：日线和分钟线分别设置
    # set_volume_limit(daily=0.00003, minute=0.005)

def handle_bar(context, bar_dict):
    order_target_percent(context.stock, 1)
```

**示例2说明**
买入下单量按照日线vol×0.00003×100变成股数，小于100的部分直接舍弃的原则决定单bar下单量。
![](https://help.tdx.com.cn/quant/uploads/mindoc/images/m_3f3a66e910196cd467ef4e1b83d96067_r.png)

分日线和分钟线设置的时候同理，根据回测周期自动选择设置的对应周期的设置得到下单量。

**示例3：set_holding_stocks设置初始持仓**

```python
def init(context):
    context.stock = "600000.SH"
    # 方式一：只设数量
    set_holding_stocks({"600000.SH": 1000})
    # 方式二：指定成本价
    # set_holding_stocks({"600000.SH": {"amount": 1000, "price": 9.8}})

def handle_bar(context, bar_dict):
    # 卖出全部初始持仓，查看交易明细中的卖出记录
    order_target_percent(context.stock, 0)
```

**示例3说明**
指定持仓后首根bar触发的信号在默认下开盘价下单模式下的成交明细。
![](https://help.tdx.com.cn/quant/uploads/mindoc/images/m_67417a356489cae46e4891fc4396c99a_r.png)

**示例4：set_log_level日志输出级别设置**

```python
def init(context):
    context.stock = "000001.SZ"
    # 只打印 warn 和 error 级别日志
    set_log_level(level="warn")

def handle_bar(context, bar_dict):
    log.info("这条日志不会显示（低于 warn 级别）")
    log.warn("这条会显示")
    order_target_percent(context.stock, 1)
```

**示例4说明**
回测日期区间两个bar，普通info级别的日志不显示
![](https://help.tdx.com.cn/quant/uploads/mindoc/images/m_dc5941c72c652ff832f8b9a255464a38_r.png)

| level 值 | 数字 | 说明 |
| --- | --- | --- |
| "DEBUG" | 10 | 最详细 |
| "INFO" | 20 | 默认级别 |
| "WARN" / "WARNING" | 30 | 警告以上 |
| "ERROR" | 40 | 错误以上 |
| "CRITICAL" / "FATAL" | 50 | 最高级别 |
| "NOTSET" | 0 | 不过滤 |

  * 字符串不区分大小写（内部 `upper()`）
