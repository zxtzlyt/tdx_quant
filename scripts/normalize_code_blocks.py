# -*- coding: utf-8 -*-
"""对 docs/tdx-quant-docs 镜像中的既有 markdown 代码块做统一排版(不重新抓取)。

规则与 crawl_tdx_docs.py 落盘时一致, 供规则更新后离线重刷存量文件:
  1. Tab 展开为 4 空格
  2. 去掉整块公共前导缩进
  3. 函数签名形态的代码块重排(参数对齐左括号、参数名/类型间单空格)

用法: python scripts/normalize_code_blocks.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crawl_tdx_docs import normalize_code_block  # noqa: E402

DOCS = Path(__file__).resolve().parent.parent / "docs" / "tdx-quant-docs"


def main() -> int:
    total_files = total_blocks = 0
    for fp in sorted(DOCS.rglob("*.md")):
        if fp.name == "INDEX.md":
            continue
        lines = fp.read_text(encoding="utf-8", newline="").split("\n")
        if sum(1 for l in lines if l.rstrip("\r").startswith("```")) % 2:
            print(f"WARN 围栏不配对, 跳过: {fp}")
            continue
        out, in_fence, body_start, changed = [], False, 0, 0
        for ln in lines:
            if not ln.rstrip("\r").startswith("```"):
                out.append(ln)
                continue
            if in_fence:                      # 关闭围栏: 重排 out[body_start:]
                body = "\n".join(out[body_start:])
                new = normalize_code_block(body)
                if new != body:
                    out[body_start:] = new.split("\n")
                    changed += 1
                out.append(ln)
                in_fence = False
            else:                             # 开启围栏
                out.append(ln)
                body_start = len(out)
                in_fence = True
        if changed:
            fp.write_text("\n".join(out), encoding="utf-8", newline="")
            total_files += 1
            total_blocks += changed
            print(f"{fp}  ({changed} 块)")
    print(f"=== 完成: {total_files} 个文件, {total_blocks} 个代码块 ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
