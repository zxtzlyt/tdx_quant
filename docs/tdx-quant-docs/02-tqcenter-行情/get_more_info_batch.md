<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1ctuhthaq5qmg/mindoc-1hlnup4o0ei68.html | 章节: 02-tqcenter-行情 -->
# 扩展信息批量get_more_info_batch

###  批量获取股票更多信息get_more_info_batch

####  根据证券代码列表批量获取股票更多信息，含涨幅系列、主力资金、L2、封单、估值与期货相关字段

```python
get_more_info_batch(
stock_list: list[str] = [],
field_list: list[str] = [],
return_df: bool = False
) -> Dict
```

####  输入参数

| 参数 | 是否必选 | 参数类型 | 参数说明 |
| --- | --- | --- | --- |
| stock_list | Y | list[str] | 证券代码列表，须带市场后缀，例如 ["600000.SH", "688318.SH"] |
| field_list | N | list[str] | 指定返回字段，为空 [] 返回全部字段，未知字段静默忽略 |
| return_df | N | bool | 为 True 且已安装 pandas 时返回 DataFrame（行索引为证券代码），否则返回 dict |

####  返回数据

| 数据字段 | 默认返回 | 数据类型 | 数据说明 |
| --- | --- | --- | --- |
| HqDate | Y | str | 行情日期 |
| fHSL | Y | str | 换手率 |
| fLianB | Y | str | 量比 |
| Wtb | Y | str | 委比 |
| Zsz | Y | str | 总市值(亿) |
| Ltsz | Y | str | 流通市值(亿) |
| BetaValue | Y | str | 贝塔系数 |
| DynaPE | Y | str | 动态市盈率 |
| MorePE | Y | str | 市盈率（港股:动, 其他扩展:静） |
| StaticPE_TTM | Y | str | 市盈率(TTM) |
| DYRatio | Y | str | 股息率 |
| PB_MRQ | Y | str | 市净率(MRQ) |
| More_YJL | Y | str | ETF/LOF 溢价率 |
| FreeLtgb | Y | str | 自由流通股本(万) |
| Yield | Y | str | 应计利息(债券)/占款天数(回购) |
| MainBusiness | Y | str | 主营构成 |
| SafeValue | Y | str | 安全分 |
| ShineValue | Y | str | 亮点数 |
| ShapeValue | Y | str | 短期形态+中期形态+长期形态编号 |
| TPFlag | Y | str | 停牌标识 |
| ZTPrice | Y | str | 涨停价 |
| DTPrice | Y | str | 跌停价 |
| vzangsu | Y | str | 量涨速 |
| Fzhsl | Y | str | 分钟换手率 |
| FzAmo | Y | str | 2 分钟金额(万元) |
| VOpenZAF | Y | str | 抢筹涨幅 |
| OpenZAF | Y | str | 开盘涨幅 |
| ZAF | Y | str | 涨幅 |
| ZAFYesterday | Y | str | 昨日涨幅 |
| ZAFPre2D | Y | str | 前天涨幅 |
| ZAFPre5 | Y | str | 5 日涨幅 |
| ZAFPre10 | Y | str | 10 日涨幅 |
| ZAFPre20 | Y | str | 20 日涨幅 |
| ZAFPre30 | Y | str | 30 日涨幅 |
| ZAFPre60 | Y | str | 60 日涨幅 |
| ZAFYear | Y | str | 年初至今涨幅 |
| ZAFPreMyMonth | Y | str | 涨幅(本月来) |
| ZAFPreOneYear | Y | str | 涨幅(一年来) |
| Zjl | Y | str | 主买净额(万元) |
| Zjl_HB | Y | str | 主力净流入(万元) |
| TotalBVol | Y | str | 总买量 |
| TotalSVol | Y | str | 总卖量 |
| BCancel | Y | str | 总撤买量 |
| SCancel | Y | str | 总撤卖量 |
| L2TicNum | Y | str | L2 逐笔成交数 |
| L2OrderNum | Y | str | L2 逐笔委托数 |
| FCAmo | Y | str | 封单额(万元)，> 0为涨停 < 0为跌停 |
| FCb | Y | str | 封成比 |
| OpenAmo | Y | str | 开盘金额(万元) |
| OpenZTBuy | Y | str | 竞价涨停买入金额(万元) |
| OpenAmoPre1 | Y | str | 昨开盘金额(万元) |
| OpenVolPre1 | Y | str | 昨开盘量 |
| CJJEPre1 | Y | str | 昨成交额(万元) |
| CJJEPre3 | Y | str | 3 日成交额(万元) |
| FDEPre1 | Y | str | 昨封单额(万元) |
| FDEPre2 | Y | str | 前封单额(万元) |
| ZTGPNum | Y | str | 板块指数的涨停家数 |
| LastStartZT | Y | str | 几天 |
| LastZTHzNum | Y | str | 几板 |
| EverZTCount | Y | str | 连板天 |
| ConZAFDateNum | Y | str | 连涨天数 |
| YearZTDay | Y | str | 年涨停天数 |
| MA5Value | Y | str | 5 日均价 |
| HisHigh | Y | str | 52 周最高 |
| HisLow | Y | str | 52 周最低 |
| IPO_Price | Y | str | 发行价 |
| IsT0Fund | Y | str | 是否是 T+0 基金 |
| IsZCZGP | Y | str | 是否是注册制 A 股 |
| IsKzz | Y | str | 是否可转债 |
| Kzz_HSCode | Y | str | 可转债对应的正股代码 |
| QHMainYYMM | Y | str | 主力合约关联的月份(期货) |
| PreVolIn | Y | str | 昨持仓量（期货期权有效） |
| VolInStock | Y | str | 持仓量（期货期权有效） |
| ClearPrice | Y | str | 结算价（期货期权有效） |
| PreMinum | Y | str | 基差/溢价 |
| KfEarnMoney | Y | str | 扣非净利润(万元) |
| RDInputFee | Y | str | 研发费用(万元) |
| CashZJ | Y | str | 货币资金(万元) |
| PreReceiveZJ | Y | str | 合同负债(万元) |
| OtherQYJzc | Y | str | 其它权益工具(万元) |
| StaffNum | Y | str | 员工人数 |
| RecentGGJYDate | Y | str | 最近北上大额交易日 |
| RecentHGDate | Y | str | 最近回购预案日 |
| RecentIncentDate | Y | str | 最近股权激励预案日 |
| NoticeDate_Recent | Y | str | 最近业绩预告日 |
| RecentReleaseDate | Y | str | 最近解禁日 |
| RecentDZDate | Y | str | 最近定增日 |
| ReportDate | Y | str | 最近财报公告日期 |
| ZTDate_Recent | Y | str | 近 2 年最近涨停板日期 |
| DTDate_Recent | Y | str | 近 2 年最近跌停板日期 |
| TopDate_Recent | Y | str | 近 2 年最近龙虎榜日期 |
| StopJYDate_Recent | Y | str | 最近停牌日期 |

