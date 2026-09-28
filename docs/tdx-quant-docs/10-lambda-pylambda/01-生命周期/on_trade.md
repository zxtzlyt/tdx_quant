<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hho9d546pbhc/mindoc-1hib60s1q4hbg.html | 章节: 10-lambda-pylambda/01-生命周期 -->
# 成交回调on_trade

###  委托回调函数 on_trade

```python
def on_trade(context, trade):
    pass
```

用途：

  * 用于在有成交后进行回调。

参数说明：

  * trade: Trade对象，包含成交详情。

**策略完整生命周期函数示例1**

```python
STOCKS = ["000001.SZ", "600000.SH"]
TEST_CASE = "T03"
STRATEGY_NAME = "smoke_timing_priority.py"
START_DATE = "20260701"
END_DATE = "20260710"
CALLED = []

def _emit(api, ok, value):
    log.info("[API_COVERAGE] %s ok=%s preview=%s" % (api, ok, value))
    record(test_case=TEST_CASE, strategy_name=STRATEGY_NAME, api=api, ok=ok, rows=1, preview=str(value)[:300])

# ===================== 原版主回调函数 =====================
def init(context):
    set_execution("close")
    context.stock = STOCKS
    CALLED.append("init")
    log.info("T03 called init")
    # init预先初始化交易标记，规避hasattr
    context._traded = False

def before_trading(context):
    CALLED.append("before_trading")
    log.info("T03 called before_trading")

def handle_bar(context, bar_dict):
    CALLED.append("handle_bar")
    log.info("T03 called handle_bar")
    # 仅做一次下单，目的：触发 on_order / on_trade 回调，不做业务逻辑
    if not context._traded:
        context._traded = True
        order_target_percent("000001.SZ", 0.2)

def handle_tick(context, tick):
    CALLED.append("handle_tick")
    log.info("T03 called handle_tick")

def after_trading(context):
    CALLED.append("after_trading")
    log.info("T03 called after_trading")

def on_order(context, order):
    CALLED.append("on_order")
    log.info("T03 called on_order")

def on_trade(context, trade):
    CALLED.append("on_trade")
    log.info("T03 called on_trade")

# ===================== 迁移兼容别名（全部同时定义） =====================
def initialize(context):
    context.stock = STOCKS
    CALLED.append("initialize")
    log.info("T03 called initialize【别名，不应执行】")

def before_trading_start(context):
    CALLED.append("before_trading_start")
    log.info("T03 called before_trading_start【别名，不应执行】")

def handle_data(context, data):
    CALLED.append("handle_data")
    log.info("T03 called handle_data【别名，不应执行】")

def after_trading_end(context):
    CALLED.append("after_trading_end")
    log.info("T03 called after_trading_end【别名，不应执行】")

# ===================== 回测结束，统一断言校验 =====================
def on_strategy_end(context):
    _emit("on_strategy_end", 1, "done")

    # 1. 原版主生命周期函数应当被调用
    assert "init" in CALLED,           "init 必须被调用"
    assert "before_trading" in CALLED, "before_trading 必须被调用"
    assert "after_trading" in CALLED,  "after_trading 必须被调用"
    assert ("handle_bar" in CALLED) or ("handle_tick" in CALLED), "handle_bar / handle_tick 至少一个触发"

    # 2. 有主函数存在，对应的兼容别名禁止执行
    assert "initialize" not in CALLED,           "init存在 → initialize别名不应执行"
    assert "before_trading_start" not in CALLED, "before_trading存在 → before_trading_start不应执行"
    assert "handle_data" not in CALLED,          "handle_bar存在 → handle_data不应执行"
    assert "after_trading_end" not in CALLED,    "after_trading存在 → after_trading_end不应执行"

    # 3. 下单后，订单、成交回调必须被触发
    assert "on_order" in CALLED,  "执行下单，on_order订单回调必须触发"
    assert "on_trade" in CALLED,  "执行下单，on_trade成交回调必须触发"

    _emit("T03_priority_check", 1, CALLED)
    log.info("==== T03 PASS, CALLED = %s ====", CALLED)
```

✅ 全部回调正常触发：
init → before_trading → handle_bar → on_order → on_trade
set_execution("close")生效，同一根 bar 内委托 + 成交一次性走完，不用跨 bar 等待撮合。
并且别名函数initialize / before_trading_start / handle_data / after_trading_end没有输出日志，证明：主函数存在时，别名被框架屏蔽，优先级规则生效。
当前 T03 用例全部校验点全部命中
✔ 原版生命周期函数全部调用
✔ 同名别名函数全部不执行（主函数优先）
✔ 下单触发 on_order 订单回调
✔ 收盘撮合，同步触发 on_trade 成交回调

**策略完整生命周期函数示例2**

```python
STOCKS = ["000001.SZ", "600000.SH"]
TEST_CASE = "T04"
STRATEGY_NAME = "smoke_alias_only.py"
START_DATE = "20260701"
END_DATE = "20260710"
CALLED = []

def _emit(api, ok, value):
    log.info("[API_COVERAGE] %s ok=%s preview=%s" % (api, ok, value))
    record(test_case=TEST_CASE, strategy_name=STRATEGY_NAME, api=api, ok=ok, rows=1, preview=str(value)[:300])

# ========== 只写迁移别名，不写原版主函数 init / handle_bar 等 ==========
def initialize(context):
    context.stock = STOCKS
    CALLED.append("initialize")
    log.info("T04 called initialize")
    context._traded = False
    set_execution("close")

def before_trading_start(context):
    CALLED.append("before_trading_start")
    log.info("T04 called before_trading_start")

def handle_data(context, data):
    CALLED.append("handle_data")
    log.info("T04 called handle_data")
    if not context._traded:
        context._traded = True
        order_target_percent("000001.SZ",0.2)

def after_trading_end(context):
    CALLED.append("after_trading_end")
    log.info("T04 called after_trading_end")

def on_order(context, order):
    CALLED.append("on_order")
    log.info("T04 called on_order")

def on_trade(context, trade):
    CALLED.append("on_trade")
    log.info("T04 called on_trade")

# ========== 回测结束断言：别名必须被调用 ==========
def on_strategy_end(context):
    _emit("on_strategy_end",1,"done")

    # 别名这套生命周期必须触发
    assert "initialize" in CALLED
    assert "before_trading_start" in CALLED
    assert "handle_data" in CALLED
    assert "after_trading_end" in CALLED

    # 订单、成交回调正常触发
    assert "on_order" in CALLED
    assert "on_trade" in CALLED

    _emit("T04_alias_check",1,CALLED)
    log.info("==== T04 PASS, CALLED = %s ====",CALLED)
```

🎉 日志显示 T04 完全 PASS
从日志CALLED列表：

```text
['initialize', 'before_trading_start', 'handle_data', 'on_order', 'on_trade', 'after_trading_end']
```

全部别名回调完整执行：
initialize ✔
before_trading_start ✔
handle_data ✔
after_trading_end ✔
订单回调on_order、成交回调on_trade也全部触发。
T03 + T04 合起来验证的两条核心规则
T03：原版主函数 + 别名同时存在 主函数优先执行，别名完全不调用
T04：只写别名，无原版主函数 别名正常接管全流程生命周期
