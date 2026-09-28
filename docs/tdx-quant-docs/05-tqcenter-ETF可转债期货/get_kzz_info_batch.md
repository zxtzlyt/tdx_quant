<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1h13a594nhvb4/mindoc-1hlnuvdpvh6o4.html | 章节: 05-tqcenter-ETF可转债期货 -->
# 可转债信息批量get_kzz_info_batch

###  批量获取可转债基础信息get_kzz_info_batch

####  根据可转债代码列表批量获取可转债基础信息，含转股价、评级、赎回与回售条款、溢价率等

```python
get_kzz_info_batch(stock_list: list[str] = [], field_list: list[str] = [], return_df: bool = False
) -> Dict
```

####  输入参数

| 参数 | 是否必选 | 参数类型 | 参数说明 |
| --- | --- | --- | --- |
| stock_list | Y | list[str] | 可转债代码列表，须带市场后缀，例如 ["123071.SZ", "123072.SZ"] |
| field_list | N | list[str] | 指定返回字段，为空 [] 返回全部字段，未知字段静默忽略 |
| return_df | N | bool | 为 True 且已安装 pandas 时返回 DataFrame（行索引为证券代码），否则返回 dict |

####  返回数据

| 数据字段 | 默认返回 | 数据类型 | 数据说明 |
| --- | --- | --- | --- |
| KZZCode | Y | str | 可转债代码 |
| KZZName | Y | str | 可转债名称 |
| HSCode | Y | str | 正股代码 |
| HSName | Y | str | 正股名称 |
| SetCode | Y | str | 证券市场 |
| ZGPrice | Y | str | 转股价格 |
| CurRate | Y | str | 当期利率 |
| RestScope | Y | str | 剩余规模(万) |
| PutBack | Y | str | 回售触发价 |
| ForceRedeem | Y | str | 强赎触发价 |
| ZGDate | Y | str | 转股日 |
| EndPrice | Y | str | 到期价 |
| EndDate | Y | str | 到期日期 |
| ZGRate | Y | str | 转股比率% |
| RealValue | Y | str | 纯债价值 |
| ExpireYield | Y | str | 到期收益率% |
| KZZScore | Y | str | 可转债评级 |
| HSScore | Y | str | 主体评级 |
| RedeemDate | Y | str | 赎回登记日期 |
| RedeemPrice | Y | str | 赎回价格 |
| PutDate | Y | str | 回售申报起始日期 |
| PutPrice | Y | str | 回售价格 |
| ZGCode | Y | str | 转股代码 |
| AGNow | Y | str | 正股现价 |
| KZZNow | Y | str | 可转债现价 |
| KZZYj | Y | str | 溢价率 |
| ZGValue | Y | str | 转股价值 |

> 外层结构为 {证券代码: {字段: 值}}，每个证券一条记录、键顺序与 stock_list 入参顺序一致。单只无数据时该代码的记录为空或字段返回 null。

####  接口使用

批量获取 123071.SZ 与 123072.SZ 的可转债基础信息。

```python
kzz = tq.get_kzz_info_batch(
stock_list=["123071.SZ", "123072.SZ"],
)
print(kzz)
```

####  数据样本

```json
{
"123071.SZ": {
"AGNow": "5.06",
"CurRate": "3.000",
"EndDate": "20261021",
"EndPrice": "115.000",
"ExpireYield": "-2.220",
"ForceRedeem": "8.680",
"HSCode": "300569",
"HSName": "天能重工",
"HSScore": "AA-",
"KZZCode": "123071",
"KZZName": "天能转债",
"KZZNow": "114.776",
"KZZScore": "AA-",
"KZZYj": "51.52",
"PutBack": "4.680",
"PutDate": "0",
"PutPrice": "0.000",
"RealValue": "114.572",
"RedeemDate": "0",
"RedeemPrice": "0.000",
"RestScope": "69366.438",
"SetCode": "0",
"ZGCode": "123071",
"ZGDate": "20210427",
"ZGPrice": "6.680",
"ZGRate": "0.905",
"ZGValue": "75.749"
},
"123072.SZ": {
"AGNow": "10.88",
"CurRate": "4.000",
"EndDate": "20261021",
"EndPrice": "120.000",
"ExpireYield": "-0.934",
"ForceRedeem": "42.390",
"HSCode": "300729",
"HSName": "乐歌股份",
"HSScore": "A+",
"KZZCode": "123072",
"KZZName": "乐歌转债",
"KZZNow": "119.770",
"KZZScore": "A+",
"KZZYj": "258.98",
"PutBack": "22.830",
"PutDate": "0",
"PutPrice": "0.000",
"RealValue": "119.553",
"RedeemDate": "0",
"RedeemPrice": "0.000",
"RestScope": "14178.080",
"SetCode": "0",
"ZGCode": "123072",
"ZGDate": "20210427",
"ZGPrice": "32.610",
"ZGRate": "0.154",
"ZGValue": "33.364"
}
}
```