> 外层结构为 {证券代码: {字段: 值}}，每个证券一条记录、键顺序与 stock_list 入参顺序一致。不同证券、权限和数据包会导致部分字段缺失。

####  接口使用

批量获取 600000.SH 与 688318.SH 的更多信息。

```python
more = tq.get_more_info_batch(
stock_list=["600000.SH", "688318.SH"],
)
print(more)
```

####  数据样本

```json
{
"600000.SH": {
"BetaValue": "-0.20",
"ClearPrice": "0.00",
"DTPrice": "8.15",
"DynaPE": "4.23",
"HisHigh": "13.87",
"HisLow": "8.07",
"HqDate": "20260918",
"Ltsz": "3020.84",
"OpenZAF": "-0.11",
"PB_MRQ": "0.40",
"PreVolIn": "0",
"VolInStock": "0",
"Wtb": "28.37",
"ZAF": "0.11",
"ZAFPre5": "0.78",
"Zjl": "3385.66",
"Zjl_HB": "-1130.75",
"Zsz": "3020.84",
"ZTPrice": "9.97",
"fHSL": "0.16",
"fLianB": "0.74"
},
"688318.SH": {
"BetaValue": "2.10",
"ClearPrice": "0.00",
"DTPrice": "61.74",
"DynaPE": "208.98",
"HisHigh": "128.91",
"HisLow": "62.62",
"HqDate": "20260918",
"Ltsz": "288.72",
"OpenZAF": "1.84",
"PB_MRQ": "7.46",
"PreVolIn": "0",
"VolInStock": "0",
"Wtb": "-8.36",
"ZAF": "4.33",
"ZAFPre5": "4.44",
"Zjl": "448.85",
"Zjl_HB": "4803.78",
"Zsz": "288.72",
"ZTPrice": "92.62",
"fHSL": "1.66",
"fLianB": "0.96"
}
}
```
