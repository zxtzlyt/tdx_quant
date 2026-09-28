<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1ctuhthaq5qmg/mindoc-1hlnuonsp0amo.html | 章节: 02-tqcenter-行情 -->
# 基础信息批量get_stock_info_batch

###  批量获取股票基本信息get_stock_info_batch

####  根据证券代码列表批量获取股票基本财务数据，含基础信息、股本、财务、每股指标、行业地域

```python
get_stock_info_batch(
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
| Name | Y | str | 证券名称 |
| Unit | Y | str | 交易单位 |
| VolBase | Y | str | 量比的基量 |
| MinPrice | Y | str | 最小价格变动 |
| XsFlag | Y | str | 价格小数位数 |
| Fz | Y | List[str] | 开收市时间（4 段，8 个元素） |
| DelayMin | Y | str | 延时分钟数 |
| QHVolBaseRate | Y | str | 期货期权的每手乘数 |
| HKVolBaseRate | Y | str | 港股/日股/新加坡股每手股数 |
| BelongHS300 | Y | str | 是否属于沪深300 |
| BelongHasKQZ | Y | str | 是否含可转债 |
| BelongRZRQ | Y | str | 是否是融资融券标的 |
| BelongHSGT | Y | str | 是否属于沪深股通 |
| IsHKGP | Y | str | 是否是港股 |
| IsQH | Y | str | 是否是期货 |
| IsQQ | Y | str | 是否是期权 |
| IsSTGP | Y | str | 是否是 ST 股票 |
| IsQuitGP | Y | str | 是否是退市整理板股票 |
| TodayDRFlag | Y | str | 当天是否有除权除息：1=分红, 2=送转股, 3=分红+送转股, 4=配股 |
| HSStockKind | Y | str | 沪深京品种类型：0=指数,1=A股主板,2=北证A股,3=创业板,4=科创板,5=B股,6=债券,7=基金,8=权证,9=其它,10=非沪深京品种 |
| ActiveCapital | Y | str | 流通股本(万股) |
| J_zgb | Y | str | 总股本(万股) |
| J_bg | Y | str | B股(万股) |
| J_hg | Y | str | H股(万股) |
| J_zzc | Y | str | 总资产(万元) |
| J_ldzc | Y | str | 流动资产(万元) |
| J_gdzc | Y | str | 固定资产(万元) |
| J_wxzc | Y | str | 无形资产(万元) |
| J_ldfz | Y | str | 流动负债(万元) |
| J_cqfz | Y | str | 少数股东权益(万元) |
| J_zbgjj | Y | str | 资本公积金(万元) |
| J_jzc | Y | str | 股东权益/净资产(万元) |
| J_yysy | Y | str | 营业收入(万元) |
| J_yycb | Y | str | 营业成本(万元) |
| J_yszk | Y | str | 应收账款(万元) |
| J_yyly | Y | str | 营业利润(万元) |
| J_tzsy | Y | str | 投资收益(万元) |
| J_jyxjl | Y | str | 经营现金净流量(万元) |
| J_zxjl | Y | str | 总现金净流量(万元) |
| J_ch | Y | str | 存货(万元) |
| J_lyze | Y | str | 利润总额(万元) |
| J_shly | Y | str | 税后利润(万元) |
| J_jly | Y | str | 净利润(万元) |
| J_wfply | Y | str | 未分配利润(万元) |
| J_jyl | Y | str | 净资产收益率(%) |
| J_mgwfp | Y | str | 每股未分配 |
| J_mgsy | Y | str | 每股收益（折算为全年） |
| J_mgsy2 | Y | str | 季报每股收益 |
| J_mggjj | Y | str | 每股公积金 |
| J_mgjzc | Y | str | 每股净资产 |
| J_mgjzc2 | Y | str | 季报每股净资产 |
| J_gdqyb | Y | str | 股东权益比 |
| J_gdrs | Y | str | 股东人数 |
| J_HalfYearFlag | Y | str | 报告期月份(3,6,9,12) |
| J_start | Y | str | 上市日期 |
| tdx_dycode | Y | str | 通达信地域代码 |
| tdx_dyname | Y | str | 通达信地域 |
| rs_hycode_sim | Y | str | 通达信行业代码 |
| rs_hyname | Y | str | 通达信行业 |
| blockzscode | Y | str | 所属的行业板块指数代码 |
| underly_setcode | Y | str | 标的市场代码（如 ETF 跟踪的指数市场） |
| underly_code | Y | str | 标的代码（如 ETF 跟踪的指数代码） |

> 外层结构为 {证券代码: {字段: 值}}，每个证券一条记录、键顺序与 stock_list 入参顺序一致。不同证券类型（股票/基金/债券/指数）只返回其中一部分字段。

####  接口使用

批量获取 600000.SH 与 688318.SH 的基本信息。

```python
info = tq.get_stock_info_batch(
stock_list=["600000.SH", "688318.SH"],
)
print(info)
```

####  数据样本

```json
{
"600000.SH": {
"ActiveCapital": "3330583.76",
"BelongHS300": "1",
"BelongHSGT": "1",
"Fz": ["570", "690", "780", "900", "900", "900", "900", "900"],
"HSStockKind": "1",
"J_HalfYearFlag": "3",
"J_gdrs": "151091.00",
"J_jly": "1786099.92",
"J_jyl": "2.14",
"J_jzc": "83377101.21",
"J_mgjzc": "22.63",
"J_mgsy": "2.15",
"J_start": "19991110",
"J_zgb": "3330583.76",
"J_zzc": "1030564714.91",
"Name": "浦发银行",
"Unit": "100",
"VolBase": "2915.68",
"XsFlag": "2",
"rs_hyname": "全国性银行",
"tdx_dyname": "上海板块"
},
"688318.SH": {
"ActiveCapital": "35856.73",
"BelongHS300": "0",
"BelongHSGT": "1",
"Fz": ["570", "690", "780", "900", "900", "900", "900", "900"],
"HSStockKind": "4",
"J_HalfYearFlag": "3",
"J_gdrs": "22145.00",
"J_jly": "3453.87",
"J_jyl": "0.89",
"J_jzc": "387189.61",
"J_mgjzc": "10.80",
"J_mgsy": "0.39",
"J_start": "20200427",
"J_zgb": "35856.73",
"J_zzc": "404451.56",
"Name": "财富趋势",
"Unit": "100",
"VolBase": "259.49",
"XsFlag": "2",
"rs_hyname": "软件服务",
"tdx_dyname": "深圳板块"
}
}
```
