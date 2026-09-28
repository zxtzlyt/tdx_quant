# -*- coding: utf-8 -*-
"""根据爬虫结果生成 docs/tdx-quant-docs/INDEX.md 总索引。"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC_DIR = ROOT / "docs" / "tdx-quant-docs"

ORDER = ["01-tqcenter-通用函数", "02-tqcenter-行情", "03-tqcenter-财务", "04-tqcenter-板块与自选股",
         "05-tqcenter-ETF可转债期货", "06-tqcenter-公式", "07-tqcenter-交易", "08-HTTP调用",
         "09-tqs-TdxAiData", "10-lambda-pylambda", "11-常量枚举"]

HEADER = """# 通达信量化官方接口文档 · 本地镜像

> 来源: https://help.tdx.com.cn/quant/ (官方文档站) | 共 {total} 页接口文档 | 抓取脚本: scripts/crawl_tdx_docs.py (可 --force 重抓)

## 三套 API 家族怎么选

| 家族 | 调用方式 | 适用场景 | 依赖 |
|---|---|---|---|
| **tqcenter / tq** | `from tqcenter import tq` → `tq.initialize(__file__)` → `tq.xxx()` | 本地客户端策略、行情订阅、实盘交易、公式选股 | 需运行支持 TQ 的通达信客户端;全部函数亦可走 HTTP JSON-RPC(127.0.0.1:17709, method=函数名, 免py文件) |
| **tqs / TdxAiData** | `pip install tdxaidata` → `from tdxaidata import tqs` → `tqs.xxx()` | 免客户端取数: 行情/财务/专业数据/分笔/集合竞价, 跨平台 | TdxAiData.dll + Token 配置;无交易、无公式 |
| **Lambda / pylambda** | `init(context)` / `handle_bar(context, bar)` 回调 + 裸函数 `get_price`/`order`/... | 云回测/信号平台策略 | 通达信客户端内提交运行 |

关键关系: 官方文档中带星号(*)的数据接口 tqs 与 tq 签名通用; Lambda 是完全独立的第三套 API(同名函数如 get_tick_data 在两族中都存在但参数不同, 查文档时注意目录)。

## 文档目录

"""


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    results = json.loads((DOC_DIR / "_meta" / "results.json").read_text("utf-8"))["results"]
    folders: dict = {}
    for r in results:
        folders.setdefault(r["folder"], {}).setdefault(r["sub"], []).append(r)

    lines = []
    for f in ORDER:
        subs = folders.get(f, {})
        n = sum(len(v) for v in subs.values())
        lines.append(f"### {f}/ ({n}页)\n")
        for sub in sorted(subs):
            if sub:
                lines.append(f"#### {sub}\n")
            for r in sorted(subs[sub], key=lambda x: x["file"]):
                rel = Path(r["file"]).relative_to(DOC_DIR).as_posix()
                lines.append(f"- [{r['title']}]({rel})")
            lines.append("")
        lines.append("")

    out = DOC_DIR / "INDEX.md"
    out.write_text(HEADER.format(total=len(results)) + "\n".join(lines), encoding="utf-8", newline="\n")
    print(f"INDEX.md written: {len(results)} pages")


if __name__ == "__main__":
    main()
