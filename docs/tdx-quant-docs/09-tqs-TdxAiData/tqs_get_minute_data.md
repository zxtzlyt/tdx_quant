<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hjbidnohpjn4/mindoc-1hlseu05n86ek.html | 章节: 09-tqs-TdxAiData -->
# 分钟数据get_minute_data

###  获取指定日期分时数据 get_minute_data

####  根据单只股票代码和日期，获取指定交易日的分时数据

```python
get_minute_data(
    stock_code: str = "",
    date: str = "",
    field_list: Optional[Iterable[str]] = None
) -> Dict
```

####  输入参数

| 参数 | 是否必选 | 参数类型 | 参数说明 |
| --- | --- | --- | --- |
| stock_code | Y | str | 单只证券代码，例如 000001.SZ |
| date | Y | str | 查询日期，支持 YYYYMMDD 、 YYYY-MM-DD 或完整时间格式 |
| field_list | N | Iterable[str] / None | 返回字段筛选，传 None 或空列表时返回全部字段 |

####  参数说明

  * `stock_code` 只支持传入单只证券代码，不传股票列表。
  * 股票代码需要带市场后缀，例如：
    * `000001.SZ`
    * `600000.SH`
    * `688318.SH`
  * `date` 支持以下格式：

```text
20260821
2026-08-21
2026-08-21 00:00:00
```

  * `field_list` 不传、传 `None` 或传空列表时，返回全部字段。
  * `field_list` 非空时，只返回指定字段。
  * 字段名称区分大小写，应使用接口返回的原始字段名。

####  返回数据

返回 `dict`，当前实际返回字段如下：

```text
Average
Price
Time
Volume
```

| 数据字段 | 数据类型 | 数据说明 |
| --- | --- | --- |
| Time | List[str] | 分时数据时间，格式通常为 HHMMSS |
| Price | List[str] | 分时成交价格 |
| Average | List[str] | 分时均价 |
| Volume | List[str] | 分时成交量 |

  * `Time`、`Price`、`Average`、`Volume` 是并行数组。
  * 同一数组下标的数据属于同一条分时记录。

####  接口使用

> 获取 `000001.SZ` 在 `2026-08-21` 的全部分时数据。

```python
from tdxaidata import tqs

minute_data = tqs.get_minute_data(
    stock_code="000001.SZ",
    date="2026-08-21",
)

print(minute_data)
```

####  字段筛选使用

> 获取 `000001.SZ` 在 `2026-08-21` 的分时时间和价格。

```python
from tdxaidata import tqs

minute_data = tqs.get_minute_data(
    stock_code="000001.SZ",
    date="2026-08-21",
    field_list=["Time", "Price"],
)

print(minute_data)
```

####  数据样本

```python
{
    "Average": [
        "11.39",
        "11.39",
        "11.39"
    ],
    "Price": [
        "11.36",
        "11.36",
        "11.37"
    ],
    "Time": [
        "093000",
        "093100",
        "093200"
    ],
    "Volume": [
        "3049",
        "1737",
        "1547"
    ]
}
```

####  注意事项

  * 返回数据是否完整取决于指定股票和日期是否有可用分时数据。
  * 日期不是交易日、股票代码无效或服务端没有数据时，可能返回空结果。
