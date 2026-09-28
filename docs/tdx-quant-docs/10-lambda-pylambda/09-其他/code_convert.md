<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hho7blr2j340/mindoc-1hibfhi6jhlqs.html | 章节: 10-lambda-pylambda/09-其他 -->
# 代码转换函数

###  统一证券代码格式

```python
normalize_symbol(symbol)
```

说明：
将不同格式的股票或基金代码，转换为`Lambda`平台的标准格式代码。

###  公开证券代码转 Lambda 底层代码

```python
to_internal_code(symbol)
```

说明：
将`Lambda`平台的标准格式代码转成`Lambda`底层格式代码，通常用于绑定`KData`。

例如：

```python
def handle_bar(context, bar_dict):
    ma5 = MA(CLOSE, 5)
    ma10 = MA(CLOSE(), 10)
    buy_signal = CROSS(ma5, ma10)
    price_filter = CLOSE > ma5

    # 需要读取 MACD 三个结果序列时，先绑定 KData，再按结果序号访问。
    stock = sm[to_internal_code(context.stock)]
    kdata = stock.get_kdata(Query(Datetime(202606100000), Datetime(202607090000), Query.DAY))
    macd = MACD(CLOSE, 12, 26, 9)(kdata)
    dif = macd.get_result(0)
    dea = macd.get_result(1)
    bar = macd.get_result(2)
```

###  Lambda 底层代码转公开证券代码

```python
from_internal_code(symbol)
```

说明：
将`Lambda`底层格式代码转成`Lambda`平台的标准格式代码。
