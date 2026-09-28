<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hhoaleti08f0/mindoc-1hhoamu2bpbqk.html | 章节: 10-lambda-pylambda/06-数据函数 -->
# 批量K线get_bars_batch

###  批量获取多个标的的历史行情

```python
get_bars_batch(
    symbols,
    count=None,
    fields=None,
    frequency="1d",
    end_date=None,
    start_date=None,
    fq=None,
    skip_paused=False,
)
```

批量获取多个标的的历史行情，返回 `dict[str, DataFrame]`。

说明：

  * `symbols` 不能为空。
  * `count` 传入时必须大于 `0`。
  * 第一版复用 Python 层 `get_price` 遍历实现，不是 C++ 批量优化路径。
  * `fq` 默认 `None`，即不复权。当前样例数据和 TLambda 运行时下，部分复权日期查询存在耗时或卡住风险，批量因子链路先采用不复权稳定口径。

示例：

```python
bars = get_bars_batch(
    ["000001.SH", "600000.SH"],
    count=5,
    fields=["close", "volume"],
)

for symbol, frame in bars.items():
    print(symbol, frame.tail(1))
```
