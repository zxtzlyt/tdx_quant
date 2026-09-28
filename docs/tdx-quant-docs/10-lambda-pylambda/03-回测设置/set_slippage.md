<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hhoa58m7i93s/mindoc-1hhoa91t58dgk.html | 章节: 10-lambda-pylambda/03-回测设置 -->
# 设置滑点set_slippage

###  设置滑点

```python
set_slippage(value)
```

兼容对象：

| 写法 | 说明 |
| --- | --- |
| set_slippage(0.001) | 原有写法，表示单边比例滑点 0.1%。 |
| PriceSlippage(value) | 【迁移兼容】比例滑点对象 |
| FixedSlippage(value) | 【迁移兼容】固定金额滑点对象 |
| set_slippage(PriceSlippage(0.02)) | 总买卖价差 2%，内部折算为买入上浮 1%、卖出下浮 1%。 |
| set_slippage(FixedSlippage(2.0)) | 总固定价差 2 元，内部折算为买入加 1 元、卖出减 1 元。 |

当前同步成交模式下已生效：

  * 买入成交价 = 当前价格 * `(1 + value)`。
  * 卖出成交价 = 当前价格 * `(1 - value)`。
  * `value` 不能为负数。

**示例1：**

```python
def init(context):
    context.stock = "000001.SZ"
    set_slippage(0.02)

def handle_bar(context, bar_dict):
    order_target_percent(context.stock, 0.2)
```

![](https://help.tdx.com.cn/quant/uploads/mindoc/images/m_16857291ada86445271a5372284162bb_r.png)

**示例1说明**
开盘价11.20，单边滑点儿2%，滑点值11.2*0.02=0.224 ，买入价 11.20+0.224=11.424

**示例2：**

```python
def init(context):
    context.stock = "000001.SZ"
    # 方式一：总买卖价差 2%，内部折算为买入+1%、卖出-1%
    set_slippage(PriceSlippage(0.02))
    # 方式二：总固定价差 2 元，内部折算为买入+1元、卖出-1元
    # set_slippage(FixedSlippage(2.0))

def handle_bar(context, bar_dict):
    order_target_percent(context.stock, 1)
```

**示例2说明**
![](https://help.tdx.com.cn/quant/uploads/mindoc/images/m_a320eb6fd83e772af23afa0d1e729206_r.png)
开盘价11.20，双边2%，折算单边1%，滑点值 11.20*0.01=0.112，买入价11.20+0.112=11.312

**示例3：**

```python
def init(context):
    context.stock = "000001.SZ"
    # 方式一：总买卖价差 2%，内部折算为买入+1%、卖出-1%
    # set_slippage(PriceSlippage(0.02))
    # 方式二：总固定价差 2 元，内部折算为买入+1元、卖出-1元
    set_slippage(FixedSlippage(2.0))

def handle_bar(context, bar_dict):
    order_target_percent(context.stock, 0.2)
```

**示例3说明：**
![](https://help.tdx.com.cn/quant/uploads/mindoc/images/m_260df422940273ae5dbd0607d632438e_r.png)
开盘价11.20，双边2，折算单边1，滑点值 1，买入价11.20+1=12.20
