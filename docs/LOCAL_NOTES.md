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

2. **财务数值走本地文件解析**:
   - 主数据源(2026-09-29 起): 官方终端"专业财务数据"下载**直接写本客户端**
     `vipdoc/cw/gpcwYYYYMMDD.dat`(实测数值比 gtja 源更全更新, 见下文双源分叉节),
     分析目录即官方客户端目录, **无需再同步**
   - gtja 的 cw 同步退役; `sync_cw --only-missing` 保留为工具, 供无订阅用户
     用券商定制版(如国泰君安)免费文件补老历史, 或未来双源场景使用
   - 文件布局: 20字节头 `<1hI1H3L>`([1]=报告期,[2]=记录数,[3]=数据区偏移,[4]=单条字节数);
     索引区 每记录11字节 `<6s1c1L>`(代码,标志,数据偏移);每条记录 记录字节数/4 个 float32,
     字段序号即官方 FN1..FN584(含义见 03-tqcenter-财务/get_financial_data.md)
   - 解析器: `python -m tdx_local.gpcw <gpcw文件或cw目录> 600519`(也可 `from tdx_local import read_series` 读历史序列)
     (已验证:茅台 2025Q3 EPS 51.53 / 每股净资产 205.28,与公开财报一致)
   - 注意: 下载中的报告期文件是 20 字节空占位, 同步时跳过
     (**`test -s` 拦不住它们——占位文件非 0 字节**; 用 `gpcw.MIN_VALID_SIZE`(>1000)
     判断, 或直接用 `gpcw.scan_reports` 核查状态)

3. **免费基本面快照**:`get_stock_info` 平铺返回 34 个 J_ 字段(最新一期财务摘要:
   J_mgsy 每股收益、J_mgjzc 每股净资产、J_jly 净利润、J_ch 营收、J_gdrs 股东人数等),
   金额单位一般为万元。要历史序列时用上面的 gpcw 解析。

## gpcw 字段校准结论(2026-09-28, 贵州茅台真值锚定)

官方 FN 编号与文件实测有三类偏差, 语义/单位/实证状态以 `tdx_local/cw_fields.py` 注册表为准:

1. **文档缺失区已锚定**: FN74=营业收入(不含利息/手续费收入, 比营业总收入低约2%),
   FN95=净利润(含少数), FN96=归母净利润, FN97=少数股东损益(=95-96 实测吻合)。
2. **单季陷阱**: FN230/232/234 文档名义为"营业收入/归母净利/经营净额",
   实测为**单季值**(2024 四季差分逐一吻合)。年度口径用 FN74/96/107。
3. **新准则科目缺失**: 合同负债/使用权资产/租赁负债在 584 槽位中无对应
   (锚点扫描跨年无交集); FN45 预收款项 2020 起恒为 0。按名请求会抛 LookupError。
4. **单位不统一**: 主表科目=元, FN238 总股本=股, 比率=%, 每股=元/股。
   (对比: HTTP `get_stock_info` 的 J_zgb 是万股。)
5. **float32 精度**: 862 亿级净利存储尾数含数千元噪声, 勾稽校验用
   `gpcw.close_enough`(默认相对容差 1e-6), 不要 `==`。

配套工具(gpcw.py): `read_series` 支持按注册名取数; `cumulative`/`single_quarters`
累计转单季(缺前置报告期抛 `GpcwReportGap`; 注意 A 股 2002 年起才有季报制度、
上市前只有年报, 全历史差分会在早期遇到缺口——用 start/end 取窗口或 on_missing='skip');
`scan_reports` 文件状态扫描;
`approx_announce_date` 法定披露截止日近似(实际公告常更早, 精确 announce_time 只能走 HTTP);
`sync_cw` 从 gtja 源目录同步(自动跳过占位)。

## 行情复权实测(2026-09-29, 茅台 2011-2026 验证)

1. **`dividend_type='front'` 是纯减法前复权**: 把未来分红直接从历史价里减掉,
   高分红股(茅台)早期价格会算出**负数**(2011 年 -176 元)——不可用于收益率计算。
2. **`dividend_type='back'` 比值也不可靠**: 同窗口后复权比值 11.19, 与正确总回报
   12.49 偏差 10%, 疑似未正确处理送股事件。**TDX 自带复权序列勿直接用于长期回报**。
