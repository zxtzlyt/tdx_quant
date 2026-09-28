<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hho9u0cbfe60/mindoc-1hhoahrgeati0.html | 章节: 10-lambda-pylambda/02-全局运行对象 -->
# context.params

###  context表单参数

```python
set_run_params(params=None, **kwargs)
get_run_params(clear=False)
```

平台可在用户策略代码前注入 `set_run_params(...)`，runner 会在本次回测或执行阶段信号任务启动时同步到 `context.params` 和 `g.params`。该参数是一次性 pending 状态；运行中再次调用只更新当前上下文，入口校验失败或任务结束后都会清理 pending 状态。

参数：

| API | 参数 | 说明 |
| --- | --- | --- |
| set_run_params | params | 参数字典，例如 {"fast": 5, "slow": 20} |
| set_run_params | **kwargs | 额外参数，会覆盖 params 中的同名 key |
| get_run_params | clear | 是否读取后清空待运行参数；普通用户策略不需要传 |

示例：参数读取：context.params.xxx

```python
# ====平台注入云表单参数====
set_run_params({"fast": 5, "slow": 20, "threshold": 0.02})

# ====用户策略代码====
def init(context):
    context.stock = ["000001.SZ", "600000.SH"]
    # 正确读取表单参数
    context.fast = context.params.fast
    context.slow = context.params.slow
    context.threshold = context.params.threshold
```
