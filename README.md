# tdx_quant — 通达信本地量化工具箱

![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)
![Dependencies](https://img.shields.io/badge/核心库依赖-0-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)

**不装 SDK、不付订阅、不爬网页** —— 用你自己的通达信终端,免费把行情和全市场财务数据搬进 Python。

- 🔌 **TqClient**:通达信 TQ 本地接口(`127.0.0.1:17709`)的 Python 客户端 —— 日K/分钟线、实时五档、板块、交易日历、分红送配,大结果自动分页续取;服务端陷阱(空信封静默、无效参数)已在客户端层补救
- 📊 **gpcw 财务文件解析**:直接解析专业财务文件(`gpcw*.dat`,FN1~FN584),1988 年至今全市场财务历史,免订阅;内置真值锚定的字段注册表与累计/单季差分
- 🗂️ **lday 日线解析与合并**:把券商定制版的全市场历史日线并入官方客户端目录,补齐"只落地看过的标的"的历史缺口
- 📈 **指标/缓存/回测三件套**:`indicators` 指标库(MACD/均线等 Python 自算 —— 公式引擎 HTTP 不可用的正解)、`kcache` 日线本地缓存(lday 二进制格式, 不复权, 支持截至某日回放)、`backtest` 选股策略回测(按调仓日切片重放防未来函数, 分红再投收益, 指数基准超额)
- 📚 **131 页官方文档镜像 + 实测笔记**:官方没写透的隐藏参数、静默空返回、数据前置条件,全部记录在案
- 🪶 **核心库零依赖**:纯标准库,克隆即用

## 为什么需要它

通达信的 TQ 量化体系能直接读客户端本地数据做量化,但实际用起来有三道坎:

| 坎 | 本仓库的解法 |
|---|---|
| 公式引擎在 HTTP 模式下不生效,`formula_*` 全部返回空 | 指标改用 Python 自算,`TqClient` 负责可靠取数 |
| 专业财务数据要付费订阅 | 官方终端可直接下载专业财务数据(实测落盘 `gpcw*.dat`);无权限时可用券商定制版(如国泰君安)免费的同格式文件 —— `gpcw.py` 直接解析 |
| 官方客户端只落地看过的标的,历史K线不全 | 券商定制版常年盘后下载全市场 `lday`,`lday.py` 按日期并集合并(重叠日以官方侧为准);深历史缺口用官网完整包 `data.tdx.com.cn/vipdoc/hsjday.zip` 补(2026-09-30 实测,见[笔记](docs/LOCAL_NOTES.md)) |
| 服务端行为陷阱:后复权随窗口起点变化、`field_list` 被忽略、无数据静默返回空 | `TqClient` 在客户端层补救(`_missing`/字段裁剪/分红换算),其余逐条记录在[实测笔记](docs/LOCAL_NOTES.md) |
| 官方文档与实际行为有出入 | [131 页接口文档完整镜像](docs/tdx-quant-docs/INDEX.md) + [实测笔记](docs/LOCAL_NOTES.md) |

## 快速开始

**前置**:Windows + 已登录的通达信金融终端(支持 TQ 的版本),TQ 服务默认开在 `http://127.0.0.1:17709/`。

```python
from tdx_local import TqClient

tq = TqClient()

# 名称 -> 代码(凡涉及证券名称先查这里, 不要凭名字猜代码)
tq.match("浦发银行")           # [{"Code": "600000.SH", "Name": "浦发银行"}]

# 新标的本地没有K线? 让客户端打开该股页面, 自动补全历史数据
tq.open_in_client("1#600000")  # 市场前缀: 0#深 1#沪 2#京

# 日K(前复权), 单次上限 24000 条, 分页已在内部自动合并
r = tq.market_data(["600000.SH"], count=120, period="1d", dividend_type="front")
closes = r["Value"]["600000.SH"]["Close"]

# 实时五档快照
tq.snapshot("600000.SH")

# 分红送配 -> {除息日: 每股税前派息(元)}, 已按每股换算, 总回报/股息率直接可用
tq.divid_factors("600519.SH")   # {"20240619": 30.876, "20241220": 23.882, ...}
```

财务历史序列(数据来自客户端专业财务下载落地的 gpcw 文件,官方终端或券商定制版均可):

```bash
# 方式一: 命令行
python -m tdx_local.gpcw "D:/券商tdx/vipdoc/cw" 600519

# 方式二: Python
python -c "from tdx_local import read_series; print(read_series('D:/券商tdx/vipdoc/cw', '600519', fields=[1, 4]))"
# FN1 基本每股收益, FN4 每股净资产
```

完整示例见 [examples/](examples/):[macd_demo.py](examples/macd_demo.py)(取K线 + Python 自算 MACD)、[financial_demo.py](examples/financial_demo.py)(财务历史序列)、[mainbusi_demo.py](examples/mainbusi_demo.py)(经营分析批量下载 + xlsx 汇总)、[http_call.py](examples/http_call.py)(不依赖 tqcenter 的本地 HTTP 直连)。

**选股/分析配方**(面向不想写代码的使用者,改文件头部参数区即可):[pick_technical.py](examples/pick_technical.py)(技术面选股+写回自定义板块)、[pick_fundamental.py](examples/pick_fundamental.py)(财报增速选股)、[market_overview.py](examples/market_overview.py)(板块强弱/全A估值/两融)、[stock_checkup.py](examples/stock_checkup.py)(单股一键体检,含分红再投总回报);DLL 插件选股的结果可用 [verify_pullback_picker.py](examples/verify_pullback_picker.py) 做 Python 同口径对账。**策略验证与数据积累**:[backtest_picker.py](examples/backtest_picker.py)(把选股策略放到历史上逐日重放, 统计持有 5/20/60 日的分红再投回报与上证超额)、[archive_minutes.py](examples/archive_minutes.py)(每天收盘后跑一次把分钟K增量归档成 CSV, 坚持攒就能突破客户端约 100 天的分钟留存上限)、[archive_minutes_vipdoc.py](examples/archive_minutes_vipdoc.py)(直读 vipdoc 的二进制归档, 转 GUI 截掉 .5 两年窗口/分钟百天窗口都不影响归档, 支持全市场)。

跑一遍实测用例确认环境(离线组不需要客户端;在线组在 TQ 服务不可达时自动整组跳过):

```bash
python -m pytest tests/ -v
```

依赖本机真实数据的用例默认指向作者的数据目录,其他机器可用环境变量 `TDX_CW_DIR` / `TDX_GTJA_CW` / `TDX_GTJA_LDAY` 覆盖,目录缺失时这些用例自动跳过(见 [conftest.py](tests/conftest.py))。CI(Windows, Python 3.9/3.12/3.14)在每次推送与 PR 时自动跑全部用例的离线部分。

## 安装

核心库零依赖,克隆后在本仓库根目录直接 import 即可:

```bash
git clone https://github.com/zxtzlyt/tdx_quant.git
```

`requirements.txt`(beautifulsoup4、html2text)只在重新抓取文档镜像时才需要;跑测试可选装 `pytest`。

## 文档

- **[实测笔记 LOCAL_NOTES](docs/LOCAL_NOTES.md)** —— 先读这个,少踩坑:哪些接口实测可用、隐藏参数、空返回排查、免费 J_ 字段清单
- **[官方文档镜像 INDEX](docs/tdx-quant-docs/INDEX.md)** —— 131 页接口文档离线版,含参数表、返回字段、代码示例,已做排版规范化
- 官方文档更新后可重抓:`python scripts/crawl_tdx_docs.py --force && python scripts/gen_index.py`

## 避坑速查(详见实测笔记)

1. 接口只读本地数据 —— 新标的先 `open_in_client()` 触发客户端下载,再取数
2. `get_market_data` 大结果分页协议已在 `TqClient` 内自动合并,调用方拿到的始终是完整数据
3. `dividend_type="back"` 以请求窗口首日为基准 —— 跨窗口拼接会算错,单窗口区间回报不受影响;跨窗口场景改用"不复权价链 + `divid_factors()` 分红再投"
4. 本地无数据的标的静默返回空 —— `market_data()` 已把这类代码移入 `result["_missing"]`;分钟线尤其要先确认本地已落地
5. `get_market_data` 的 `field_list` 服务端会忽略 —— `market_data()` 已在客户端按参数裁剪,并剥离每股混入的 `ErrorId`
6. `get_stock_info` 的返回字段平铺在顶层(不在 `Value` 里),`field_list` 必须用文档精确字段名
7. `get_financial_data` 需要文档未记载的 `table_list`/`report_type`/`start_time`/`end_time` 参数;**`table_list` 必须等于 `field_list`**(2026-09-30 实测推翻"HTTP 数值通道关闭"旧结论) —— 补齐后 FN 数值 HTTP 全通
8. `refresh_kline` 只能喂 `get_market_data` 的缓存,喂不到公式引擎
9. 64 位通达信只能加载 64 位 DLL;官方规范自带的示例 DLL 全是 32 位(含名字带 64 的)——自用需 MSVC 自行编译 64 位(实测记录见[笔记](docs/LOCAL_NOTES.md))
10. `create_sector`/`send_user_block` 的**中文板块名**经 HTTP 会损坏客户端板块表(非法字节),板块简称用英文;`TqClient` 已对网关返回的非法 UTF-8 做容错

## 目录结构

```
tdx_quant/
├── tdx_local/                    # 核心包(纯标准库, 零依赖)
│   ├── __init__.py               # 包入口, 导出 TqClient / read_series 等
│   ├── tq_client.py              # TQ HTTP JSON-RPC 客户端(自动分页续取)
│   ├── cw_fields.py              # 财务字段注册表(锚定校准/单位/单季陷阱/缺失登记)
│   ├── lday.py                   # 日线文件解析与合并同步
│   ├── gpcw.py                   # 专业财务文件解析器(历史序列/单季差分/目录同步)
│   ├── indicators.py             # 技术指标库(MACD/均线/RSI/KDJ/BOLL/ATR/金叉/分红送转再投)
│   ├── kcache.py                 # 日线本地缓存(lday 格式, 不复权, 增量同步, 截至某日回放)
│   ├── backtest.py               # 选股策略回测(调仓日重放/防未来函数/成本/卖出条件/分年)
│   ├── factor.py                 # 因子评测(RankIC/ICIR/分层/多空价差)
│   ├── ratios.py                 # 财务衍生比率层(现成槽位+组合注册表)
│   ├── sectors.py                # 板块文件解析(hq_cache 定义板块+blocknew 自定义板块)
│   ├── limits.py                 # 涨停/连板判定与复盘(交易所四舍五入口径)
│   ├── event_study.py            # 事件研究(除息/自定义事件前后漂移)
│   ├── portfolio.py              # 组合层(波动率倒数权重/相关性/净值曲线)
│   ├── markets.py                # 扩展市场常量表(港股/美股/期货等 20 市场枚举)
│   ├── newtick.py                # newtick 逐笔读取层(vid 索引/vtc 逐日 zlib, 实验性)
│   ├── audit.py                  # 数据体检(python -m tdx_local.audit)
│   └── report_html.py            # 回测结果 HTML 报告(SVG 净值曲线)
├── examples/                     # 可运行示例
│   ├── macd_demo.py              # 取K线 + Python 自算 MACD
│   ├── financial_demo.py         # 财务历史序列示例
│   ├── mainbusi_demo.py          # 经营分析批量下载 + xlsx 汇总
│   ├── http_call.py              # 不依赖 tqcenter 的本地 HTTP 直连
│   ├── pick_technical.py         # 配方: 技术面选股(金叉/多头/放量, 写回自定义板块)
│   ├── pick_fundamental.py       # 配方: 财报增速选股(HTTP FN 通道)
│   ├── market_overview.py        # 配方: 板块强弱/全A估值/两融余额
│   ├── stock_checkup.py          # 配方: 单股一键体检(含分红再投总回报)
│   ├── verify_pullback_picker.py # 配方: DLL 选股器×Python 同口径交叉对账
│   ├── backtest_picker.py        # 配方: 策略历史回测(重放/超额统计)
│   ├── archive_minutes.py        # 配方: 分钟线归档(TQ/CSV 版)
│   ├── archive_minutes_vipdoc.py # 配方: vipdoc 直读二进制归档(gzip, 防转档截窗)
│   ├── daily_pipeline.py         # 配方: 盘后一条龙(分钟归档+lday合并+日K增量)
│   ├── limit_up_review.py        # 配方: 涨停/连板复盘(kcache 全池)
│   ├── watchtower.py             # 配方: 盘中盯盘器(批量快照轮询+阈值提示)
│   ├── pick_pullback.py          # 配方: 缩量回踩 10 日线选股
│   ├── pick_nshape.py            # 配方: N 字反包选股
│   └── pick_sector_momentum.py   # 配方: 板块动量榜
├── tests/                        # 实测用例(pytest)
│   ├── test_offline.py           # 解析/mock 逻辑, 不依赖客户端在线
│   ├── test_live.py              # TQ 在线接口(服务离线时自动整组跳过)
│   └── test_guide_examples.py    # 配方示例配套测试(离线+在线)
├── scripts/                      # 镜像维护工具
│   ├── crawl_tdx_docs.py         # 官方文档镜像爬虫
│   ├── gen_index.py              # 总索引生成
│   ├── normalize_code_blocks.py  # 代码块离线重排(Tab/缩进/签名对齐)
│   └── audit_docs.py             # 镜像体检(结构/表格/链接全量检查)
├── docs/                         # 文档
│   ├── LOCAL_NOTES.md            # 本机实测笔记(先读这个,细节与坑都在这里)
│   └── tdx-quant-docs/           # 官方文档镜像(131页) + INDEX.md
├── requirements.txt              # 仅文档镜像爬虫需要; 核心库零依赖
├── LICENSE                       # MIT; docs/tdx-quant-docs/ 版权归通达信
└── README.md
```

## 兼容性

Windows 11 · Python 3.14 实测(核心库仅用标准库,3.9+ 理论可用)· 通达信金融终端64 v7.73(TQ 已开启,专业财务/K线数据自行下载)· 券商定制版通达信(可选的免费数据源)· 2026-09 全量实测

## 许可

代码部分 [MIT](LICENSE);`docs/tdx-quant-docs/` 镜像内容版权归通达信所有,仅供学习研究,侵权请联系移除。

---

**免责声明**:本项目为个人学习研究用途的非官方工具,与通达信(财富趋势科技)无任何关联。数据均来自本地客户端,准确性以官方为准;股市有风险,本项目不构成任何投资建议。