3. **`get_divid_factors` 返回值无日期**: 只有 [派息,配股价,送转,配股] 金额行, 按时间
   排序, 无法与除权日对齐。
4. **正确做法(总回报财富模拟)**: 不复权价 + 带日期分红事件, 逐日模拟——
   除息日收现金(按送股前股数) -> 送股乘股数 -> 现金按当日收盘再投。
   茅台 2011→2026.09: 价格 6.71 倍(13.45%/年) vs 总回报 12.49 倍(18.22%/年);
   与 hexin 前复权比值 12.41 交叉吻合。分红事件(带日期)外部源可得,
   金额可用 `get_divid_factors` 按序核对。注意送股识别: 对比分红基准股本跳变。

## 全接口实测补充(2026-09-29, 60 项用例)

> 用例已固化到 `tests/`(pytest): 离线组 `test_offline.py` 不依赖客户端, 在线组
> `test_live.py` 在 17709 不可达时自动整组跳过。运行: `python -m pytest tests/ -v`。
> 当日实测: 57 通过 / 3 注意 / 0 失败, 据此修复 TqClient 三处静默失败(见下)。

### TqClient 修复(同日)

1. `call()` 无参调用时省略 `params` 键, 网关回 `-32602 "MCP参数params必须为对象"`
   且被静默吞掉 —— `get_sector_list`/`formula_get_all` 等无参方法一直返回空。
   现恒传 `params`(空参传 `{}`), 并对 JSON-RPC 层 `error` 显式抛 `TqError`。
2. `snapshot()` 原从 `result.Value[code]` 取数, 当前客户端快照字段平铺在 result
   顶层(与 `get_stock_info` 同款), 恒返回空 —— 已适配(兼容旧 Value 形态)。

### 服务端行为新发现(官方文档/本笔记此前未记载)

1. **`dividend_type='back'` 以请求窗口首日为基准** ⚠️: 窗口内首个除息日之前
   back==不复权, 之后才出现差异; 换窗口起点会得到不同的"后复权"序列。
   跨窗口拼接后复权数据会算错收益(单窗口内算区间回报不受影响)。
2. `get_market_data` **忽略 `field_list`**(恒返回全部字段, 且每股 dict 混有
   `ErrorId`/`Time`/`VolInStock`/`ForwardFactor`) —— 现在 `market_data()` 收尾
   按参数客户端裁剪; 本地无数据的代码返回每股空信封
   `{"ErrorId":"0","Value":[]}`(静默), 现移入 `result["_missing"]`。
3. `get_stock_list` **必须 `market`+`list_type` 双参**(缺任一报
   "参数缺少:market/list_type"): 5=全部A股 5578 / 50=沪深A股 5227 /
   32=可转债 330 / 31=ETF基金 1732(2026-09-29 实测家数)。
4. `get_financial_data` 除 `table_list`/`report_type` 外**还必须传
   `start_time`/`end_time`**; 补齐后报告期日历可用(ProDataPaged), 数值通道
   仍无 FN 字段(维持原结论)。
5. `get_divid_factors` 返回**列式结构**(`result.Date/Type/Value` 平行数组, 非文档
   的行式 dict), Bonus 列为**每 10 股派息(元)**, `start_time`/`end_time` 被忽略
   (恒返回全历史)。`TqClient.divid_factors()` 已封装为 `{除息日: 每股派息元}`。
6. 网关不支持 `get_market_snapshot_batch` 与 `get_subscribe_hq_stock_list`
   (均 `-32601 "MCP不支持该tqcenter方法名"`); 批量快照只能循环单只。
7. `get_stock_list_in_sector` 支持板块代码或名称两种传参, 结果一致;
   注意 880081(轮动趋势)成份股仅 2 只 ETF, 属正常。
8. 本地无 5m 数据的股票走 `get_market_data` 不报错, 返回空信封(见第 2 条);
   1m 有 15840 根(600000.SH), 未超 24000 不触发分页。

### tqcenter 侧对照实测(2026-09-29, 客户端内运行)

客户端 tqcenter 环境: Python 3.14.3(64位), default-encoding=utf-8 但
`open()` 文本模式默认 cp936 —— 上一版测试脚本结果文件乱码的根因
(未显式指定 encoding, 落到 locale 首选编码); 输出文件须显式 utf-8-sig。

