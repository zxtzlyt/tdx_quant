# 本地模式(17709)实测笔记

> 2026-09-28 在本机实测得出,补充官方文档没写透或易踩的坑。接口参考见同目录各章节文档。

## 实测可用接口 ✅
`get_match_stkinfo`(名称→代码)、`get_market_snapshot`(实时快照含五档)、`get_market_data`(日K/分钟)、
`get_sector_list`、`get_trading_dates`、`formula_get_all`、`refresh_kline`、`refresh_cache`、
`get_stock_info`、`exec_to_tdx`(可驱动客户端打开个股页面并触发数据下载)。

## 关键坑与结论

1. **接口只读本地,数据要先落地**
   - 新标的没有历史K线时 `get_market_data` 只返回当天 1 根;
   - `refresh_kline(['600000.SH'],'1d')` 只刷"缓存",`get_market_data` 能读到,但公式引擎读不到;
   - 最有效的方式:`exec_to_tdx('http://www.treeid/breed_1#600000')` 让客户端打开该股页面,自动补全历史(实测 1 根 → 179 根,市场前缀 0#深 1#沪 2#京);
   - 根治:客户端定期做"盘后数据下载"。

2. **公式引擎在 HTTP 模式下不可用 ❌**
   - `formula_set_data_info`(含必填 start_time/end_time)与 `formula_set_data`(字典行格式,Date 用
     `YYYY-MM-DD HH:MM:00`)都返回"设置成功",但 `formula_get_data` 返回空、`formula_zb('MACD')` 全 0;
   - 结论:本客户端版本的公式计算通路走 HTTP 不生效。**指标一律用 Python 自算**
     (EMA→DIF/DEA/MACD 十几行代码,数据源 get_market_data)。

3. **get_stock_info 的返回结构特殊**:字段平铺在 `result` 顶层,不在 `result.Value` 里;
   `field_list` 必须用文档字段表的精确名称(如 `Name`/`MinPrice`),字段名猜错会静默返回空。

4. **download_file 与K线无关**:它是下十大股东、ETF申赎清单、舆情、龙虎榜、限售解禁等文件的
   (down_time 为指定日期如 `20241231`,不是年份);别用它补K线。

5. **数据未落地时的静默空返回**:`get_trackzs_etf_info` 返回 `{"raw": ""}`、
   `get_trading_dates` 返回 `Value:null`(需 999999 指数K线,`refresh_kline(['999999.SH'],'1d')` 可解)
   ——遇到空返回先怀疑"本地没数据",再怀疑参数。

6. **get_market_data 一次最多 24000 条**;大结果带分页标记(KlinePaged / TPythPaged),
   遇到 `has_more`/`page_token` 必须按游标续取合并。前复权传 `dividend_type:'front'`。

7. **时间格式** `YYYYMMDD` / `YYYYMMDDHHMMSS`;市场后缀 `.SH/.SZ/.BJ/.CSI/...`(常量枚举见 11-常量枚举/constants.md)。

## 代码模板

```python
import json, urllib.request
def tq(method, **params):
    req = urllib.request.Request('http://127.0.0.1:17709/',
        data=json.dumps({'id':1,'method':method,'params':params}, ensure_ascii=False).encode('utf-8'),
        headers={'Content-Type':'application/json; charset=utf-8'}, method='POST')
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode('utf-8')).get('result', {})

r = tq('get_market_data', stock_list=['600000.SH'], count=120, period='1d', dividend_type='front')
val = r['Value']['600000.SH']   # {'Date': [...], 'Open': [...], ...}
```

## 财务数据方案(2026-09-28 实测)

1. **专业财务接口的隐藏参数**:本客户端版本的 `get_financial_data` / `get_financial_data_by_date` /
   `get_gp_one_data` / `get_gpjy_value` 在 HTTP 模式下必须额外传文档未记载的
   `table_list: []` 和 `report_type: 'announce_time'|'tag_time'`,否则报
   `json has no table_list / no report_type`。
   补齐后**报告期日历能查**(announce_time/tag_time 列表),但 **FN/GO/GPJY 数值通道返回 null**——
   数值在 HTTP 模式下取不到,勿再深挖。

2. **财务数值走本地文件解析**(国泰君安客户端免费提供,官方终端要订阅):
   - 数据源: `D:\jyrj\gtja\vipdoc\cw\gpcwYYYYMMDD.dat`(每报告期一个文件,1988 至今,已同步到
     `D:\jyrj\tdx\vipdoc\cw\`;gtja 客户端会持续下载更新,新文件出来后再同步一次)
   - 文件布局: 20字节头 `<1hI1H3L>`([1]=报告期,[2]=记录数,[3]=数据区偏移,[4]=单条字节数);
     索引区 每记录11字节 `<6s1c1L>`(代码,标志,数据偏移);每条记录 记录字节数/4 个 float32,
     字段序号即官方 FN1..FN584(含义见 03-tqcenter-财务/get_financial_data.md)
   - 解析器: `python -m tdx_local.gpcw <gpcw文件或cw目录> 600519`(也可 `from tdx_local import read_series` 读历史序列)
     (已验证:茅台 2025Q3 EPS 51.53 / 每股净资产 205.28,与公开财报一致)
   - 注意: gtja 下载中的报告期文件是 20 字节空占位,同步时跳过(`[ -s ]` 判断)

3. **免费基本面快照**:`get_stock_info` 平铺返回 34 个 J_ 字段(最新一期财务摘要:
   J_mgsy 每股收益、J_mgjzc 每股净资产、J_jly 净利润、J_ch 营收、J_gdrs 股东人数等),
   金额单位一般为万元。要历史序列时用上面的 gpcw 解析。
