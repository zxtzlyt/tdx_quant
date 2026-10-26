# -*- coding: utf-8 -*-
"""回测结果 HTML 报告 —— 零依赖拼一份带净值曲线(SVG)与统计表的网页。

面向"回测完想给别人/未来的自己看一眼"的场景: backtest.run 的 result 直接
渲染, summary/yearly 两张表 + 每个持有期一条批次净值曲线 + 逐笔明细前 N 行。

用法::

    from tdx_local import backtest, report_html

    result = backtest.run(...)
    report_html.render_backtest_html(result, "backtest.html")
"""
import html
import time

from . import backtest

__all__ = ["render_backtest_html"]

_CSS = """body{font-family:system-ui,'Microsoft YaHei',sans-serif;margin:2em;
color:#222;max-width:960px}h2{border-bottom:2px solid #345;margin-top:1.6em}
table{border-collapse:collapse;font-size:14px}td,th{border:1px solid #ccc;
padding:4px 10px}th{background:#eef}code{background:#f4f4f4;padding:0 4px}
.up{color:#c00}.down{color:#070}.meta{color:#666;font-size:13px}"""


def _esc(v):
    return html.escape(str(v))


def _svg_curve(curve, width=880, height=140):
    """[(卖出日, 净值)] -> SVG 折线(自适应 y 范围)。"""
    if not curve:
        return "<p class='meta'>(无净值数据)</p>"
    xs = [i for i, _ in enumerate(curve)]
    ys = [nav for _, nav in curve]
    y0, y1 = min(ys), max(ys)
    if y1 - y0 < 1e-9:
        y0, y1 = y0 - 0.5, y1 + 0.5
    pad = 6
    pts = " ".join(
        f"{pad + x * (width - 2 * pad) / max(len(curve) - 1, 1):.1f},"
        f"{height - pad - (y - y0) * (height - 2 * pad) / (y1 - y0):.1f}"
        for x, y in zip(xs, ys))
    return (f"<svg width='{width}' height='{height}' role='img'>"
            f"<polyline fill='none' stroke='#1a5fb4' stroke-width='2' points='{pts}'/>"
            f"<text x='{pad}' y='{14}' font-size='11' fill='#666'>max {y1:.3f}"
            f" | min {y0:.3f} | 末端 {ys[-1]:.3f}</text></svg>")


def _cls(v):
    return "up" if v > 0 else "down" if v < 0 else ""


def render_backtest_html(result, path, title="回测报告") -> str:
    """backtest.run 的 result -> HTML 文件; 返回文件路径字符串。"""
    s = result["summary"]
    parts = [f"<!doctype html><meta charset='utf-8'><title>{_esc(title)}</title>",
             f"<style>{_CSS}</style>",
             f"<h1>{_esc(title)}</h1>",
             f"<p class='meta'>共 {len(result['picks'])} 笔选股(去重前), "
             f"跳过 {sum(result['skipped'].values())} 次; "
             f"生成于 {time.strftime('%Y-%m-%d %H:%M')}</p>",
             "<h2>汇总(按持有期)</h2><table><tr><th>持有期</th><th>笔数</th>"
             "<th>胜率%</th><th>平均%</th><th>中位%</th><th>平均超额%</th>"
             "<th>超额胜率%</th></tr>"]
    for h, m in s.items():
        if m.get("n", 0) == 0:
            continue
        ae = "--" if m["avg_excess"] is None else f"{m['avg_excess']:+.2f}"
        ew = "--" if m["excess_win"] is None else f"{m['excess_win']:.1f}"
        parts.append(f"<tr><td>{h}日</td><td>{m['n']}</td>"
                     f"<td>{m['win']:.1f}</td>"
                     f"<td class='{_cls(m['avg'])}'>{m['avg']:+.2f}</td>"
                     f"<td class='{_cls(m['med'])}'>{m['med']:+.2f}</td>"
                     f"<td>{ae}</td><td>{ew}</td></tr>")
    parts.append("</table>")

    yearly = result.get("yearly") or {}
    if any(yearly.values()):
        parts.append("<h2>分年(按卖出日)</h2><table><tr><th>持有期</th><th>年份</th>"
                     "<th>笔数</th><th>胜率%</th><th>平均%</th><th>平均超额%</th></tr>")
        for h, rows in yearly.items():
            for year, m in sorted(rows.items()):
                ae = "--" if m["avg_excess"] is None else f"{m['avg_excess']:+.2f}"
                parts.append(f"<tr><td>{h}日</td><td>{_esc(year)}</td><td>{m['n']}</td>"
                             f"<td>{m['win']:.1f}</td>"
                             f"<td class='{_cls(m['avg'])}'>{m['avg']:+.2f}</td>"
                             f"<td>{ae}</td></tr>")
        parts.append("</table>")

    curve = result.get("curve") or {}
    if any(curve.values()):
        parts.append("<h2>批次净值曲线(每批等权、全额再投近似)</h2>")
        for h, c in curve.items():
            parts.append(f"<h3>持有 {h} 日</h3>{_svg_curve(c)}")

    if s:
        h0 = next(iter(s))
        picks = sorted(result["picks"], key=lambda p: p["ret"].get(h0) or 0)
        parts.append(f"<h2>逐笔明细(按持有 {h0} 日收益排序, 最多 50 行)</h2>"
                     "<table><tr><th>调仓日</th><th>代码</th><th>卖出日</th>"
                     "<th>收益%</th><th>超额%</th></tr>")
        for p in picks[:50]:
            sd = p.get("sell_date", {}).get(h0, "--")
            r = p["ret"].get(h0)
            e = p.get("excess", {}).get(h0)
            r_cell = "--" if r is None else f"<td class='{_cls(r)}'>{r:+.2f}</td>"
            e_cell = "--" if e is None else f"{e:+.2f}"
            parts.append(f"<tr><td>{p['date']}</td><td><code>{_esc(p['code'])}</code></td>"
                         f"<td>{_esc(sd)}</td>{r_cell}<td>{e_cell}</td></tr>")
        parts.append("</table>")
    text = "\n".join(parts)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return str(path)
