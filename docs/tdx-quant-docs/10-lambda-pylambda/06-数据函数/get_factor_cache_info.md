<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hhoaleti08f0/mindoc-1hhoapc2dga88.html | 章节: 10-lambda-pylambda/06-数据函数 -->
# 因子缓存信息get_factor_cache_info

###  因子缓存辅助

```python
clear_factor_cache(reset_stats=False)
get_factor_cache_info()
```

说明：

  * `calc_factor_batch` 默认启用当前 bar 内缓存，同一 bar 内相同股票池、因子、周期、窗口和复权参数的重复调用会直接返回缓存副本。
  * 缓存在每根 bar 推进时自动清空，不跨 bar、不跨日期复用，避免未来函数和动态复权口径问题。
  * `clear_factor_cache(reset_stats=True)` 可手动清空缓存并重置命中统计。
  * `get_factor_cache_info()` 返回 `size / hits / misses`，主要用于调试和性能排查。

示例：

```python
clear_factor_cache(reset_stats=True)
f1 = calc_factor_batch(["600000.SH"], ["return", "ma"], count=5)
f2 = calc_factor_batch(["600000.SH"], ["return", "ma"], count=5)
info = get_factor_cache_info()
assert info["hits"] >= 1
```
