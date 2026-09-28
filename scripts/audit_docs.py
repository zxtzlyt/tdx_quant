# -*- coding: utf-8 -*-
"""对 docs/ 下的 markdown 做全面体检(只报告, 不修改)。

检查项:
  结构: 围栏配对 / 空文件 / 无H1 / 多个H1 / 行尾空白 / 换行符风格
  代码块: 残留Tab / 公共前导缩进 / 签名块内错位多空格
  正文: 残留HTML实体 / 残留HTML标签 / 不间断空格
  表格: 同一表内各行列数不一致
  链接: 空目标 / 站内相对链接指向不存在的文件
  索引: INDEX.md 与实际文件互相覆盖

用法: python scripts/audit_docs.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC_DIR = ROOT / "docs"
MIRROR = DOC_DIR / "tdx-quant-docs"

FENCE_RE = re.compile(r"^```")
SIG_HEAD_RE = re.compile(r"^(async\s+def\s+\w+|def\s+\w+|\w+)\s*\(")
SIG_TAIL_RE = re.compile(r"\)\s*(->\s*[^:]+)?:\s*$")
ENTITY_RE = re.compile(r"&#?\w+;")
TAG_RE = re.compile(r"</?[a-zA-Z][a-zA-Z0-9-]*(\s[^<>]*)?/?>")
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]*)\)")
IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)\s]*)\)")
SPLIT_PIPE_RE = re.compile(r"(?<!\\)\|")


def iter_segments(lines):
    """把文件切成 (kind, lines) 片段, kind in {'prose','code'}; 围栏行归入 code。"""
    cur, in_fence, lang = [], False, ""
    for ln in lines:
        if FENCE_RE.match(ln.rstrip("\r")):
            if in_fence:
                yield "code", lang, cur
                cur, in_fence = [], False
            else:
                yield "prose", "", cur
                cur, in_fence, lang = [], True, ln.strip()[3:]
        else:
            cur.append(ln)
    yield "code" if in_fence else "prose", lang, cur


def common_indent(block_lines):
    ind = [len(l) - len(l.lstrip(" \t")) for l in block_lines if l.strip()]
    return min(ind) if ind else 0


def internal_multispace(line):
    cnt, q, i, n = 0, None, 0, len(line)
    while i < n:
        c = line[i]
        if q:
            if c == "\\":
                i += 2
                continue
            if c == q:
                q = None
        elif c in "'\"":
            q = c
        elif c == " ":
            j = i
            while j < n and line[j] == " ":
                j += 1
            if j - i >= 2 and i > 0:
                cnt += 1
            i = j
            continue
        i += 1
    return cnt


def audit_file(fp: Path, findings: dict) -> None:
    raw = fp.read_text(encoding="utf-8", newline="")
    rel = str(fp.relative_to(ROOT))
    lines = raw.split("\n")
    crlf = "\r\n" in raw

    def add(key, detail=""):
        findings.setdefault(key, []).append(f"{rel}{(' :: ' + detail) if detail else ''}")

    if raw.count("\n") and raw.count("\n") == len([1 for l in lines if l.endswith("\r")]):
        pass  # 全CRLF, 单独在 crlf 计数
    fence_lines = sum(1 for l in lines if FENCE_RE.match(l.rstrip("\r")))
    if fence_lines % 2:
        add("围栏不配对")
    h1_lines, prose_lines = [], []
    for kind, lang, seg in iter_segments(lines):
        seg_text = "\n".join(seg)
        if kind == "code":
            if "\t" in seg_text:
                add("代码块残留Tab")
            if common_indent(seg) > 0:
                add("代码块公共前导缩进")
            if lang == "python":
                joined = " ".join(l.strip() for l in seg if l.strip())
                if SIG_HEAD_RE.match(joined) and SIG_TAIL_RE.search(joined):
                    if sum(internal_multispace(l) for l in seg) > 0:
                        add("签名块内错位多空格")
            for m in ENTITY_RE.finditer(seg_text):
                add("代码块内HTML实体", m.group(0))
        else:
            prose_lines.extend(seg)
            h1_lines.extend(l for l in seg if l.startswith("# "))
            for m in ENTITY_RE.finditer(seg_text):
                add("正文HTML实体", m.group(0))
            for m in TAG_RE.finditer(seg_text):
                add("正文HTML标签", m.group(0))
            if "\xa0" in seg_text:
                add("正文不间断空格", f"{seg_text.count(chr(160))}处")
    if crlf:
        add("CRLF行尾")
    if any(l.rstrip("\r") != l.rstrip() and l.strip() for l in lines):
        add("行尾空白")
    if len(raw) < 120:
        add("疑似空文件", f"{len(raw)}字节")
    if not h1_lines:
        add("无H1标题")
    if len(h1_lines) > 1:
        add("多个H1", str(len(h1_lines)))
    body = "\n".join(prose_lines)
    # 表格列数一致性
    table, prev_cols = [], None
    def flush_table():
        nonlocal table, prev_cols
        if len(table) >= 2:
            cols = {len(SPLIT_PIPE_RE.split(r)) - 1 for r in table}
            if len(cols) > 1:
                add("表格列数不一致", f"{len(table)}行, 列数{sorted(cols)}")
        table, prev_cols = [], None
    for l in lines:
        ls = l.rstrip("\r").rstrip()
        if ls.startswith("|"):
            table.append(ls)
        elif table:
            flush_table()
    if table:
        flush_table()
    # 链接与图片
    for m in LINK_RE.finditer(body):
        target = m.group(2)
        if not target:
            add("链接目标为空", m.group(0)[:40])
        elif not target.startswith(("http://", "https://", "#", "mailto:")):
            if not (fp.parent / target).resolve().exists():
                add("站内链接失效", target)
    for m in IMG_RE.finditer(body):
        target = m.group(2)
        if not target.startswith(("http://", "https://")):
            if not (fp.parent / target).resolve().exists():
                add("本地图片缺失", target)


def audit_index(findings: dict) -> None:
    index = MIRROR / "INDEX.md"
    if not index.exists():
        findings.setdefault("INDEX缺失", []).append(str(index))
        return
    text = index.read_text(encoding="utf-8")
    linked = set()
    for m in LINK_RE.finditer(text):
        t = m.group(2)
        if t.endswith(".md"):
            linked.add(t.replace("\\", "/").lower())
            if not (MIRROR / t).resolve().exists():
                findings.setdefault("INDEX链接失效", []).append(t)
    actual = {str(p.relative_to(MIRROR)).replace("\\", "/").lower()
              for p in MIRROR.rglob("*.md") if p.name != "INDEX.md"}
    for miss in sorted(actual - linked):
        findings.setdefault("未入INDEX的文件", []).append(miss)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    findings: dict = {}
    files = [p for p in DOC_DIR.rglob("*.md") if "_meta" not in p.parts]
    for fp in sorted(files):
        audit_file(fp, findings)
    audit_index(findings)
    if not findings:
        print(f"ALL PASS  ({len(files)} 个文件)")
        return 0
    print(f"检查 {len(files)} 个文件, 发现 {len(findings)} 类问题:\n")
    for key in sorted(findings):
        items = findings[key]
        print(f"[{key}] {len(items)} 处")
        for it in items[:6]:
            print(f"    {it}")
        if len(items) > 6:
            print(f"    ... 及另外 {len(items) - 6} 处")
    return 0


if __name__ == "__main__":
    sys.exit(main())
