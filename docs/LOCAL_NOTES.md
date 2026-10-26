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
   ⚠️ 数值通道结论已被 2026-09-30 发现推翻: 根因是 `table_list=[]`,
   见文末「专业财务函数族 HTTP 全通」。
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
   ⚠️ 已被 2026-09-30 发现推翻: 当时的重试 `table_list=[]` 实为"不选任何表";
   `table_list=field_list` 后 FN 数值全量返回, 见文末新节。

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

### 专业财务函数族 HTTP 全通(2026-09-30, 红宝书24对照实测)

> 背景: 对照《红宝书24-专业财务函数》九函数编号表逐族验证。此前 FN 数值通道
> "彻底关闭"的结论根因是隐藏参数 `table_list` 传了空表。

1. **`table_list` = `field_list`(隐藏必填参数, 五族通用)**: 网关为
   get_financial_data/get_gpjy_value/get_scjy_value/get_bkjy_value/
   get_gp_one_data(type 1/3/5/7/9) 构造请求时要求 `table_list`;
   传 `[]` 时 ErrorId=0 但 Value 全 null(语义="不选任何表")。
   tqcenter 1.2.0 源码 `"table_list": field_list` 佐证 —— 与 field_list 同值。
2. **FN 数值通道 HTTP 完全可用**(推翻 09-29 两条旧结论): 
   `get_financial_data(stock_list, field_list=["FN1",...], table_list=同,
   report_type="tag_time", start_time, end_time)` 返回 {代码: {FN码: [值...]}}
   + announce_time/tag_time 平行数组。茅台 2026 中报 FN96=445.17亿 与东财 F10
   经营评述互证; FN1/FN40/FN95/FN107 与 gpcw 解析一致。
   gpcw 文件解析降级为离线备份与校准器, 不再是数值唯一来源。
3. **GO 族可用**(GO 单值快照): GO1 发行价/GO3 一致预期目标价/GO26 最新解禁日/
   GO33 最新总股本(万股)/GO34 实际流通A股, 字符串数值扁平 dict。
4. **GP 族可用**(GP 日序列, {GP码: [{Date, Value:[N1,N2...]}]}):
   GP3 融资余额(万元, 浦发 ~37亿)+GP4 大宗/ GP16 总市值/ GP21 股息率
   实测正常; 注意 GP6 陆股通持股、SC2 沪深股通净买入等北向口径恒 0
   (北向逐日披露已停, 非取数失败)。
5. **SC 族可用**(SC 市场序列): SC1 沪深两融余额 2.58 万亿(万元口径)量级正确;
   返回不带 ProDataPaged 包装(顶层 {SC码: [...]}), 无 stock_list 入参。
6. **BK 族可用**(BK 板块估值): 880001(全A) BK5 市盈率TTM 整体法 20.94/
   算术平均 35.61, BK10 板块总市值; 板块须为有估值数据的板块指数
   (880081 轮动趋势类返回 null 属正常)。入参 stock_list=板块代码。
7. 测试对应: test_live.py 新增 test_financial_data_fn_numeric_channel/
   test_gp_one_data_snapshot/test_gpjy_value_series/test_scjy_value_market/
   test_bkjy_value_sector; 原 fn_channel 金丝雀测试改断言取数成功。

### DataTool 盘后数据工具实测与日线全历史修复(2026-09-30 凌晨)

1. **DataTool.exe**(`D:\Program Files (x86)\tdx_data_tool\v4`)是官方"深沪行情
   数据处理工具": 纯 GUI、无任何命令行开关(exe 字符串/导入表实证);
   `datatool.ini` 已配 `VIPDOC=D:\jyrj\tdx\vipdoc`。功能 = 盘后下载(日线包/
   分笔包)→ 转档(.day/.01/.5/.vid+.vtc)→ 合并/检错/删除区间。任务清单存
   `downit5.cfg`(GUI 里保存过才生成)。老脚本同款直连 URL
   `59.175.238.39/products/data/data/{newday,2ktick}/YYYYMMDD.zip` 已失效
   (IP 不通),现行下载地址由 GUI 内部寻址,exe 字符串中未暴露。
