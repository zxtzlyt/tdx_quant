<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1hjbidnohpjn4/mindoc-1hlsf0u13l0d4.html | 章节: 09-tqs-TdxAiData -->
# 订阅行情subscribe

###  订阅实时行情 subscribe

####  订阅指定股票的实时行情，通过回调函数接收真实行情数据，并可保存到本地文件

```python
subscribe(
    stock_list: List[str] = [],
    callback: Optional[Callable[[str], Any]] = None
) -> None
```

####  输入参数

| 参数 | 是否必选 | 参数类型 | 参数说明 |
| --- | --- | --- | --- |
| stock_list | Y | List[str] | 待订阅的证券代码列表 |
| callback | Y | Callable | 行情回调函数，接收一个行情数据字符串参数 |

  * `subscribe`接口必须传入`callback`回调函数

####  参数说明

  * `stock_list` 必须传入股票代码列表，不能为空。
  * 股票代码需要带市场后缀，例如：
    * `000001.SZ`
    * `600000.SH`
    * `600519.SH`
  * `callback` 必须是可调用对象。
  * 回调函数只接收一个参数：

```python
data: str
```

  * `data` 是底层行情服务返回的 JSON 字符串。
  * `subscribe` 调用成功后，行情数据会通过回调函数异步返回。
  * `subscribe` 本身不会返回行情数据。
  * 主程序需要持续运行，否则 Python 进程退出后将无法继续接收行情。
  * 取消订阅使用：

```python
unsubscribe(stock_list)
```

####  返回数据

`subscribe` 本身返回：

```python
None
```

实时行情通过回调函数返回，回调参数为 JSON 字符串。

实际回调数据的基本结构如下：

```json
{
    "Error": "",
    "ErrorId": 0,
    "ResultSets": [
        {
            "ColDes": [
                "code",
                "decimal",
                "price",
                "pre_close",
                "open",
                "high",
                "low",
                "refresh_time",
                "volume",
                "bond_match_price",
                "limit_up",
                "limit_down",
                "accrued_interest",
                "cage_up",
                "cage_down",
                "after_hours_flag",
                "tomorrow_limit_up",
                "tomorrow_limit_down",
                "sdunit_status",
                "seal_amount",
                "ask1",
                "ask2",
                "ask3",
                "ask4",
                "ask5",
                "ask_vol1",
                "ask_vol2",
                "ask_vol3",
                "ask_vol4",
                "ask_vol5",
                "bid1",
                "bid2",
                "bid3",
                "bid4",
                "bid5",
                "bid_vol1",
                "bid_vol2",
                "bid_vol3",
                "bid_vol4",
                "bid_vol5"
            ],
            "Content": [
                [
                    "000001.SZ",
                    2,
                    11.350,
                    11.400,
                    11.360,
                    11.430,
                    11.340,
                    95024,
                    155267,
                    0.0,
                    12.540,
                    10.260,
                    5.490,
                    11.590,
                    11.120,
                    0,
                    0.0,
                    0.0,
                    3,
                    0.0,
                    11.360,
                    11.370,
                    11.380,
                    11.390,
                    11.400,
                    343,
                    1043,
                    1276,
                    1396,
                    6887,
                    11.350,
                    11.340,
                    11.330,
                    11.320,
                    11.310,
                    1061,
                    2660,
                    4393,
                    4078,
                    5048
                ]
            ]
        }
    ]
}
```

####  返回字段

`ColDes` 是字段名数组，`Content` 是数据数组。

`Content` 中每一行数据与 `ColDes` 按相同下标对应。

| 字段 | 数据说明 |
| --- | --- |
| code | 证券代码 |
| decimal | 价格小数位数或价格精度 |
| price | 最新价 |
| pre_close | 昨收价 |
| open | 开盘价 |
| high | 最高价 |
| low | 最低价 |
| refresh_time | 行情刷新时间，通常为 HHMMSS 数字 |
| volume | 成交量 |
| bond_match_price | 债券匹配价格 |
| limit_up | 涨停价 |
| limit_down | 跌停价 |
| accrued_interest | 应计利息 |
| cage_up | 上限价格 |
| cage_down | 下限价格 |
| after_hours_flag | 盘后标志 |
| tomorrow_limit_up | 下一交易日涨停价 |
| tomorrow_limit_down | 下一交易日跌停价 |
| sdunit_status | 证券状态 |
| seal_amount | 封单金额 |
| ask1 ~ ask5 | 五档卖价 |
| ask_vol1 ~ ask_vol5 | 五档卖量 |
| bid1 ~ bid5 | 五档买价 |
| bid_vol1 ~ bid_vol5 | 五档买量 |

####  接口使用

> 订阅 `000001.SZ`、`600000.SH` 和 `600519.SH` 的实时行情，并持续运行 30 秒。

```python
import time

from tdxaidata import tqs

def on_quote(data: str) -> None:
    print("收到实时行情：")
    print(data)

stock_list = [
    "000001.SZ",
    "600000.SH",
    "600519.SH",
]

subscribed = False

try:
    tqs.subscribe(
        stock_list=stock_list,
        callback=on_quote,
    )
    subscribed = True

    print("订阅成功")
    print("当前订阅列表：")
    print(tqs.get_subscribe_hq_stock_list())

    time.sleep(30)

finally:
    if subscribed:
        tqs.unsubscribe(stock_list)
        print("已取消订阅")
```

####  解析回调数据

```python
import json

from tdxaidata import tqs

def on_quote(data: str) -> None:
    try:
        quote_data = json.loads(data)

        if quote_data.get("ErrorId") not in (0, "0", None):
            print("行情服务返回错误：", quote_data)
            return

        result_sets = quote_data.get("ResultSets", [])

        for result_set in result_sets:
            field_names = result_set.get("ColDes", [])
            content = result_set.get("Content", [])

            for row in content:
                quote = dict(zip(field_names, row))
                print(
                    quote.get("code"),
                    quote.get("price"),
                    quote.get("volume"),
                )

    except json.JSONDecodeError:
        print("回调数据不是有效 JSON：", data)
    except Exception as exc:
        print("解析行情回调失败：", exc)

stock_list = ["000001.SZ"]

try:
    tqs.subscribe(stock_list, on_quote)
    input("订阅已建立，按回车取消订阅...")
finally:
    tqs.unsubscribe(stock_list)
```

####  注意事项

  * `subscribe` 不会自动为业务程序创建永久运行逻辑。
  * 如果调用 `subscribe` 后程序没有其他阻塞逻辑，主线程执行结束后程序会退出。
  * 可以使用 `while True`、事件等待或其他业务循环保持程序运行。
  * `subscribe` 回调收到的是原始 JSON 字符串，不是已经转换好的字典。
  * 需要使用 `json.loads(data)` 将回调字符串解析为 Python 对象。
  * `Content` 中每行数据与 `ColDes` 按下标对应。
  * 行情回调可能在短时间内连续触发多次。
  * 回调函数不建议执行耗时计算、网络请求或长时间文件操作。
  * 保存数据时建议使用追加写入方式，避免覆盖之前的行情记录。
  * 策略程序必须保持运行，否则订阅会随 Python 进程退出而终止。
  * 程序退出前应调用 `unsubscribe` 释放订阅。
  * 当前底层取消订阅为全局取消订阅，即使传入部分股票，也可能取消全部底层订阅。
