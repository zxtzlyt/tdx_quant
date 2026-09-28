<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hhoaleti08f0/mindoc-1hhoasuth0c00.html | 章节: 10-lambda-pylambda/06-数据函数 -->
# 原生指标MA/MACD

###  原生指标函数

Lambda提供了大量原生指标函数。用户策略里可以直接使用这些指标，不需要自己用pandas重写 `MA / MACD / CROSS`。

常用写法：

```python
def handle_bar(context, bar_dict):
    ma5 = MA(CLOSE, 5)
    ma10 = MA(CLOSE(), 10)
    buy_signal = CROSS(ma5, ma10)
    price_filter = CLOSE > ma5

    # 需要读取 MACD 三个结果序列时，先绑定 KData，再按结果序号访问。
    stock = sm[to_internal_code(context.stock)]
    kdata = stock.get_kdata(Query(Datetime(202606100000), Datetime(202607090000), Query.DAY))
    macd = MACD(CLOSE, 12, 26, 9)(kdata)
    dif = macd.get_result(0)
    dea = macd.get_result(1)
    bar = macd.get_result(2)
```

常用原生指标包括：

| 类别 | 函数 |
| --- | --- |
| 行情源指标 | KDATA 、 OPEN 、 HIGH 、 LOW 、 CLOSE 、 AMO 、 VOL |
| 均线和趋势 | MA 、 EMA 、 SMA 、 WMA 、 MACD |
| 交叉和引用 | CROSS 、 LONGCROSS 、 REF 、 BARSLAST 、 BARSCOUNT |
| 区间统计 | HHV 、 LLV 、 COUNT 、 SUM |
| 基础运算 | ABS 、 MAX 、 MIN 、 IF |

说明：

  * 这些函数底层复用原生 `Indicator`，不是 Python 层重新计算。
  * `CLOSE` 这类源指标既支持 `CLOSE()`，也支持作为参数直接写入 `MA(CLOSE, 5)`。

`注意`
**下面这段代码获取k线数据get_kdata获取的是所有当前股票最近的200根k，不管当前运行到哪个bar都是你运行这个策略真实时间的最近N根k。**

```python
def init(context):
    context.stock = "000001.SZ"
    set_benchmark("000300.SH")

def handle_bar(context, bar_dict):
    s = sm[context.stock]
    k = s.get_kdata(Query(-200))
```

`Query` 参数与枚举速查：

```python
Query(start=0, end=None, ktype=Query.DAY, recover_type=Query.NO_RECOVER)
```

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| start | int 或 Datetime | 0 | 起始索引或起始日期。 Query(-200) 表示最近 200 根 K 线； Query(Datetime(...), Datetime(...)) 表示按日期区间取数。 |
| end | int 、 Datetime 或 None | None | 结束索引或结束日期；应与 start 同类型。省略时按 start 的查询方式使用默认结束点。 |
| ktype | Query 周期枚举 | Query.DAY | K 线周期。 |

常用写法：

| 写法 | 含义 |
| --- | --- |
| Query(-200) | 最近 200 根K线 |
| Query(-200, ktype=Query.DAY) | 最近 200 根日线 |
| Query(-200, ktype=Query.MIN5) | 最近 200 根 5 分钟线 |
| Query(Datetime(202607010000), Datetime(202607200000), Query.DAY) | 取 2026-07-01 到 2026-07-20 的日线区间。 |

K 线周期枚举：

| 枚举 | 说明 |
| --- | --- |
| Query.DAY | 日线 |
| Query.WEEK | 周线 |
| Query.MONTH | 月线 |
| Query.QUARTER | 季线 |
| Query.HALFYEAR | 半年线 |
| Query.YEAR | 年线 |
| Query.MIN | 1 分钟线 |
| Query.MIN5 | 5 分钟线 |
| Query.MIN15 | 15 分钟线 |
| Query.MIN30 | 30 分钟线 |
| Query.MIN60 | 60 分钟线 |
| Query.HOUR2 | 2 小时线 |
| Query.HOUR4 | 4 小时线 |
| Query.HOUR6 | 6 小时线 |
| Query.HOUR12 | 12 小时线 |

