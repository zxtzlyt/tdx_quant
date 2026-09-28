<!-- source: https://help.tdx.com.cn/quant/docs/markdown/ctx.stock.md/mindoc-1h10pqrdlj71o.html | 章节: 01-tqcenter-通用函数 -->

#  下载特定数据文件download_file

* * *

###  10大股东数据文件、ETF申赎清单文件、最近舆情信息文件、股票综合信息文件、经营分析数据文件、龙虎榜数据、限售解禁数据

```python
download_file(stock_code: str = '',
              down_time:str = '',
              down_type:int = 1):
```

###  输入参数

| 参数 | 是否必选 | 参数类型 | 参数说明 |
| --- | --- | --- | --- |
| stock_code | Y | List[str] | 证券代码 |
| down_time | Y | List[str] | 指定日期 |
| down_type | Y | List[str] | 指定下载类型 |

  * down_type=1时，下载10大股东数据文件，down_time为指定日期
  * down_type=2时，下载ETF申赎清单文件，down_time为指定日期
  * down_type=3时，下载最近舆情信息文件，不需要指定日期
  * down_type=4时，下载股票综合信息文件，不需要指定日期
  * down_type=5时，下载经营分析数据文件，down_time为指定日期
  * down_type=6时，下载最近的龙虎榜数据，不需要指定日期
  * down_type=7时，下载限售解禁数据，不需要指定日期
  *   * 下载的文件保存在 .\PYPlugins\data 文件夹
  * down_type=1时，下载的文件中含指定日期所在年度的所有10大股东数据和流通股东数据
  * down_type=5时，下载的文件中含指定日期所在年度的所有经营分析数据

###  接口使用

```python
from tqcenter import tq
tq.initialize(__file__)
# 下载10大股东数据
down_ptr_10 = tq.download_file(stock_code='688318.SH', down_time='20241231',down_type=1)
print(down_ptr_10)
# 下载ETF申赎数据
dowm_ptr_etf = tq.download_file(stock_code='159109.SH', down_time='20260227',down_type=2)
print(dowm_ptr_etf)
```

###  数据样本

```text
{
   "ErrorId" : "0",
   "Msg" : "下载十大股东数据[2025]成功。",
   "run_id" : "1"
}

{
   "ErrorId" : "0",
   "Msg" : "下载ETF申述清单[20250101]成功。",
   "run_id" : "1"
}
```