1. **FN 数值通道在 tqcenter 模式可用**(HTTP 恒 null 定性为网关限制, 非数据缺失):
   `get_financial_data(stock_list, field_list=["FN1","FN4","FN74","FN95","FN96"],
   start_time, end_time, report_type="tag_time")` 返回 {代码: pd.DataFrame},
   含 FN 值 + announce_time/tag_time, 茅台 10 个报告期齐全。
2. **field_list 是数值通道的必要参数**(tqcenter 亦然): 缺省只回日历两列。
3. `table_list` 是 HTTP 网关独有参数: tqcenter 下传它直接 TypeError(意外关键字)。
4. **GO 通道可用**: `get_gp_one_data` 返回 GO1 发行价/GO3 一致预期目标价/GO5 预期EPS
   /GO8 预期净利润(万元), 字符串数值。
5. `get_divid_factors` 在 tqcenter 返回 pd.DataFrame(Date 索引, Bonus 为每10股,
   与 HTTP 列式数组一一对应); **且尊重 start_time/end_time** —— HTTP 网关忽略
   时间参数属网关行为, 非数据层行为。
6. **gpcw 字段校准被官方通道反向验证**: tqcenter FN74(2024)=170899144704 与
   gpcw 解析值一致; FN96(2024)=86228148224 即 close_enough 文档里的 float32
   噪声案例原值; FN95-FN96=31.07亿 与 cw_fields 少数股东损益注记吻合;
   FN1/FN4(2025Q3)=51.53/205.28 与锚值一致。
7. **HTTP + field_list 重试已做(同日客户端在线): FN 仍为 null** ——
   table_list/report_type/start_time/field_list 全部补齐也只回日历两列,
   数值通道在 HTTP 网关彻底关闭, "财务数值走 gpcw 文件解析"结论坐实。
   tests/test_live.py 探针保留为金丝雀: 未来客户端版本若放行会以 skip 提示。

### 数据更新后的双源分叉实测(2026-09-29, 客户端下载专业财务+K线之后)

1. **官方客户端的"专业财务数据"下载会直接改写 vipdoc/cw/gpcw\*.dat**(当日改写
   65 个, 2008 年报起), 且与 gtja 源出现**实质分叉**: 8 个文件大小不一致
   (官方更全, 如 20241231 多 301716/920202 两家新上市公司), gpcw20250930
   大小相同但 38 条记录值不同(官方为更正值, 如 000572 FN362 1.43 vs gtja 1.47)。
2. **sync_cw 新增 `--only-missing` 模式**: 双源场景下 gtja 同步改用只补缺,
   永不覆盖已有文件, 避免用 gtja 旧版冲掉官方新版; 默认行为不变。
   推荐工作流: 官方下载为准(近年数据), gtja 只补 2008 以前的老历史报告期。
3. **官方客户端 K 线下载尾部新鲜但深度有限**: sh600519 尾根 20260928 但仅
   1251 根(约5年), gtja 5972 根全历史 —— lday 合并的价值场景;
   `sync_lday(only_missing=True)` 实跑补缺 503 个文件(客户端开着也安全),
   全量并集合并仍建议先关客户端。
4. **盘后下载会清空分钟数据**: 更新前 1m 有 15840 根, 下载后 5m/1m 均空信封
   (`_missing` 可见), refresh_kline 救不回 —— 分钟线需在客户端"盘后数据下载"
   勾选分钟线, 或打开过对应周期图后才落地。

5. **⚠️ 盘后下载会把本地日K重置为"最近5年"窗口**: 实测全市场统一变成
   1251 根(20210802~20260928), 尾部新鲜但深度丢失(此前 get_market_data
   可取全历史约 6000 根); 分钟数据则被整体清空。恢复方法: 关客户端后
   `python -m tdx_local.lday sync <gtja_lday> <tdx_lday>` 全量并集合并
   (补回老历史, 重叠日以官方侧为准保住新鲜尾部); 并检查盘后下载对话框的
   下载范围设置, 避免下次下载再次截断。在测试里对应
   `test_market_data_paging_merge_consistent`(总量骤降即报警)。