**滚动计算ma金叉死叉策略**

```python
def init(context):
    set_benchmark("000300.SH")
    context.stock = "000001.SZ"

def handle_bar(context, bar_dict):
    hist = attribute_history(context.stock, 25, "1d", ["close"])
    if len(hist) < 25:
        return

    ma5 = hist["close"].rolling(5).mean()
    ma20 = hist["close"].rolling(20).mean()

    # 金叉
    buy = ma5.iloc[-2] <= ma20.iloc[-2] and ma5.iloc[-1] > ma20.iloc[-1]

    # 死叉
    sell = ma5.iloc[-2] >= ma20.iloc[-2] and ma5.iloc[-1] < ma20.iloc[-1]
    if buy:
        order_target_percent(context.stock, 1.0)
    elif sell:
        order_target_percent(context.stock, 0)

def after_trading(context):
    log.info("盘后运行结束")
```

**ma原生指标回测策略**

```python
def init(context):
    context.stock = "000001.SZ"
    set_benchmark("000300.SH")

def handle_bar(context, bar_dict):
    sym = context.stock
    # 必须先取 kdata
    kdata = sm[context.stock].get_kdata(Query(Datetime(202001010000), Datetime(202612310000), Query.DAY))
    if len(kdata) < 30:
        return

    # 第1步：定义指标
    ma5_ind = MA(CLOSE, 5)
    ma20_ind = MA(CLOSE, 20)

    # 第2步：用 kdata 计算
    ma5 = ma5_ind(kdata)
    ma20 = ma20_ind(kdata)

    # 金叉
    buy = CROSS(ma5_ind, ma20_ind)(kdata)

    # 死叉
    sell = CROSS(ma20_ind, ma5_ind)(kdata)

    dt = get_datetime()
    current_date = str(dt)[:10]

    i = -1
    for j in range(len(kdata)):
        kdate = str(kdata[j].datetime)[:10]
        if kdate <= current_date:
            i = j

    if i < 1:
        return

    buy_value = int(float(buy[i]) > 0)
    sell_value = int(float(sell[i]) > 0)

    pos = get_position(sym)
    amount = pos.amount if pos else 0

    if amount <= 0 and buy_value > 0:
        order_target_percent(sym, 0.8)
        log.info("MA金叉，买入满仓")

    elif amount > 0 and sell_value > 0:
        order_target_percent(sym, 0)
        log.info("MA死叉，卖出清仓")

    record(
        buy=buy_value,
        sell=sell_value,
    )

def after_trading(context):
    log.info("盘后运行结束")
```

**macd指标回测策略**

```python
def init(context):
    context.stock = "000001.SZ"
    set_benchmark("000300.SH")
    set_execution("close")

def handle_bar(context, bar_dict):
    sym = context.stock
    dt = get_datetime()

    stock = sm[to_internal_code(sym)]
    kdata = stock.get_kdata(
        Query(
            Datetime(202001010000),
            Datetime(202612310000),
            Query.DAY
        )
    )

    if len(kdata) < 35:
        return

    dif_ind = EMA(CLOSE, 12) - EMA(CLOSE, 26)
    dea_ind = EMA(dif_ind, 9)
    macd_ind = 2 * (dif_ind - dea_ind)

    dif = dif_ind(kdata)
    dea = dea_ind(kdata)
    macd = macd_ind(kdata)

    buy = CROSS(dif_ind, dea_ind)(kdata)
    sell = CROSS(dea_ind, dif_ind)(kdata)

    dt = get_datetime()
    current_date = str(dt)[:10]

    i = -1
    for j in range(len(kdata)):
        kdate = str(kdata[j].datetime)[:10]
        if kdate <= current_date:
            i = j

    if i < 1:
        return

    dif_value = float(dif[i])
    dea_value = float(dea[i])
    macd_value = float(macd[i])
    buy_value = int(float(buy[i]) > 0)
    sell_value = int(float(sell[i]) > 0)

    log.info(
        "当前日期=%s 信号日期=%s kdata_last=%s dif=%.4f dea=%.4f buy=%d sell=%d",
        dt,
        kdata[i].datetime,
        kdata[-1].datetime,
        dif_value,
        dea_value,
        buy_value,
        sell_value,
    )
    pos = get_position(sym)
    amount = pos.amount if pos else 0

    if amount <= 0 and buy_value > 0:
        order_target_percent(sym, 0.8)
        log.info("MACD金叉，买入满仓")

    elif amount > 0 and sell_value > 0:
        order_target_percent(sym, 0)
        log.info("MACD死叉，卖出清仓")

    record(
        dif=dif_value,
        dea=dea_value,
        macd=macd_value,
        buy=buy_value,
        sell=sell_value,
    )

def after_trading(context):
    log.info("盘后运行结束")
```

