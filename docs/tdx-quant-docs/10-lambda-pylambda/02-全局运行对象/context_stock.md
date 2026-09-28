<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hho9u0cbfe60/huicecontext.html | 章节: 10-lambda-pylambda/02-全局运行对象 -->
# context.stock

###  context上下文变量context.stock、context.universe的核心区别

`context.stock`
仅允许在 init(context) 内部做声明赋值，作为股票池输入入口。
支持单字符串 context.stock = "000001.SZ"，也支持列表 context.stock = ["000001.SZ","600000.SH"]
⚠️后续回调（handle_bar / before_trading_start）修改它无效，不会改变回测股票池。
⚠️不能写 context.stock = ["all"]，没有全市场魔法值；不赋值会直接抛 ValueError，回测直接报错终止。
`context.universe`
Lambda框架内部做：代码标准化、去重、合法性校验之后，输出的最终生效股票池。
init 执行完成之后才定稿，init内部访问context.universe不一定完整；
在handle_bar、before_trading_start、after_trading_end回调里面，业务代码、冒烟测试统一遍历 context.universe，不要用 context.stock。

```python
def init(context):
    # 仅在这里声明股票池
    context.stock = ["000001.SZ", "600000.SH"]

def handle_bar(context, bar_dict):
    # ❌不要 for sym in context.stock
    # ✅建议统一使用 universe
    for sym in context.universe:
        bar = bar_dict[sym]
```
