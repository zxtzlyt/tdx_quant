<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hhoa58m7i93s/mindoc-1hhoa7gjbabuo.html | 章节: 10-lambda-pylambda/03-回测设置 -->
# 设置佣金set_commission

###  设置交易费用

如果init里面没有设置费用参数，默认给回测引擎送的默认参数open_tax=0.0,close_tax=0.0005, open_commission=0.0003,close_commission=0.0003,min_commission=5.0；如果回测希望不收取费用可以显示设置如下。

```python
set_commission(
    open_tax=0.0,
    close_tax=0,
    open_commission=0,
    close_commission=0,
    min_commission=0,
)
```

默认参设置

```python
set_commission(
    open_tax=0.0,
    close_tax=0.001,
    open_commission=0.0003,
    close_commission=0.0003,
    min_commission=5.0,
)
```

注意过户费默认万分之0.1双边怎么设置都会有，已经内置好无法修改和去掉。
参数：

| 参数 | 说明 |
| --- | --- |
| open_tax | 买入印花税 |
| close_tax | 卖出印花税 |
| open_commission | 买入佣金 |
| close_commission | 卖出佣金 |
| min_commission | 单笔最低佣金 |

兼容对象：

```python
set_commission(PerShare(type="stock", cost=0.0003, min_trade_cost=5.0))
set_commission(PerTrade(type="stock", cost=5.0))
```

| 对象 | 说明 |
| --- | --- |
| PerShare(type="stock", cost=0.0003, min_trade_cost=5.0) | 按成交金额比例收取佣金。 type="stock" 时卖出侧默认保留 A 股印花税。 |
| PerTrade(type="stock", cost=5.0) | 按笔固定费用兼容对象。当前底层成本模型按最低佣金近似表达固定每笔费用。 |

**示例1：不设置用默认**

```python
def init(context):
    context.stock = ["000001.SZ"]
    set_benchmark("000300.SH")
    set_execution("close")
def handle_bar(context, bar_dict):
    for sym in context.stock:
        order_target_percent(sym,0.2)
```

**示例1说明：**
![](https://help.tdx.com.cn/quant/uploads/mindoc/images/m_d993c1d619296642524cd7265c5bd6c7_r.png)
100万初始资金的设置，调整股票目标仓位到总资产的20% 首次下单如图。没有设置费用，按照默认设置收取费用。
万三佣金：11.11 _18000_ 3/10000=59.994
万0.1的过户费11.11 _18000_ 0.1/10000=1.9998
两个合起来 59.994+ 1.9998=61.9938
买入手续费验证完成。

**示例2：按成交额比例收佣（万一，免5）**

```python
def init(context):
    context.stock = "000001.SZ"
    # 方式一：按成交额比例收佣（万一，免5）
    set_commission(PerShare(type="stock", cost=0.0001, min_trade_cost=0.0))
    # 方式二：按笔固定费用（每笔5元）
    # set_commission(PerTrade(type="stock", cost=5.0))

def handle_bar(context, bar_dict):
    order_target_percent(context.stock, 0.2)
```

**示例2说明：**

![](https://help.tdx.com.cn/quant/uploads/mindoc/images/m_0dc1a8f34e1c16217f48d2fc403eee75_r.png)
100万初始资金的设置，调整股票目标仓位到总资产的20% 首次下单如图。没有设置费用，按照默认设置收取费用。
万一佣金：11.20 _18000_ 1/10000=20.16
万0.1的过户费11.20 _18000_ 0.1/10000=2.016
两个合起来 20.16+ 2.016=22.176
默认次日开盘下单手续费验证完成。

**示例3：按笔固定费用（每笔5元）**

```python
def init(context):
    context.stock = "000001.SZ"
    # 方式一：按成交额比例收佣（万一，免5）
    # set_commission(PerShare(type="stock", cost=0.0001, min_trade_cost=0.0))
    # 方式二：按笔固定费用（每笔5元）
    set_commission(PerTrade(type="stock", cost=5.0))

def handle_bar(context, bar_dict):
    order_target_percent(context.stock, 0.2)
```

**示例3说明**
![](https://help.tdx.com.cn/quant/uploads/mindoc/images/m_4dc8ddca4d91b4a2b786f791028dc6e4_r.png)
100万初始资金的设置，调整股票目标仓位到总资产的20% 首次下单如图。没有设置费用，按照默认设置收取费用。
佣金：固定5元
万0.1的过户费11.20 _18000_ 0.1/10000=2.016
两个合起来 5+ 2.016=7.016
默认次日开盘价下单手续费验证完成。

**示例4：按成交额比例收佣（万一，最小收固定5）**

```python
def init(context):
    context.stock = "000001.SZ"
    # 方式一：按成交额比例收佣（万一，免5）
    set_commission(PerShare(type="stock", cost=0.0001, min_trade_cost=5))
    # 方式二：按笔固定费用（每笔5元）
    # set_commission(PerTrade(type="stock", cost=5.0))

def handle_bar(context, bar_dict):
    order_target_percent(context.stock, 0.2)
```

![](https://help.tdx.com.cn/quant/uploads/mindoc/images/m_a65f97e9530cdbd701f53dad177e3081_r.png)
![](https://help.tdx.com.cn/quant/uploads/mindoc/images/m_2510c735d9069fe94e8fa2c2fbd14f11_r.png)
买入金额很小时收取固定费用5元和万分之0.1的的过户费
买入金额导致按照佣金率大于5元之后按照佣金率计算。
默认次日开盘价下单手续费验证完成。
