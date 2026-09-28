<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hhoa58m7i93s/mindoc-1hhoaba3gefmg.html | 章节: 10-lambda-pylambda/03-回测设置 -->
# 设置选项set_option

###  设置通用回测选项

```python
set_option(name, value)
```

设置通用回测选项。
当前正式支持的 `name` 如下：

| name | 可选值 | 默认值 | 说明 |
| --- | --- | --- | --- |
| limit_order_expire_bars | None 或正整数 | None | 设置限价单未成交时最多保留的撮合 bar 数； None 表示不自动过期 |
| future_data_policy | "truncate" 或 "raise" | "truncate" | 策略查询时间超过当前策略时点时， truncate 截断到当前时点， raise 直接抛出异常；同时适用于行情和历史财务数据查询 |

**示例**

```python
set_option("limit_order_expire_bars", 3)
set_option("future_data_policy", "raise")
```

说明：

  * `set_option` 当前不会校验 `name` 是否在白名单中，传入未支持的名称虽然可能不会立即报错，但不会产生对应功能效果。

**示例1：限价单当前bar不成交，保留N根信号**

```python

def init(context):
    context.stock = "000001.SZ"
    context.bar_count = 0
    set_execution("close")
    # 限价单未成交时最多保留 3 根 bar，超时自动撤销
    set_option("limit_order_expire_bars", 3)

def handle_bar(context, bar_dict):
    context.bar_count += 1
    # 第1根bar挂一个不可能成交的限价单（市价的50%）
    if context.bar_count == 1:
        price = 11.13
        order(context.stock, 100,price=price)
        log.info(f"【第1根bar】挂限价单 {price:.2f}，等待3根bar过期自动撤销")
    elif context.bar_count == 5:
        log.info(f"【第5根bar】限价单应已在第4根bar自动撤销，查交易明细确认")
```

**示例1说明**
评测运行时间段：20260810-20260817 000001.SZ 20260810 前复权收盘价11.29
![](https://help.tdx.com.cn/quant/uploads/mindoc/images/m_1d98a0221767685b1339f9b465a5dfc7_r.png)
set_execution("close") 设置了当前根成交，限价价格低高于等于低于收盘价都不会在20260810下单。set_option("limit_order_expire_bars", 3)只要设置了，限价单只会从开始日期后的第一根bar之后才有交易。目前是限价单只能在回测开始日期之后的bar才能有信号，开始日期当前bar是不可能有信号的。

限价单未成交时最多保留 3 根 bar，依次为20260811[11.24,11.40] 、20260812[11.20,11.29]、20260813[11.18,11.27].（20260814[11.11,11.23]）
当能满足限价单在最近一根k价格区间以内的就会在最近一根k成交。
限价order(context.stock, 100,price=11.24) 在20260811 成交
![](https://help.tdx.com.cn/quant/uploads/mindoc/images/m_8a367f2a3437a10e1ee70db18202108b_r.png)
限价order(context.stock, 100,price=11.23) 在20260812 成交
![](https://help.tdx.com.cn/quant/uploads/mindoc/images/m_fcbee7b11b52c5ca182c5c753174dde1_r.png)
限价order(context.stock, 100,price=11.19) 在20260813 成交
![](https://help.tdx.com.cn/quant/uploads/mindoc/images/m_c370ff2e0beb4a4bf9b88fe492c9f201_r.png)
因为set_option("limit_order_expire_bars", 3)，即便是限价价格比如定位11.13在后面第4根20260814[11.11,11.23]价格内也无法下单成功了。

**注意**
限价下单如果不设置 set_option("limit_order_expire_bars", 3)相当于没设置限制，满足价格位置时累积bar的限价单都会集体触发。
限价单支持跨 bar 累积、按 `limit_order_expire_bars` 过期。
没设置limit_order_expire_bars是默认有价格满足时前面全部下单
![](https://help.tdx.com.cn/quant/uploads/mindoc/images/m_f67652157ed69d7fe4ea87a90a25e089_r.png)
此现象是限价单跨日累积导致的，不是日线 handle bar在同一天调用了多次。
当前执行顺序是:
1.撮合前几天遗留的未完成订单;
2.调用当天的 handle bar ;
3.代码每天都新建一张 100 股、11.1 元限价单;
4.默认 limit order expire bars=None ，未成交订单不会自动过期。
5.在20260717满足价格的时候前面bar累积的单子一起下单。

**示例2:开启未来数据抛出报错**

```python
def init(context):
    context.stock = "000001.SZ"
    # "raise" = 查询超过当前时间点的数据时抛异常（默认 "truncate" = 截断不报错）
    # set_option("future_data_policy", "raise")

def handle_bar(context, bar_dict):
    # 故意查询 end_date 超过当前时间的数据（未来数据）
    future_date = context.current_dt + timedelta(days=30)
    hist = get_price(
        context.stock,
        start_date=context.current_dt - timedelta(days=10),
        end_date=future_date,  # 超过当前时间 → 触发 future_data_policy
        frequency="1d",
        fields=["close"],
    )
    log.info(f"【查询结果】行数={len(hist)}，最后日期={hist.index[-1]}，当前时间={context.current_dt}")
    log.info(f"【截断判断】请求end={future_date}，实际end={hist.index[-1]}，{'已截断' if hist.index[-1] < future_date else '未截断'}")
    order_target_percent(context.stock, 1)

def after_trading(context):
    log.info(f"===== 总资产: {context.portfolio.total_value:.2f} =====")
```

**示例2说明**
当注释掉 set_option（默认 "truncate"）→ 静默截断到当前时间，不报错
![](https://help.tdx.com.cn/quant/uploads/mindoc/images/m_2ba171db5ff2412f48b8793d577e3fdd_r.png)
当set_option("future_data_policy", "raise")有效时 "raise" → end_date 超过当前时间会报错中断
![](https://help.tdx.com.cn/quant/uploads/mindoc/images/m_9bae52e15fea6aa6d137c13d29142824_r.png)
