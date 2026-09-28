<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hi3n0rqkakt4/mindoc-1hi3n4r9e6cpo.html | 章节: 10-lambda-pylambda/05-特有行情 -->
# 中证高管持股列表get_zzgz_stocklist

###  获取中证国证成份股

```python
get_zzgz_stocklist(index_code, setcode=None, list_type=0)
```

说明：
1.`get_zzgz_stocklist`用于查询中证/国证等指数成份股。

示例：

```python
zz = get_zzgz_stocklist("000171", setcode=62)
gz = get_zzgz_stocklist("399303.CNI", list_type=1)
```
