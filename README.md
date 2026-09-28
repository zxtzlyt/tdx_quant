# tdx_quant — 通达信 TQ 本地量化工具箱

不联网云 API、不订阅付费数据,基于**本机通达信终端**做量化取数与分析。

> 声明:本项目为个人学习研究用途的非官方工具,与通达信(财富趋势科技)无任何关联;
> 股市有风险,代码不构成投资建议。

## 它解决什么问题

通达信 2026 年推出的 TQ 量化体系(`tq.*` 接口 + 本机 `127.0.0.1:17709` HTTP 服务)
可以直接读**客户端本地数据**做行情与量化,但有三道坎,本仓库逐一解决:

1. **公式引擎在 HTTP 模式下不生效**(`formula_*` 全部返回空)→ 指标改用 Python 自算,
   本仓库提供取数客户端
2. **专业财务数据要付费订阅** → 发现券商定制版通达信(如国泰君安)盘后下载免费提供
   同格式财务文件,提供 `gpcw*.dat` 解析器(FN1~FN584 字段,1988 年至今全市场)
3. **官方文档与实际行为有出入** → 131 页接口文档完整镜像 + 一份实测笔记(LOCAL_NOTES),
   把隐藏参数、静默空返回、数据前置条件全部记录在案

## 三条数据通道

| 通道 | 内容 | 依赖 |
|---|---|---|
| `TqClient`(HTTP 17709) | 日K/分钟线、实时快照(五档)、板块、交易日历、除权、证券检索、驱动客户端 | 通达信金融终端(支持TQ版本)运行中 |
| `tdx_local.gpcw` | 专业财务历史序列(FN1~FN584: 每股收益、净资产、总资产…) | 任意通达信家族客户端的 `vipdoc/cw/gpcw*.dat` |
| `get_stock_info` 的 J_ 字段 | 免费的最新一期财务摘要(34个字段) | 同通道1 |

## 安装

```bash
pip install -r requirements.txt   # 仅文档爬虫需要; tdx_local 本体零依赖(纯标准库)
```

前置条件:安装并登录**支持 TQ 策略的通达信金融终端**(官方 `tq.*` 体系),
配置好 `TDX_TQ_URL` 环境变量或使用默认 `http://127.0.0.1:17709/`。

## 快速开始

```python
from tdx_local import TqClient

tq = TqClient()
tq.match("浦发银行")                        # 名称->代码, [{"Code":"600000.SH","Name":"浦发银行"}]
tq.open_in_client("1#600000")               # 让客户端打开个股页面, 自动补历史数据
r = tq.market_data(["600000.SH"], count=120, period="1d", dividend_type="front")
closes = r["Value"]["600000.SH"]["Close"]   # 大结果分页已自动续取合并
```

```bash
# 财务历史序列(每股收益/净资产), 数据来自券商版通达信下载的 gpcw 文件
python examples/financial_demo.py "D:/券商tdx/vipdoc/cw" 600519

# 完整 demo: 取K线 + Python 自算 MACD
python examples/macd_demo.py 600000.SH

# 重新生成官方文档镜像(131页 markdown, 官方更新后可随时重抓)
python scripts/crawl_tdx_docs.py && python scripts/gen_index.py
```

## 文档镜像与版权声明

[`docs/tdx-quant-docs/`](docs/tdx-quant-docs/INDEX.md) 是官方量化文档站
`https://help.tdx.com.cn/quant/` 的离线镜像(131 页接口文档,含参数表/返回字段/代码示例,
文件头部均注明原文 URL)。

- **版权归 通达信(财富趋势科技) 所有**,本镜像仅供学习研究,如有侵权请提交 issue,
  将立即移除;也可删除该目录后用 `scripts/crawl_tdx_docs.py` 自行生成
- [`docs/LOCAL_NOTES.md`](docs/LOCAL_NOTES.md) 是本机实测笔记(自有内容,和官方文档互补):
  隐藏参数、公式引擎的坑、数据落地前置条件、空返回排查、免费 J_ 字段清单

## 实测要点(详见 LOCAL_NOTES)

- 接口只读本地 → 新标的先 `open_in_client()` 触发客户端下载,再取数
- `get_market_data` 单次上限 24000 条,分页协议已在 `TqClient` 内自动合并
- `get_stock_info` 返回字段平铺在顶层(不在 `Value`),且 `field_list` 必须用文档精确字段名
- `get_financial_data` 需要文档未记载的 `table_list`/`report_type` 隐藏参数,
  且数值通道在 HTTP 模式下返回 null → 财务数值一律走 `gpcw` 文件解析

## 目录结构

```
tdx_local/            核心库(纯标准库)
  tq_client.py        TQ HTTP JSON-RPC 客户端(自动分页续取)
  gpcw.py             专业财务文件解析器(FN1~FN584, 支持历史序列)
examples/             macd_demo.py / financial_demo.py
docs/
  LOCAL_NOTES.md      实测笔记(先读这个, 少踩坑)
  tdx-quant-docs/     官方文档镜像 + INDEX.md 总索引
scripts/              crawl_tdx_docs.py(镜像爬虫) / gen_index.py(索引生成)
                      normalize_code_blocks.py(代码块离线重排) / audit_docs.py(镜像体检)
```

## 测试环境

Windows 11 x64 · Python 3.14 · 通达信金融终端64 v7.73(TQ 已开启) · 券商定制版通达信(财务文件来源) · 2026-09 全部实测

## 许可

代码部分 [MIT](LICENSE);`docs/tdx-quant-docs/` 内文档内容版权归通达信所有(见上)。
