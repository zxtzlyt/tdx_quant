<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hhoa58m7i93s/mindoc-1hhoajhqre804.html | 章节: 10-lambda-pylambda/03-回测设置 -->
# 性能分析enable_profile

###  开启轻量函数耗时统计

```python
enable_profile(func_list=None)
get_profile_stats()
```

参数和返回：

| API | 说明 |
| --- | --- |
| enable_profile() | 统计全部被 runner 调用的用户函数 |
| enable_profile(["handle_bar", "trade"]) | 只统计指定函数名 |
| get_profile_stats() | 返回当前进程内统计快照 |

**示例1：开启用户函数轻量耗时统计**

```python
def init(context):
    context.stock = "000001.SZ"
    enable_profile()

def handle_bar(context, bar_dict):
    order_target_percent(context.stock, 1)

def after_trading(context):
    stats = get_profile_stats()
    # 验证方法：看日志里 stats 是否有内容（非空字典）
    log.info(f"【profile统计】{stats}")
    if stats:
        for func_name, info in stats.items():
            log.info(f"  {func_name}: 调用{info.get('count', '?')}次, 耗时{info.get('time', '?')}")
    else:
        log.info("【profile统计】空，说明未生效")
```

**示例1说明**
enable_profile()时获取到的结果情况
![](https://help.tdx.com.cn/quant/uploads/mindoc/images/m_364dc6a5214be3164b8803b7a13e848e_r.png)
注释掉enable_profile()后
![](https://help.tdx.com.cn/quant/uploads/mindoc/images/m_7ae40c06beeefade53593cd056f2e6c8_r.png)
