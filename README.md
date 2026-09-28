# tdx_quant — 通达信本地量化工具箱

![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)
![Dependencies](https://img.shields.io/badge/核心库依赖-0-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)

**不装 SDK、不付订阅、不爬网页** —— 用你自己的通达信终端,免费把行情和全市场财务数据搬进 Python。

- 🔌 **TqClient**:通达信 TQ 本地接口(`127.0.0.1:17709`)的 Python 客户端 —— 日K/分钟线、实时五档、板块、交易日历,大结果自动分页续取
- 📊 **gpcw 解析器**:直接解析通达信专业财务文件(`gpcw*.dat`,FN1~FN584 字段),1988 年至今全市场财务历史,免订阅
- 📚 **131 页官方文档镜像 + 实测笔记**:官方没写透的隐藏参数、静默空返回、数据前置条件,全部记录在案
- 🪶 **核心库零依赖**:纯标准库,克隆即用

## 为什么需要它

通达信的 TQ 量化体系能直接读客户端本地数据做量化,但实际用起来有三道坎:

| 坎 | 本仓库的解法 |
|---|---|
| 公式引擎在 HTTP 模式下不生效,`formula_*` 全部返回空 | 指标改用 Python 自算,`TqClient` 负责可靠取数 |
| 专业财务数据要付费订阅 | 券商定制版通达信(如国泰君安)盘后下载免费提供同格式财务文件,`gpcw.py` 直接解析 |
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
```

财务历史序列(数据来自券商版通达信下载的 gpcw 文件):

```bash
# 方式一: 命令行
python -m tdx_local.gpcw "D:/券商tdx/vipdoc/cw" 600519

# 方式二: Python
python -c "from tdx_local import read_series; print(read_series('D:/券商tdx/vipdoc/cw', '600519', fields=[1, 4]))"
# FN1 基本每股收益, FN4 每股净资产
```

完整示例见 [examples/](examples/):[macd_demo.py](examples/macd_demo.py)(取K线 + Python 自算 MACD)、[financial_demo.py](examples/financial_demo.py)(财务历史序列)。

## 安装

核心库零依赖,克隆后在本仓库根目录直接 import 即可:

```bash
git clone https://github.com/zxtzlyt/tdx_quant.git
```

`requirements.txt`(beautifulsoup4、html2text)只在重新抓取文档镜像时才需要。

## 文档

- **[实测笔记 LOCAL_NOTES](docs/LOCAL_NOTES.md)** —— 先读这个,少踩坑:哪些接口实测可用、隐藏参数、空返回排查、免费 J_ 字段清单
- **[官方文档镜像 INDEX](docs/tdx-quant-docs/INDEX.md)** —— 131 页接口文档离线版,含参数表、返回字段、代码示例,已做排版规范化
- 官方文档更新后可重抓:`python scripts/crawl_tdx_docs.py --force && python scripts/gen_index.py`

## 避坑速查(详见实测笔记)

1. 接口只读本地数据 —— 新标的先 `open_in_client()` 触发客户端下载,再取数
2. `get_market_data` 大结果分页协议已在 `TqClient` 内自动合并,调用方拿到的始终是完整数据
3. `get_stock_info` 的返回字段平铺在顶层(不在 `Value` 里),`field_list` 必须用文档精确字段名
4. `get_financial_data` 需要文档未记载的 `table_list`/`report_type` 参数,且数值通道在 HTTP 模式下返回 null —— 财务数值一律走 `gpcw` 文件解析
5. `refresh_kline` 只能喂 `get_market_data` 的缓存,喂不到公式引擎

## 目录结构

```
tdx_quant/
├── tdx_local/                # 核心包(纯标准库, 零依赖)
│   ├── __init__.py           # 包入口, 导出 TqClient / read_series
│   ├── tq_client.py          # TQ HTTP JSON-RPC 客户端(自动分页续取)
│   └── gpcw.py               # 专业财务文件解析器(FN1~FN584, 历史序列)
├── examples/                 # 可运行示例
│   ├── macd_demo.py          # 取K线 + Python 自算 MACD
│   └── financial_demo.py     # 财务历史序列示例
├── scripts/                  # 镜像维护工具
│   ├── crawl_tdx_docs.py     # 官方文档镜像爬虫
│   ├── gen_index.py          # 总索引生成
│   ├── normalize_code_blocks.py  # 代码块离线重排(Tab/缩进/签名对齐)
│   └── audit_docs.py         # 镜像体检(结构/表格/链接全量检查)
├── docs/                     # 文档
│   ├── LOCAL_NOTES.md        # 本机实测笔记(先读这个)
│   └── tdx-quant-docs/       # 官方文档镜像(131页) + INDEX.md
├── requirements.txt          # 仅文档镜像爬虫需要; 核心库零依赖
├── LICENSE                   # MIT; docs/tdx-quant-docs/ 版权归通达信
└── README.md
```

## 兼容性

Windows 11 · Python 3.14 实测(核心库仅用标准库,3.9+ 理论可用)· 通达信金融终端64 v7.73(TQ 已开启)· 券商定制版通达信(财务文件来源)· 2026-09 全量实测

## 许可

代码部分 [MIT](LICENSE);`docs/tdx-quant-docs/` 镜像内容版权归通达信所有,仅供学习研究,侵权请联系移除。

---

**免责声明**:本项目为个人学习研究用途的非官方工具,与通达信(财富趋势科技)无任何关联。数据均来自本地客户端,准确性以官方为准;股市有风险,本项目不构成任何投资建议。