**原生指标ma金叉死叉版按当前bar取k，这用起来才更像指标原生写法，取k线技巧**

```python
def init(context):
   context.stock = "000001.SZ"
   set_benchmark("000300.SH")

def handle_bar(context, bar_dict):
   sym = context.stock
   # 必须先取 kdata
   # kdata = sm[context.stock].get_kdata(Query(-200))
   current_dt = get_datetime()
   end_dt = Datetime(current_dt.year, current_dt.month, current_dt.day,
                     current_dt.hour, current_dt.minute, current_dt.second, 0, 0)
   kdata = sm[context.stock].get_kdata(Query(Datetime(202001010000), end_dt, Query.DAY))

   if len(kdata) < 30:
       return

   # 第1步：定义指标
   ma5_ind = MA(CLOSE, 5)
   ma20_ind = MA(CLOSE, 20)

   # 第2步：用 kdata 计算
   ma5 = ma5_ind(kdata)
   ma20 = ma20_ind(kdata)

   # 金叉
   buy = CROSS(ma5_ind, ma20_ind)(kdata)
   # 死叉
   sell = CROSS(ma20_ind, ma5_ind)(kdata)

   # 只判断当前bar
   if buy[-1] > 0 :
       order_target_percent(context.stock, 1.0)
   elif sell[-1] > 0 :
       order_target_percent(context.stock, 0)

def after_trading(context):
   log.info("盘后运行结束")
```

**直接用cross构建金叉指标**

```python
def init(context):
    context.stock = "000001.SZ"
    set_benchmark("000300.SH")

def handle_bar(context, bar_dict):
    sym = context.stock
    # 必须先取 kdata
    # kdata = sm[context.stock].get_kdata(Query(-200))
    current_dt = get_datetime()
    end_dt = Datetime(current_dt.year, current_dt.month, current_dt.day,
                      current_dt.hour, current_dt.minute, current_dt.second, 0, 0)
    kdata = sm[context.stock].get_kdata(Query(Datetime(202001010000), end_dt, Query.DAY))

    if len(kdata) < 30:
        return

    # # 第1步：定义指标
    # ma5_ind = MA(CLOSE, 5)
    # ma20_ind = MA(CLOSE, 20)

    # # 第2步：用 kdata 计算
    # ma5 = ma5_ind(kdata)
    # ma20 = ma20_ind(kdata)

    # 金叉
    buy = CROSS(MA(CLOSE, 5),  MA(CLOSE, 20))(kdata)

    # 死叉
    sell = CROSS( MA(CLOSE, 20), MA(CLOSE, 5))(kdata)

    # 只判断当前bar
    if buy[-1] > 0 :
        order_target_percent(context.stock, 1.0)
    elif sell[-1] > 0 :
        order_target_percent(context.stock, 0)

def after_trading(context):
    log.info("盘后运行结束")
```