2. **newday 日包是增量; 深历史要靠官网完整包**: `data.tdx.com.cn/vipdoc/hsjday.zip`
   (526MB, 沪深京全历史含退市证券, 官网 vipdata 页: "首次安装或长时间没下日线
   时下载, 放 vipdoc 解压覆盖")。本次**未直接覆盖**, 而是解压到独立目录后
   `python -m tdx_local.lday sync` 全量并集合并(须关客户端, TdxW 强杀):
   sh/sz/bj = 6130/5935/614 个文件(+1921 退市/缺失证券);
   sz000001 由 20120104(券商源遗留缺口)修复为 19910403 上市首日起
   (3568→8463 根); sh600519 保持 20010827; 尾根 20260929 未回退;
   test_offline 32 passed。**今后日线全历史修复直接复跑本条即可。**
3. **分笔→分钟管道**: 2ktick 分笔包 → DataTool 分笔转档(newtick/*.vid+*.vtc,
   vid 是按日期索引的文件头, 每股单文件多日共存) → 分钟转档(minline/*.01
   1分钟 + fzline/*.5 5分钟)。⚠️ **分钟转档重写 .5 时只保留约最近两年**
   (600519 实测: baostock 合并出的 2020→2024-09 段被 2026-09-30 的转档
   截掉, 余 24000 根/20240905 起) —— baostock 深历史合并必须安排在
   全部 GUI 转档批次完成之后重跑; 分批下载对账方法: vid 头 start/days、
   down/tickzip 的 zip 日期集合与 999999 交易日历三方核对。
3b. **✅ 分钟+分笔窗口滚动维持中(2026-10-15 复验)**: 窗口已滚动到
   20260511→20261015 共 107 个交易日(10-12~10-15 四天 17:10 转档补齐,
   .01=25680 根=107×240 无缺失; 此前 10-11 复验 103 天), 沪深北三市分笔同步;
   999999 指数日线尾根仅到 1008(客户端重开登录后自动补 1009, 交易日历随动)。
   **客户端"盘后数据下载"勾 1m/5m 实测(10-15)**: 日线正常更到当日且全历史
   未截(旧的"日K重置5年"坑这次未复现), 但 vipdoc 分钟文件**零写入**(界面显示
   "下载完毕"也没落盘) —— 补全市场分钟别指望这条路, 只有 DataTool 管道有效。
   此前 2026-10-08 终验: 20260511→20260929 共 100 个交易日, zip 100/100,
   .01 每天整 240 根无缺失; 全市场 .01/.5 各 sh 28854 / sz 25386 / bj 381
   个(含基金债券等非股标的, 抽样首日晚于 0512 的均为 5 月后新股)。
   **教训(踩过一次)**: 分钟转档是按时间段的, 分批下载后逐段转档容易
   留洞 —— 本次 0901/0914/0915 三天被最早一轮的转档区间跳过(后用补转
   0901→0915 一段修复); 每轮转档后必须按天对账(.01 根数/240 = 应覆盖
   天数)。**今后例行**: 每个交易日盘后 DataTool 下当日分笔包 → 分笔
   转档 → 分钟转档(区间直接勾"上次终点→当日") → **跑归档器(见 3c)**。
3c. **✅ 分钟深历史归档兜底(2026-10-15 上线)**: GUI 分钟转档每次重写 .5 只留
   最近约 24000 根(600519 起点 10-15 已滚到 20240918), 截掉的段不可再生。
   `examples/archive_minutes_vipdoc.py` 直读 vipdoc, 以同 32 字节记录格式
   (<HH4IfI2H) 落 `<仓库根>/minute_archive/<1m|5m>/<market><code>.bin`,
   **只增不减**: 首见代码整文件拷贝(种子), 此后只追加比归档末根 (日期,时间)
   新的记录, 转档怎么截窗都不影响。离线可跑(转档完即可, 不需要 TdxW)。
   - **例行第 4 步**: 每轮"下载→分笔转档→分钟转档"后
     `python examples/archive_minutes_vipdoc.py 5m all`(全市场 5m 已于
     10-15 种子约 8.4GB, 二次运行幂等 0 新增); 按日对账
     `python examples/archive_minutes_vipdoc.py check 600519.SH`。
   - **1m 全市场种子约 45GB、每交易日约 +0.4GB, 尚未做**(默认只跑参数区
     关注池); .01 窗口起点 0511 固定、目前还在增长(25680 根未截), 前端
     何时开始滚掉未知 —— 若要全市场 1m 深度, 早点决定 `1m all`。
   - 读取: `read_bars(路径, count=, end_date=)` 返回与 TQ market_data
     同构字段; `.lc1/.lc5` 旧格式客户端已不再维护(600519.lc1 停在 08-07),
     分钟数据只看 .01/.5。
4. **分钟/分笔深度上限(免费官方通道)**: 客户端历史分钟下载 ~100 天
   (datatool.ini `MINDAYS=120` 吻合), 盘后下载历史时段每次≤31 天; 分笔服务器
   保留窗口以 DataTool GUI 日历可选范围为准(未实测)。**1 分钟补到 2020-01
   无免费通道**: 东财 klt=1 实测仅回 1 个交易日且随后封锁本机直连;
   gtja 侧仅 2023-05~08 共 66 日残留; 可选付费源(tushare 5000 积分/QMT/聚宽)
   或从现在起每日盘后积累。5 分钟深历史免费可用 baostock(2011 起, 无 1 分钟)。
5. **待办(GUI 点击, 客户端关闭状态下)**: 补满分钟 100 天窗口与分笔窗口 =
   打开 DataTool → 分笔页勾日期区间(先选老日期试探服务器窗口) → 下载 →
   分笔转档 → 分钟转档; 若日历拒绝老日期则按月分批勾最近可得区间。
6. **tqs/TdxAiData 云通道(=知乎《全能实战指南》说的"数据采集插件")**:
   PYPlugins 已部署 TdxAiData.dll 但版本旧于 user/tqserver.py 1.1.1
   (缺 GetCallAuctionInStr 导出, 初始化即 AttributeError); PyPI
   `pip install tdxaidata` 可用(自带配套 DLL+ini)。但调用任何接口返回
   `[错误] Need TokenKey` —— 需登录通达信个人版商城 → 会员中心 →
   积分和Key管理 → 创建"数据服务"Key 填入 TdxAiData.ini [Token]。
   官方文档 tdxaidata_overview 样例注释原文: **"一分钟周期云获取方式后期
   不做限制 不受限100天"** —— 唯一明示可突破客户端分钟 100 天上限的通道;
   能回溯到多早(2020?)须拿到 Key 后实测 get_tick_data/get_minute_data。
7. **tqs 云通道实测(2026-09-30, 用户提供数据服务Key)**: Key 写入 ini 后
   认证打通 —— `get_market_data period='1d'` 正常返回(600519 近期日线);
   但**全部分钟/分笔族接口(1m/5m/15m/30m/1h/tick/minute_data, 近期与
   2020 日期均试)统一返回 `[错误] TokenKey Insufficient Or Key Error`**,
   即该 Key 当前档位只含基础行情, 分钟/分笔需要商城侧开通对应数据包
   (积分/付费规则在商城后台, 公开资料查不到)。回溯深度问题被权限问题
   遮蔽, 开通数据包后方可实测。工具链已就绪: pip tdxaidata + ini 已配,
   探针即本条命令行。
8. **baostock 免费 5 分钟深历史(2026-09-30 实测, 全市场回补已启动)**:
   `pip install baostock` 免 token。
   - 覆盖: **沪深个股 5m 自 2020-01-02 起**(并非 2015), 指数/ETF/北交所
     均无 5m; 单次查询可拉整区间(~78k 行/股); time 即 TDX bar 结束时刻
     (09:35 起), 量纲 股/元 与 vipdoc 一致。
   - **.5/.01 新代分钟文件布局(实证钉死, 与日线同日聚合交叉验证通过)**:
     `<HH 4I f I 2H>` = 日期词(y-2004)*2048+m*100+d, 时间词 hh*60+mm,
     开高低收×100(I), 成交额(f32 元), 成交量(I 股), pad。
   - **吞吐与禁忌**: 默认 2000 行/页 × 39 次往返 ≈ 280s/股; 实测把
     `BAOSTOCK_PER_PAGE_COUNT` 调大(20000/100000)会触发服务端异常
     (小查询空响应、查询挂死), **不要改这个常量**; 同 IP 并发 >3-4 连接
     会被整体饿死(冷却 >15 分钟), 多进程分片 ≤2-3 且慎重。
   - ⚠️ **惩罚实测升级(2026-09-30 白天)**: 凌晨并发实验触发的惩罚持续
     多日未解 —— 形态为 login 秒回但 k 线查询黑洞(60s 零字节)。
   - ⚠️ **终局(2026-10-08): 判定为服务端自身异常, 非 IP 封禁** ——
     切手机热点新出口 IP(113.80.22.250)后 k 线查询**照样黑洞**, 日线/
     5m/周线/日历全部不通, 时间恰在国庆长假。**本任务放弃此通道**:
     磨机循环与 `D:\temp_baostock_fill`(脚本+断点)已清理; .5 深历史
     缺 2020-01→2024-09 段的现状予以接受, 假期后若恢复可按本节配方
     重建脚本复跑(并集合并/断点/健康门卫要点都在上文), 或走 tqs
     分钟数据包(见第 7 条)。
   - (复跑要点存档) 页大小 2000/页×39 往返 ≈ 280s/股, 勿调
     `BAOSTOCK_PER_PAGE_COUNT`; .5 按(日期,时间)并集合并、本地优先、
     原子替换; 单连接串行铁律。

## DLL 扩展通道实测(2026-09-30, tdx_docs 两份官方规范)

> 起因: 用户要求基于 tdx_docs 两份规范(DLL函数编程规范/插件选股编程规范)整理可用指南。
> 全部过程与使用说明沉淀在 `docs/选股分析指南.md`(仅本机, 不入库), 此处只记坑与结论。

1. **官方示例 DLL 全是 32 位**: `通达信插件选股编程规范/MyPlugin64.dll` 虽名带 64,
   PE Machine 实为 0x014C(32 位); DLL函数规范的示例干脆没带编译产物。
   本机 TdxW.exe 是 64 位(0x8664) —— 官方示例直接部署必失败, 须自行编译。
2. **本机 MSVC 就位但不在 PATH**: VS18 BuildTools(MSVC 14.50) 在
   `C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\`,
   需先 call `Common7\Tools\VsDevCmd.bat -arch=x64`; 无 gcc。
   编译脚本 `dll/build_64bit.cmd`(编译 + dumpbin 导出自检), 产物在 `dll/out/`。
3. **官方示例源码 5 处问题**(VC6 时代代码, 现代 MSVC 编不过/跑不对, 修正版在
   `dll/src/`, 文件头注释有逐条说明): ① `PLUGIN_EXPORTS` 定义在 include 之后
   → 导出函数变 dllimport, DLL 无导出表(最隐蔽); ② ParamInfo 的 nMin 误写 nMax;
   ③ AfxRightData 的 for 作用域泄漏(C2065); ④ InputInfoThenCalc1 未防
   nDataNum=ASK_ALL(-1) 直接 new 崩溃; ⑤ strcpy 需 _CRT_SECURE_NO_WARNINGS。
4. **源码含中文字面量(插件名等)必须 UTF-8 BOM**: 无 BOM 时 cl 按 cp936 误读源码;
   带 BOM 后窄字面量正确转为 GBK 字节, 通达信界面显示正常。
5. **公式 DLL 通道端到端验证通过**: TestPluginTCale64.dll → T0002\dlls\ →
   公式管理器 DLL函数 绑定(客户端弹"成功绑定了TestPluginTCale64.dll",
   绑定对话框原话"64位主程序只能绑定64位DLL") → 用户公式 TESTDLL:
   `TDXDLL1(1,H,C,C);` → 编辑器动态翻译面板解析出"第1号DLL" →
   exec_to_tdx `zb_TESTDLL` 挂浦发银行日K副图 → 输出递增直线末值 419.00
   (=420根K线序号, TestPlugin1 语义精确吻合)。
6. **插件选股入口在量化模拟版已移除**: 键盘精灵 `.9` 全列只有 .905 条件选股/
   .906 定制选股/.907 模式选股/.908 策略股票池/.909 综合选股, 无插件选股;
   MyPlugin64.dll 已按规范部署 `D:\jyrj\tdx\Plugin\` 备而待用(标准版可用)。
   `.908` 在本版实测=策略股票池(网上资料说的 .908=插件选股 属其它版本)。
7. **create_sector/send_user_block 中文板块名会写坏客户端板块表**: HTTP 网关
   对中文参数做 UTF-8→GBK 转码, "技术选股"存成了含非法字节的乱码记录,
   get_user_sector 返回的 JSON 从此不是合法 UTF-8, urllib decode 直接炸。
   delete_sector 对该损坏记录返回"成功"但删不掉。已修: ① TqClient.call 解码
   errors="replace"(网关缺陷兜底); ② 配方改用英文板块简称 JXG。
   残留乱码板块待客户端 UI 删除(自定义板块设置, 键盘精灵 .931)。
8. **exec_to_tdx 是 GUI 自动化的最佳通道**(HTTP 可达): `breed_1#600000` 跳个股
   (顺带把数据下载下来), `zb_MACD`/`zb_自编公式名` 挂指标到当前图 ——
   本轮 computer use 验证公式 DLL 全靠它。客户端主界面自绘控件, 坐标点击
   基本无效; Ctrl+T/Ctrl+F 快捷键与键盘精灵(直接打字)可靠; 弹出对话框全是
   标准 Win32, UIA 树完整可自动化。窗口最小化(bounds 变 -48000)是一切
   "点击无效"的元凶, 截图动作会临时还原窗口。
9. **测试**: `tests/test_guide_examples.py` 15 用例(11 离线纯逻辑 + 4 在线端到端,
   在线组沿用 refresh_cache 探活门控), 全部通过。配方脚本与测试互相咬合:
   在线测试真跑配方 main()(monkeypatch 参数), 曾抓出 FN 值为字符串的实 bug。

### 标准版重装后的插件选股实测(2026-09-30 上午, 用户重装 tdx64 标准版)

1. **原地重装**: 同目录 D:\jyrj\tdx, TdxW.exe 0x8664, 标题从"(量化模拟)"变
   "通达信金融终端 V7.73 标准版"; 之前部署的 Plugin\MyPlugin64.dll 与
   T0002\dlls\TestPluginTCale64.dll 均保留; TQ 17709 仍在线。
2. **插件选股入口在「公式」菜单下**(用户确认), 不在老规范说的"功能→选股器";
   键盘精灵 .9 热键表仍无 .908 —— **热键表≠功能存在**, 认菜单不认热键。
3. **自研插件① 上线**: dll/src/MyPicker/MyPicker.cpp "缩量回踩MA支撑"
   (MA上行 + 今日量<=前5日均量*缩量% + 收盘价在MA±回踩幅度%, 四参数
   Value[0..3]=回踩%/缩量%/均线天数/回看天数)。真 64 位(0x8664),
   4 导出齐全, 已部署 Plugin\。新坑: LEAN_AND_MEAN 下 fabs 需显式 <math.h>。
4. **交叉验证工作流**: 插件选股 → 选股入板块(英文简称如 HJ) →
   `python examples/verify_pullback_picker.py HJ` 用 Python 同口径复算对账。
5. 本会话 computer use 不可用(引导脚本路径变更报 unavailable) —— GUI 验证
   转用户三步手动流程, 见指南 §2.4。

## 回测子系统与指标/缓存模块(2026-10-05 自主开发会话)

> 用户授权 6 小时自主功能开发。产出: `tdx_local/{indicators,kcache,backtest}.py`
> + `examples/{backtest_picker,archive_minutes}.py`。此处记录设计取舍与待验项。

1. **指标抽取的口径统一**: macd_demo/stock_checkup/pick_technical 三处重复实现
   收敛进 `indicators.py`。保留两处既定口径: ① MACD 柱 =(DIF−DEA)×2(A股看盘
   软件口径); ② 交叉判定"昨天相等也算触发"(dif[-2]<=dea[-2])。修复原
   total_return_with_dividends 原地 pop 入参 dict 的副作用, 并兼容 int/str
   日期键(divid_factors 返回 str 键, market_data 的 Date 是 int)。
2. **kcache 存不复权价是刻意设计**: 前复权序列随未来分红整体平移, 拿它做
   point-in-time 回放本身失真; 当时看到的"前复权"无法从今天的复权序列复原。
   回测的指标与收益都在原始价上算。与官方 vipdoc .day 文件混用时注意
   Volume 单位口径需自查(本缓存只保证 TQ 返回原值)。
3. **`end_time+count` 组合: 实测通过**(2026-10-05 客户端在线,
   test_market_data_end_time_count_window): count=10+end_time=20240628 恰好
   返回截至该日的 10 根, 末根==end_time。回测 point-in-time 窗口语义坐实。
4. **回测收益口径**: forward_return 与 stock_checkup 茅台口径一致(不复权价链
   +分红事件逐日再投), 分红事件只取除息日位置在 (买入日, 卖出日] 的行 ——
   买入当日除息归前手。 dividends_by_code 支持 callable(逐股惰性+记忆化),
   可直接传 `tq.divid_factors`, 全市场回测不必预取全部分红。
5. **防未来函数的构造性保证**: backtest.run 给策略的每个窗口都经
   slice_asof(end_date=T) 截断, 有回归测试(test_bt_run_point_in_time_and_
   benchmark)。但**策略函数闭包引用外部实时数据仍可绕过** —— docstring 与
   配方模板都写明"只用 asof 入参"。
6. **backtest_picker.py 未连真实服务实跑**(TQ 服务离线): 模块级逻辑由 7 个
   离线用例覆盖, 整条链路(取数->建缓存->重放->报告)由假客户端接线测试验证
   (test_guide_examples::test_backtest_picker_offline_wire)。首次真跑预期是把
   候选池(约40只)全历史拉进 kcache, 150只/批分页续取, 预计数秒; 若报错优先查
   `_missing` 与基准 999999.SH 是否有本地数据。同会话伸缩项: pick_technical/
   pick_fundamental 增加 WRITE_CSV 参数(结果带日期追加进 picks_csv/, 默认关)。
7. **版本对齐**: `__init__.__version__` 0.2.0 与 pyproject 1.0.0 此前不同步,
   本次统一为 1.1.0。

### 客户端在线真跑补记(2026-10-05 下午, 标准版 V7.73)

8. **批量快照标准版可用了**: `get_market_snapshot_batch` 在量化模拟版网关
   曾 -32601 不支持(2026-09-30), 标准版实测一次返回多只五档全字段
   (field_list 照例被忽略, 数值为字符串)。已封装 `TqClient.snapshot_batch()`
   —— 盘中批量盯盘不用再循环单只。同型坑: `get_financial_data` 的
   **ProDataPaged 分页标记标准版不再回**(量化模拟版曾回 True), 依赖该
   标记的逻辑要按"可能缺席"处理(tests 已改为两版本都通过)。
9. **分钟周期实测**: period 合法形如 '1m'/'5m'/'15m'(写 '5'/'5min' 报
   period error); 客户端本地是否有数据取决于是否下载过该周期 —— 本机
   1m 全市场有货且留存约两个月(600000.SH 最早 20260807, Time 格式
   HHMMSS), 5m/15m 为空信封(没下载过)。archive_minutes 默认周期据此
   定为 1m; 首跑 7 只归档 60,720 行, 二次运行 0 行(去重验证通过)。
10. **backtest 首次真跑**(银行板块 42 只): kcache 首建 140,989 根日K
    (数秒级), 500 交易日 51 个调仓日重放出 35 笔金叉+多头选股; 60 日
    持有胜率 65.6%/平均超额 +1.89%, 20 日 61.8%/+0.60%, 5 日 48.6%/-0.61%
    (上证基准)。全链路(取数->缓存->重放->分红再投->报告)一次跑通。

### 优化轮(2026-10-05 傍晚)

11. **backtest.run 性能**: slice_asof 的线性扫截断改 bisect_right 二分
    (前置条件: Date 升序无重复, kcache/lday/TQ 返回皆然); 日期->下标映射
    从"全候选预建"改为基准+被选中代码惰性建; asof 切片免二次 list() 复制。
    400只×1200根×201调仓日实测 4.20s -> ~1.5s(2.8x), 选股笔数与收益逐笔
    一致(80601 笔相同); 全市场 5000 只外推从 ~1 分钟级降到 ~20s 级。
12. **示例容错覆盖盘点**: 全部用 TqClient 的示例入口统一 TqError 包装
    (本轮补齐 mainbusi_demo); financial_demo 走 gpcw 文件解析不碰 TQ、
    http_call 用自带 TqHttpError —— 不属同型, 不强加。

## 送转股口径修复与回测成本/卖出条件(2026-10-27, ROADMAP P0 执行)

13. **get_divid_factors 的 Value row 真实结构**(推翻 2026-09-29 笔记):
    row = [每10股派息, 每10股送股, 每10股转增, 配股相关列], 且**全部行
    Type=1** —— 此前"扩缩股要找 Type=11 行"的结论作废。真值锚定:
    601888 20170616 行 [x,0,10,x] = 10转10; 000333 20140430 = 10转15;
    300750 20230426 = 10转8; 万科 1991-2000 的送股在 row[1](4.4/4.5/7.5)。
    row[3] 疑为配股比例/价格(口径未定), 配股需股东再出资, 全收益模型按
    惯例忽略(偏保守)。已封装 `TqClient.divid_splits()` -> {日期: 每股送转}。
14. **不带送转的总回报是错的**: "10送10"除权日价格腰斩而旧模型不补股本,
    601888 2017 全年真实总回报 +103%, 旧模型只显示价格涨幅的一半量级。
    修复后 `total_return_with_dividends(..., splits=)` / backtest
    `splits_by_code` 处理顺序按真实业务: 派息按送转前股本 -> 股本×(1+送转)
    -> 现金按除权日收盘再投。**四案例互证**(带送转总回报 vs 前复权单窗口
    区间收益): 601888 差 -1.11pp, 601318 +0.13pp, 300750 -0.02pp,
    000333 +0.53pp(在线用例 test_live_split_total_return_matches_front_
    adjusted)。
15. **refresh_kline 喂历史窗口**: 客户端只落地"看过的标的/窗口", 茅台
    2006 年窄窗口只回 1 根 —— `refresh_kline([code])` 一次即从盘上
    vipdoc lday(lday 合并过的全历史)喂进 K线缓存, 2005-2006 回满 292 根。
    在线锚定用例依赖此步。(茅台 2006 本地 lday 仍有洞, 锚定案例改用
    601888/601318/300750/000333。)
16. **backtest 交易成本**: `run(commission=, stamp_tax=, slippage=)` 折算
    cost_in = slippage+commission, cost_out = slippage+commission+stamp_tax
    (印花税仅卖出); 净收益 = 毛×(1-cost_out)/(1+cost_in)-1, 全仓进出近似。
    A股建议 A_SHARE_COSTS: 佣金万2.5双边 + 印花税万5卖出。基准不含成本,
    超额天然保守。默认全零, 逐笔收益与旧版一致(兼容回归测试)。
17. **卖出条件 sell_rule(asof, held_days) -> bool**: 持有期内逐日检查
    (截至当日含收盘的 window 切片), 触发提前卖出(horizon 仍为上限);
    需同时传 bars。picks 每笔新增 sell_date/early, 报告新增
    `report_yearly()` 分年表与 result["curve"] 批次净值(每批等权、全额
    再投近似, 期内不换仓)。
18. **market_data 数值为字符串**(标准版): 直接把 Close 喂 indicators/
    backtest 会 TypeError —— 调用方按 stock_checkup 模式先 float 化;
    kcache/lday 通道天然是数值, 无此问题。

## newtick 逐笔数据结构与 ROADMAP P2 执行结论(2026-10-27 凌晨)

19. **vipdoc/newtick 逐笔文件布局**(sz000001 全 112 天对拍):
    `.vid` 未压缩索引, 16B 头 <IIII>=(version=2, 首日, 末日, 日数), 其后每日
    22B <IIIdH>=(日期YYYYMMDD, 解压后字节, 压缩后字节, 疑似当日均价f64, 未知)。
    `.vtc` = **每天一个 zlib 流连续拼接**(非 gzip, 非 gzip 魔数); 第 i 成员
    解压长 == vid 第 i 日 raw_size 严格相等, 顺序一致; 每段头 4B=日期 u32。
    已封装 `tdx_local/newtick.py`(read_vid/read_days, 尺寸校验)。
20. **逐笔记录体未逆向**(段头之后): 时间编码/价格定点/方向字段未知, 已存证
    样本 hex 于 newtick.py docstring 思路 —— 下一步对拍: 逐笔量合计 vs 日线
    Volume、末笔价 vs 收盘价、逐笔价与 L1 快照区间。管道已通(能解能切),
    字段逆向是独立课题, 不阻塞分笔数据的日常归档。
21. **P2 各项落地结论**: 板块文件=GBK纯文本(sectors.py, 本机 2330 板块);
    扩展市场=常量表(markets.py, ds 目录空无行情可验); F10 无本地正文缓存
    (files/f11 仅查看器资源) —— 离线解析死局; 回测 HTML 报告/report_html、
    数据体检 python -m tdx_local.audit(只 stat 不解压, 全市场归档逐文件
    解压是天级耗时, 按日对账留给单代码 check 子命令); 盯盘器 watchtower
    (快照现价字段=Now); 配方库 +3(缩量回踩/N字反包/板块动量榜)。
    numpy 加速评估: 瓶颈已在优化轮解决(全市场 20s 级), 暂不加复杂度;
    公式 DLL 台架评估: 需客户端 GUI 手工配合, Python 侧闭环弱, 暂缓。
