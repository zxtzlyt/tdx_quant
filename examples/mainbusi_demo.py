# -*- coding: utf-8 -*-
"""通达信 TQ download_file(down_type=5) —— 经营分析数据批量下载与汇总。

用法(仓库根目录):
    python examples/mainbusi_demo.py                 # 默认 600519.SH, 2020 至今
    python examples/mainbusi_demo.py 600519.SH 000001.SZ

行为: 逐年调用 download_file(down_type=5) 下载经营分析文件
(<通达信安装目录>\\PYPlugins\\data\\mainbusi<代码>_<年份>.json), 解析后
合并写入一个 xlsx(明细 + 主营简介两个 sheet); 无 openpyxl 时退回 CSV。

实测要点(2026-09, 通达信金融终端64 v7.73):
- down_time 必须是完整日期 YYYYMMDD, 只取其年份(传 "2024" 报 down_time error);
  本脚本统一传年中 0630, 规避未来日期问题
- 文件内容 list[{"zygc": "<json字符串>"}], 内层 JSON 缺最后一个 "}", 需配平补齐
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tdx_local import TqClient  # noqa: E402

START_YEAR = 2020


def find_tdx_dir():
    """从注册表卸载项找通达信安装目录, 兜底扫常见路径; 找不到返回 None。"""
    import winreg
    for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        for base in (r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                     r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"):
            try:
                hive_key = winreg.OpenKey(hive, base)
            except OSError:
                continue
            with hive_key:
                for n in range(winreg.QueryInfoKey(hive_key)[0]):
                    try:
                        with winreg.OpenKey(hive_key, winreg.EnumKey(hive_key, n)) as sub:
                            if "通达信" not in winreg.QueryValueEx(sub, "DisplayName")[0]:
                                continue
                            for attr in ("InstallLocation", "DisplayIcon"):
                                try:
                                    loc = winreg.QueryValueEx(sub, attr)[0]
                                except OSError:
                                    continue
                                loc = loc.split(",")[0].strip('" ')  # DisplayIcon 常带 ,0 后缀
                                if loc.lower().endswith(".exe"):
                                    loc = str(Path(loc).parent)
                                if Path(loc, "TdxW.exe").exists():
                                    return loc
                    except OSError:
                        continue
    for cand in ("C:/new_tdx", "D:/new_tdx", "C:/tdxW", "D:/tdxW"):
        if Path(cand, "TdxW.exe").exists():
            return cand
    return None


def _loads_zygc(s):
    """解析 zygc 内层 JSON; 通达信导出的串缺最后一个 "}", 按括号配平补齐后重试。"""
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    stack, instr, esc = [], False, False
    for ch in s:
        if instr:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                instr = False
        elif ch == '"':
            instr = True
        elif ch in "{[":
            stack.append(ch)
        elif ch in "}]":
            if stack:
                stack.pop()
    return json.loads(s + "".join("}" if c == "{" else "]" for c in reversed(stack)))


def download_year(stock_code, year, tdx_dir):
    """down_type=5 下载某年度经营分析, 返回落盘文件路径。"""
    r = TqClient().call("download_file", stock_code=stock_code,
                        down_time=f"{year}0630", down_type=5)
    if r.get("ErrorId") != "0":
        raise RuntimeError(str(r))
    name = f"mainbusi{stock_code.split('.')[0]}_{year}.json"
    path = Path(tdx_dir) / "PYPlugins" / "data" / name
    for _ in range(10):  # 正常同步返回即已落盘, 轮询只作兜底
        if path.exists():
            return path
        time.sleep(1)
    raise FileNotFoundError(path)


def parse_mainbusi(path, stock_code):
    """解析单个年度文件, 返回 (主营简介dict, 明细行list)。"""
    items = json.loads(Path(path).read_text(encoding="utf-8"))
    intro, rows = {}, []
    for item in items:
        z = _loads_zygc(item["zygc"])
        if "产品名称" in z:  # 首条: 公司主营简介
            intro.update(z)
            continue
        for period, dims in z.items():  # 其余每条: 一个报告期
            for dim, entries in dims.items():  # 维度: 按产品(项目)/按行业/按地区
                rows.extend({"股票": stock_code, "报告期": period,
                             "分类维度": dim, **e} for e in entries)
    return intro, rows


def num(v):
    """字符串数值转 float, 空串转 None。"""
    return float(v) if v not in ("", None) else None


def save_xlsx(intros, rows, out_path):
    from openpyxl import Workbook
    from openpyxl.styles import Font
    cols = ["股票", "报告期", "分类维度", "主营构成", "主营收入(元)", "收入比例%",
            "主营成本", "成本比例%", "毛利", "利润比例%", "毛利率%"]
    num_cols = {"主营收入(元)", "收入比例%", "主营成本", "成本比例%",
                "毛利", "利润比例%", "毛利率%"}
    wb = Workbook()
    ws = wb.active
    ws.title = "经营分析明细"
    ws.append(cols)
    for c in ws[1]:
        c.font = Font(bold=True)
    for r in sorted(rows, key=lambda x: x["报告期"]):
        ws.append([num(r[c]) if c in num_cols else r[c] for c in cols])
    ws.freeze_panes = "A2"
    for i in range(1, len(cols) + 1):
        ws.column_dimensions[ws.cell(1, i).column_letter].width = 14
    ws2 = wb.create_sheet("主营简介")
    ws2.append(["股票", "产品名称", "主营构成"])
    for c in ws2[1]:
        c.font = Font(bold=True)
    for code, intro in intros.items():
        ws2.append([code, intro.get("产品名称", ""), intro.get("主营构成", "")])
    wb.save(out_path)


def save_csv(intros, rows, out_path):
    import csv
    cols = ["股票", "报告期", "分类维度", "主营构成", "主营收入(元)", "收入比例%",
            "主营成本", "成本比例%", "毛利", "利润比例%", "毛利率%"]
    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:  # BOM 便于 Excel 打开
        w = csv.writer(f)
        w.writerow(cols)
        w.writerows([[r[c] for c in cols] for r in sorted(rows, key=lambda x: x["报告期"])])
        w.writerow([])
        w.writerow(["股票", "产品名称", "主营构成"])
        for code, intro in intros.items():
            w.writerow([code, intro.get("产品名称", ""), intro.get("主营构成", "")])


def main():
    stocks = sys.argv[1:] or ["600519.SH"]
    this_year = time.localtime().tm_year
    years = range(START_YEAR, this_year + 1)
    tdx_dir = find_tdx_dir()
    if not tdx_dir:
        raise RuntimeError("未定位到通达信安装目录")

    intros, rows, failed = {}, [], []
    for stock in stocks:
        for y in years:
            try:
                path = download_year(stock, y, tdx_dir)
                intro, rs = parse_mainbusi(path, stock)
                intros[stock] = intro
                rows.extend(rs)
                periods = sorted({r["报告期"] for r in rs})
                print(f"{stock} {y}: {len(rs)} 行, 报告期 {periods[0]}~{periods[-1]}")
            except Exception as e:  # 单年度失败不中断整体
                failed.append((stock, y, str(e)[:80]))
                print(f"{stock} {y}: 失败 {e}")
        if rows:
            rows.sort(key=lambda x: (x["股票"], x["报告期"]))

    out = Path(__file__).resolve().parent.parent / \
        f"经营分析_{'_'.join(s.split('.')[0] for s in stocks)}_{START_YEAR}-{this_year}.xlsx"
    try:
        save_xlsx(intros, rows, out)
    except ImportError:
        out = out.with_suffix(".csv")
        save_csv(intros, rows, out)
    print(f"\n汇总完成: {out}  共 {len(rows)} 行" + (f"; 失败 {failed}" if failed else ""))


if __name__ == "__main__":
    main()
