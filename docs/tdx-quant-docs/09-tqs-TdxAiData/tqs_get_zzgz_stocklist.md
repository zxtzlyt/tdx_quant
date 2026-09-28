<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hjbidnohpjn4/mindoc-1hlseuoousuvo.html | 章节: 09-tqs-TdxAiData -->
# 中证高管持股股票列表get_zzgz_stocklist

###  获取指数成分股get_zzgz_stocklist

####  根据指数代码，获取指定指数的成分股列表

```python
get_zzgz_stocklist(
    index_code: str = "",
    list_type: int = 0
) -> List
```

####  输入参数

| 参数 | 是否必选 | 参数类型 | 参数说明 |
| --- | --- | --- | --- |
| index_code | Y | str | 指数代码，例如 000300.SH |
| list_type | N | int | 成分股返回类型，默认值为 0 |

####  参数说明

  * `index_code` 必须传入指数代码，不能为空。支持沪(SH)，深(SZ)，京(BJ)，中证(CSI)和国证(CNI)等类型的指数。
  * 指数代码建议带市场后缀，例如：

```text
399001.SZ
000905.SH
000510.SH
000852.SH
899050.BJ
932000.CSI
980112.CNI
```

  * `list_type` 默认值为0，如果为1则表示返回证券名称。

```python
get_zzgz_stocklist(
    index_code="000300.SH",
    list_type=0,
)
```

可以返回沪深 300 成分股代码列表。

####  返回数据

返回列表中的股票代码带市场后缀，例如：

```text
000001.SZ
000002.SZ
000063.SZ
600000.SH
```

####  接口使用

> 获取沪深 300 指数 `000300.SH` 的成分股列表。

```python
from tdxaidata import tqs

stock_list = tqs.get_zzgz_stocklist(
    index_code="000300.SH",
    list_type=0,
)

print(stock_list)
```

####  数据样本

```python
[
    "000001.SZ",
    "000002.SZ",
    "000063.SZ",
    "000100.SZ",
    "000157.SZ",
    "000166.SZ",
    "000301.SZ",
    "000333.SZ",
    "000338.SZ",
    "000408.SZ"
]
```

####  实际返回说明

使用以下参数进行实际验证：

```python
tqs.get_zzgz_stocklist(
    index_code="000300.SH",
    list_type=0,
)
```

实际返回：

```text
返回类型：list
返回数量：300
```

####  注意事项

  * `index_code` 不能为空。
  * `list_type` 必须为整数。
  * 指数代码无效、指数市场不支持或服务端没有数据时，可能返回空列表或空对象。
