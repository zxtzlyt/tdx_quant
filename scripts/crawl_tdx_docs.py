# -*- coding: utf-8 -*-
"""抓取通达信量化官方文档站(help.tdx.com.cn/quant)全部接口类页面并转为本地 markdown。

用法: python scripts/crawl_tdx_docs.py
输出: docs/tdx-quant-docs/<章节>/<接口名>.md  +  docs/tdx-quant-docs/_meta/results.json
可重复运行,已成功的页面会被跳过(--force 全量重抓)。
"""
import json
import re
import sys
import textwrap
import time
import urllib.request
import urllib.error
from pathlib import Path
from urllib.parse import urljoin

import html2text
from bs4 import BeautifulSoup, NavigableString

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "docs" / "tdx-quant-docs"
META_DIR = OUT_DIR / "_meta"
BASE = "https://help.tdx.com.cn/quant/docs/markdown/"

# (章节目录, 子目录或'', 回退文件名, 相对路径, 中文标题提示)
MANIFEST = [
    # ---- 01 tqcenter 通用函数 ----
    *[( "01-tqcenter-通用函数", "", n, f"ctx.stock.md/{p}.html", t) for n, p, t in [
        ("initialize",                  "mindoc-1cv85e8u9nb0c", "初始化initialize"),
        ("subscribe_hq",                "mindoc-1h1104d65vr68", "订阅行情subscribe_hq"),
        ("unsubscribe_hq",              "mindoc-1h112vh7jtsms", "取消订阅更新unsubscribe_hq"),
        ("get_subscribe_hq_stock_list", "mindoc-1h1137r4k2mas", "获得订阅列表get_subscribe_hq_stock_list"),
        ("refresh_cache",               "mindoc-1h10f9145us1g", "刷新行情缓存refresh_cache"),
        ("refresh_kline",               "mindoc-1h10fh9m6recg", "缓存历史K线refresh_kline"),
        ("download_file",               "mindoc-1h10pqrdlj71o", "下载特定数据文件download_file"),
        ("send_message",                "mindoc-1h10rkbndkb0k", "发送消息到TQ策略界面send_message"),
        ("send_warn",                   "mindoc-1h10u5k9qjh8o", "发送预警信号到客户端send_warn"),
        ("send_file",                   "mindoc-1h10u17ue9464", "发送文件到客户端send_file"),
        ("send_bt_data",                "mindoc-1h10vc2pot87c", "发送回测数据send_bt_data"),
        ("print_to_tdx",                "mindoc-1h62l8kg2k4jc", "打印数据到客户端print_to_tdx"),
        ("exec_to_tdx",                 "mindoc-1h85iq443j44c", "调用客户端功能exec_to_tdx"),
        ("get_match_stkinfo",           "mindoc-1hdguaia2v4bo", "检索证券信息get_match_stkinfo"),
    ]],
    # ---- 02 tqcenter 行情 ----
    *[( "02-tqcenter-行情", "", n, f"mindoc-1ctuhthaq5qmg/{p}.html", t) for n, p, t in [
        ("get_market_data",          "mindoc-1h10g60jt68sc", "行情获取get_market_data"),
        ("get_market_snapshot",      "mindoc-1h10iig4pb6e0", "实时行情快照get_market_snapshot"),
        ("get_stock_info",           "mindoc-1h10jj7r7jol4", "股票基础信息get_stock_info"),
        ("get_more_info",            "mindoc-1h3rtq1hij0ac", "股票扩展信息get_more_info"),
        ("get_pricevol",             "mindoc-1hce2o96aktmk", "价格成交量get_pricevol"),
        ("get_zdt_data",             "mindoc-1hh9i0av0gtok", "涨跌停数据get_zdt_data"),
        ("get_exday_data",           "mindoc-1hh9gktmqsv5c", "除权除息数据get_exday_data"),
        ("get_divid_factors",        "mindoc-1h10hsiat36k4", "复权因子get_divid_factors"),
        ("get_relation",             "mindoc-1h84ec4p26qus", "关联证券get_relation"),
        ("get_trading_dates",        "mindoc-1h10q7i3702rk", "交易日get_trading_dates"),
        ("get_ipo_info",             "mindoc-1h137jr3khrqo", "IPO信息get_ipo_info"),
        ("get_gb_info",              "mindoc-1h3ru0b1tssrc", "股本信息get_gb_info"),
        ("get_gb_info_by_date",      "mindoc-1hc4303vsv1fk", "股本信息按日期get_gb_info_by_date"),
        ("get_market_snapshot_batch","mindoc-1hlnpjm512efk", "快照批量get_market_snapshot_batch"),
        ("get_stock_info_batch",     "mindoc-1hlnuonsp0amo", "基础信息批量get_stock_info_batch"),
        ("get_more_info_batch",      "mindoc-1hlnup4o0ei68", "扩展信息批量get_more_info_batch"),
    ]],
    # ---- 03 tqcenter 财务 ----
    *[( "03-tqcenter-财务", "", n, f"TdxQuant.md/{p}.html", t) for n, p, t in [
        ("get_financial_data",           "mindoc-1h10m001ic888", "专业财务数据get_financial_data"),
        ("get_financial_data_by_date",   "mindoc-1h10mdt617qss", "专业财务数据按日期get_financial_data_by_date"),
        ("get_gpjy_value",               "mindoc-1h10muc82r55k", "股票专业数据get_gpjy_value"),
        ("get_gpjy_value_by_date",       "mindoc-1h2pci5gh6h7k", "股票专业数据按日期get_gpjy_value_by_date"),
        ("get_bkjy_value",               "mindoc-1h10p0ncmp5mc", "板块专业数据get_bkjy_value"),
        ("get_bkjy_value_by_date",       "mindoc-1h10p3d31736g", "板块专业数据按日期get_bkjy_value_by_date"),
        ("get_scjy_value",               "mindoc-1h10p8op6ia9g", "市场专业数据get_scjy_value"),
        ("get_scjy_value_by_date",       "mindoc-1h10pe678ta04", "市场专业数据按日期get_scjy_value_by_date"),
        ("get_gp_one_data",              "mindoc-1h10pk3rsg044", "股票单点数据get_gp_one_data"),
    ]],
    # ---- 04 tqcenter 板块与自选股 ----
    *[( "04-tqcenter-板块与自选股", "", n, f"mindoc-1ctuhttn72svo/{p}.html", t) for n, p, t in [
        ("get_stock_list",           "mindoc-1h10qo3uj48fg", "证券列表get_stock_list"),
        ("get_sector_list",          "mindoc-1h10r5907noko", "板块列表get_sector_list"),
        ("get_stock_list_in_sector", "mindoc-1h10r92mchgug", "板块成份股get_stock_list_in_sector"),
    ]],
    *[( "04-tqcenter-板块与自选股", "", n, f"mindoc-1h139a4ckchkk/{p}.html", t) for n, p, t in [
        ("get_user_sector",   "mindoc-1h1hauh9inaac", "获取自选股get_user_sector"),
        ("send_user_block",   "mindoc-1h10sec960u0c", "发送自定义板块send_user_block"),
        ("clear_sector",      "mindoc-1h10sbcnl1c94", "清空板块clear_sector"),
        ("create_sector",     "mindoc-1h10rrkuj1drs", "创建板块create_sector"),
        ("delete_sector",     "mindoc-1h10s391lng6s", "删除板块delete_sector"),
        ("rename_sector",     "mindoc-1h10s7n863d50", "重命名板块rename_sector"),
    ]],
    # ---- 05 tqcenter ETF/可转债/期货 ----
    *[( "05-tqcenter-ETF可转债期货", "", n, f"mindoc-1h13a594nhvb4/{p}.html", t) for n, p, t in [
        ("get_trackzs_etf_info", "mindoc-1h6hknp6pjppc", "指数跟踪ETF信息get_trackzs_etf_info"),
        ("get_kzz_info",         "mindoc-1h137euvcjn98", "可转债信息get_kzz_info"),
        ("get_kzz_info_batch",   "mindoc-1hlnuvdpvh6o4", "可转债信息批量get_kzz_info_batch"),
    ]],
    # ---- 06 tqcenter 公式 ----
    *[( "06-tqcenter-公式", "", n, f"mindoc-1h3hrvkp4sc0g/{p}.html", t) for n, p, t in [
        ("formula_format_data",      "mindoc-1h3hte6obagc0", "公式数据格式化formula_format_data"),
        ("formula_set_data",         "mindoc-1h3hsvcct5sdc", "公式设置数据formula_set_data"),
        ("formula_set_data_info",    "mindoc-1h3hs08rn02uc", "公式设置数据信息formula_set_data_info"),
        ("formula_get_data",         "mindoc-1h3httgemshno", "公式获取数据formula_get_data"),
        ("formula_zb_xg_exp",        "mindoc-1h3huq37005ro", "指标选股专家公式formula_zb/xg/exp"),
        ("formula_process_mul_xg_zb","mindoc-1h4ad5lisvdfg", "批量公式formula_process_mul_xg/zb"),
        ("formula_get_all",          "mindoc-1hce2u769tljc", "获取全部公式formula_get_all"),
        ("formula_get_info",         "mindoc-1hce356csmgmo", "获取公式信息formula_get_info"),
    ]],
    # ---- 07 tqcenter 交易 ----
    *[( "07-tqcenter-交易", "", n, f"mindoc-1h7k4iqb1grk4/{p}.html", t) for n, p, t in [
        ("stock_account",          "mindoc-1h7k4k5tk6q64", "登录交易账号stock_account"),
        ("query_stock_asset",      "mindoc-1h84fvcjulrnc", "查询资产query_stock_asset"),
        ("query_stock_orders",     "mindoc-1h7k4rp481gt4", "查询委托query_stock_orders"),
        ("query_stock_positions",  "mindoc-1h7k5ar9kc508", "查询持仓query_stock_positions"),
        ("query_history_trade",    "mindoc-1hlnun1348n54", "查询历史成交query_history_trade"),
        ("order_stock",            "mindoc-1h7k5j4drr928", "下单order_stock"),
        ("cancel_order_stock",     "mindoc-1h84elp5atr6o", "撤单cancel_order_stock"),
    ]],
    # ---- 08 HTTP调用 ----
    ("08-HTTP调用", "", "http_json_rpc", "mindoc-1hdhbmi50d038.html", "HTTP方式调用"),
    # ---- 09 tqs TdxAiData ----
    ("09-tqs-TdxAiData", "", "tdxaidata_overview", "mindoc-1hjbgqpdhv114.html", "TdxAiData后台接口总览"),
    *[( "09-tqs-TdxAiData", "", n, f"mindoc-1hjbidnohpjn4/{p}.html", t) for n, p, t in [
        ("tqs_get_tick_data",           "mindoc-1hlsetap441rs", "分笔数据get_tick_data"),
        ("tqs_get_minute_data",         "mindoc-1hlseu05n86ek", "分钟数据get_minute_data"),
        ("tqs_get_zzgz_stocklist",      "mindoc-1hlseuoousuvo", "中证高管持股股票列表get_zzgz_stocklist"),
        ("tqs_get_call_auction",        "mindoc-1hlsevg97ftug", "集合竞价get_call_auction"),
        ("tqs_get_call_auction_batch",  "mindoc-1hlsf010md5gg", "集合竞价批量get_call_auction_batch"),
        ("tqs_subscribe",               "mindoc-1hlsf0u13l0d4", "订阅行情subscribe"),
        ("tqs_unsubscribe",             "mindoc-1hlsf1ifqpt8k", "取消订阅unsubscribe"),
    ]],
    # ---- 10 Lambda pylambda ----
    *[( "10-lambda-pylambda", "01-生命周期", n, f"mindoc-1hho7blr2j340/mindoc-1hho9d546pbhc/{p}.html", t) for n, p, t in [
        ("init",           "mindoc-1hho9hh3kshvo", "初始化init"),
        ("before_trading", "mindoc-1hho9irt0nu3s", "盘前回调before_trading"),
        ("handle_bar",     "mindoc-1hho9jic0qbu8", "K线回调handle_bar"),
        ("after_trading",  "mindoc-1hho9kq57km1c", "盘后回调after_trading"),
        ("on_strategy_end","mindoc-1hho9lb0bd8ck", "策略结束on_strategy_end"),
        ("on_order",       "mindoc-1hib55063ha7o", "订单回调on_order"),
        ("on_trade",       "mindoc-1hib60s1q4hbg", "成交回调on_trade"),
    ]],
    *[( "10-lambda-pylambda", "02-全局运行对象", n, f"mindoc-1hho7blr2j340/mindoc-1hho9u0cbfe60/{p}.html", t) for n, p, t in [
        ("context_stock",    "huicecontext",       "context.stock"),
        ("context_params",   "mindoc-1hhoahrgeati0", "context.params"),
        ("context_portfolio","portfolio",          "context.portfolio"),
        ("position",         "position",           "positions对象"),
        ("bar_object",       "bar",                "Bar对象"),
        ("context_run_info", "runinfo",            "context.run_info"),
        ("order_object",     "order",              "Order对象"),
        ("trade_object",     "trade",              "Trade对象"),
    ]],
    *[( "10-lambda-pylambda", "03-回测设置", n, f"mindoc-1hho7blr2j340/mindoc-1hhoa58m7i93s/{p}.html", t) for n, p, t in [
        ("set_benchmark",  "mindoc-1hhoa5ki6fpkk", "设置基准set_benchmark"),
        ("set_commission", "mindoc-1hhoa7gjbabuo", "设置佣金set_commission"),
        ("set_slippage",   "mindoc-1hhoa91t58dgk", "设置滑点set_slippage"),
        ("set_option",     "mindoc-1hhoaba3gefmg", "设置选项set_option"),
        ("set_execution",  "mindoc-1hhoae0q7sqok", "设置执行方式set_execution"),
        ("enable_profile", "mindoc-1hhoajhqre804", "性能分析enable_profile"),
        ("other_settings", "mindoc-1hhoak9m7p5io", "其他设置函数"),
    ]],
    *[( "10-lambda-pylambda", "04-定时任务", n, f"mindoc-1hho7blr2j340/mindoc-1hibf3lo5qk7g/{p}.html", t) for n, p, t in [
        ("run_daily",           "mindoc-1hibf4cf978ng", "每日定时run_daily"),
        ("run_weekly_monthly",  "mindoc-1hibf6bvaogfo", "按周月定时"),
    ]],
    *[( "10-lambda-pylambda", "05-特有行情", n, f"mindoc-1hho7blr2j340/mindoc-1hi3n0rqkakt4/{p}.html", t) for n, p, t in [
        ("lambda_get_tick_data",      "mindoc-1hhob7ou94li8", "分笔数据get_tick_data"),
        ("lambda_get_minute_data",    "mindoc-1hi3n2jbg66bs", "分钟数据get_minute_data"),
        ("lambda_get_zzgz_stocklist", "mindoc-1hi3n4r9e6cpo", "中证高管持股列表get_zzgz_stocklist"),
    ]],
    *[( "10-lambda-pylambda", "06-数据函数", n, f"mindoc-1hho7blr2j340/mindoc-1hhoaleti08f0/{p}.html", t) for n, p, t in [
        ("get_price",                "mindoc-1hhoalokn8c6g", "历史价格get_price"),
        ("get_bars_batch",           "mindoc-1hhoamu2bpbqk", "批量K线get_bars_batch"),
        ("calc_factor_batch",        "mindoc-1hhoantm89gu4", "批量因子calc_factor_batch"),
        ("get_factor_cache_info",    "mindoc-1hhoapc2dga88", "因子缓存信息get_factor_cache_info"),
        ("history",                  "mindoc-1hhoaqrp4i0ic", "历史数据history"),
        ("attribute_history",        "mindoc-1hhoarm6i3eek", "属性历史attribute_history"),
        ("get_current",              "mindoc-1hhoave9jakik", "当前数据get_current"),
        ("index_industry_concept",   "mindoc-1hhob9ldbiqak", "获取指数行业和概念成份"),
        ("native_indicators_ma_macd","mindoc-1hhoasuth0c00", "原生指标MA/MACD"),
        ("get_all_securities",       "mindoc-1hhob255nqs7s", "全部证券get_all_securities"),
        ("get_security_info",        "get_security_info",    "证券信息get_security_info"),
        ("trading_calendar",         "mindoc-1hhob115b5p0s", "交易日历函数"),
        ("time_functions",           "mindoc-1hhob071fp9s4", "时间函数"),
    ]],
    *[( "10-lambda-pylambda", "07-交易函数", n, f"mindoc-1hho7blr2j340/mindoc-1hhobbn0nuedg/{p}.html", t) for n, p, t in [
        ("order",                    "mindoc-1hhobbvteo4ds", "下单order"),
        ("order_value",              "mindoc-1hhobcp20bskg", "按价值下单order_value"),
        ("order_target",             "mindoc-1hhobdfdncbo0", "目标数量下单order_target"),
        ("order_percent_target_value","mindoc-1hhobe5d2u5e8","比例目标市值下单"),
        ("rebalance_target_weights", "mindoc-1hhoberagvv8c", "组合目标权重调仓"),
        ("query_orders_trades",      "mindoc-1hhobfk2rmg84", "订单和成交查询"),
        ("cancel_order",             "mindoc-1hhobgp6ravs4", "提交撤单"),
    ]],
    *[( "10-lambda-pylambda", "08-账户查询", n, f"mindoc-1hho7blr2j340/mindoc-1hib696p7b7gc/{p}.html", t) for n, p, t in [
        ("get_cash",      "mindoc-1hib69thso1oo", "获取资金get_cash"),
        ("get_positions", "mindoc-1hib6kkioc08g", "获取持仓列表get_positions"),
        ("get_position",  "mindoc-1hib6nhrouuvg", "获取单持仓get_position"),
        ("get_portfolio", "mindoc-1hib6pevs6fck", "获取组合get_portfolio"),
    ]],
    *[( "10-lambda-pylambda", "09-其他", n, f"mindoc-1hho7blr2j340/{p}.html", t) for n, p, t in [
        ("logging_and_helpers", "mindoc-1hhoc0a5b29v0", "记录日志和辅助"),
        ("code_convert",        "mindoc-1hibfhi6jhlqs", "代码转换函数"),
        ("full_example",        "mindoc-1hhodeob36hi4", "完整示例"),
        ("lambda_faq",          "mindoc-1hhodgohoq4j0", "Lambda常见问题"),
    ]],
    # ---- 11 常量枚举 ----
    ("11-常量枚举", "", "constants", "Dict.html", "常量枚举"),
]


def fetch(url: str, retries: int = 2) -> str:
    last_err = None
    for i in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept-Language": "zh-CN,zh;q=0.9",
            })
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as e:
            last_err = e
            if i < retries:
                time.sleep(1 + i * 2)
    raise RuntimeError(f"fetch failed after {retries+1} tries: {url} ({last_err})")


def table_to_md(table) -> str:
    """把 HTML 表格转成 markdown 管道表格(参数表/字段表是文档核心,必须保真)。"""
    def cell_text(c) -> str:
        for br in c.find_all("br"):
            br.replace_with(" ")
        txt = c.get_text(" ", strip=True)
        txt = re.sub(r"\s+", " ", txt)
        return txt.replace("|", "\\|")

    rows = []
    head = table.find("thead")
    body = table.find("tbody") or table
    header_cells = []
    if head:
        tr = head.find("tr")
        if tr:
            header_cells = [cell_text(c) for c in tr.find_all(["th", "td"])]
    if not header_cells:
        first_tr = body.find("tr")
        if first_tr and first_tr.find("th"):
            header_cells = [cell_text(c) for c in first_tr.find_all(["th", "td"])]
    data_rows = []
    for tr in body.find_all("tr"):
        if header_cells and tr.find("th") and tr is body.find("tr"):
            continue
        cells = [cell_text(c) for c in tr.find_all(["td", "th"])]
        if cells:
            data_rows.append(cells)

    ncols = max([len(header_cells)] + [len(r) for r in data_rows]) if (header_cells or data_rows) else 0
    if ncols == 0:
        return ""
    if not header_cells:
        header_cells = [""] * ncols
    rows.append("| " + " | ".join(header_cells) + " |")
    rows.append("| " + " | ".join(["---"] * ncols) + " |")
    for r in data_rows:
        r = r + [""] * (ncols - len(r))
        rows.append("| " + " | ".join(r) + " |")
    return "\n".join(rows)


def preprocess(content) -> dict:
    """清理 VuePress 正文并把代码块/表格抽成占位符(html2text 会折叠文本节点里的换行,
    表格和代码必须在转换后自行还原)。返回 {'code': [(lang, text)], 'table': [md]}。"""
    store = {"code": [], "table": []}
    for a in content.find_all("a", class_="header-anchor"):
        a.decompose()
    for div in content.find_all("div", class_=re.compile("line-numbers")):
        if div.find("pre") is None:  # 行号水印不含代码块; 含 pre 的是外层容器, 不能删
            div.decompose()
    for tag in content.find_all(["script", "style"]):
        tag.decompose()
    for pre in content.find_all("pre"):
        code = pre.find("code") or pre
        classes = " ".join(pre.get("class", []) + code.get("class", []))
        m = re.search(r"language-([\w+#-]+)", classes)
        store["code"].append((m.group(1) if m else "", code.get_text()))
        pre.replace_with(NavigableString(f"\n\nXCXCODE{len(store['code'])-1}XCX\n\n"))
    for table in content.find_all("table"):
        store["table"].append(table_to_md(table))
        table.replace_with(NavigableString(f"\n\nXCXTABLE{len(store['table'])-1}XCX\n\n"))
    for img in content.find_all("img"):
        if img.get("src"):
            img["src"] = urljoin(BASE, img["src"])
    for a in content.find_all("a", href=True):
        a["href"] = urljoin(BASE, a["href"])
    return store


def collapse_spaces(text: str) -> str:
    """把引号外的连续空白(含Tab)压成单个空格, 引号内原样保留。"""
    out, q, i, n = [], None, 0, len(text)
    while i < n:
        c = text[i]
        if q:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if c == q:
                q = None
        elif c in "'\"":
            q = c
            out.append(c)
        elif c in " \t":
            j = i
            while j < n and text[j] in " \t":
                j += 1
            out.append(" ")
            i = j
            continue
        else:
            out.append(c)
        i += 1
    return "".join(out)


def split_top_commas(text: str) -> list:
    """按括号深度0处的逗号切分(忽略引号内的逗号与括号)。"""
    parts, cur, depth, q, i, n = [], [], 0, None, 0, len(text)
    while i < n:
        c = text[i]
        if q:
            cur.append(c)
            if c == "\\" and i + 1 < n:
                cur.append(text[i + 1])
                i += 2
                continue
            if c == q:
                q = None
        elif c in "'\"":
            q = c
            cur.append(c)
        elif c in "([{":
            depth += 1
            cur.append(c)
        elif c in ")]}":
            depth -= 1
            cur.append(c)
        elif c == "," and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(c)
        i += 1
    parts.append("".join(cur))
    return parts


def reformat_signature(block: str):
    """函数签名形态的代码块重排: 参数逐行对齐左括号, 参数名/类型间单空格。

    官方文档源码用多空格+Tab 手工对参数做列对齐且常对错位, 直接展开观感很差;
    重排后逐字符比对(压扁空白后)与原文一致才接受, 否则返回 None 保留原样。
    """
    joined = collapse_spaces(" ".join(l.strip() for l in block.split("\n") if l.strip()))
    m = re.match(r"^(async\s+def\s+\w+|def\s+\w+|\w+)\s*\(", joined)
    if not m or not re.search(r"\)\s*(->\s*[^:]+)?:\s*$", joined):
        return None
    head = m.group(0)
    start = m.end() - 1                      # head 末尾的 '(' 位置
    depth, q, end, i, n = 0, None, None, start, len(joined)
    while i < n:
        c = joined[i]
        if q:
            if c == "\\":
                i += 2
                continue
            if c == q:
                q = None
        elif c in "'\"":
            q = c
        elif c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
            if depth == 0:
                end = i
                break
        i += 1
    if end is None:
        return None
    inner = joined[start + 1:end]
    suffix = joined[end + 1:].strip()         # '-> Dict:' / ':' 等
    params = [p.strip() for p in split_top_commas(inner) if p.strip()]
    if not params:
        return None
    close = ")" + (suffix if suffix.startswith(":") else " " + suffix if suffix else "")
    indent = " " * len(head)
    if len(params) == 1:
        out = [head + params[0] + close]
    else:
        out = [head + params[0] + ","]
        out += [indent + p + "," for p in params[1:-1]]
        out.append(indent + params[-1] + close)
    if collapse_spaces(" ".join(x.strip() for x in out)) != joined:
        return None                           # 内容有出入, 放弃重排
    return "\n".join(out)


def normalize_code_block(text: str) -> str:
    """代码块统一排版: Tab展开(4) -> 去公共前导缩进 -> 签名块重排。"""
    text = textwrap.dedent(text.expandtabs(4))
    refmt = reformat_signature(text)
    return refmt if refmt is not None else text


def postprocess(md: str, store: dict) -> str:
    def code_sub(m):
        lang, text = store["code"][int(m.group(1))]
        return f"\n```{lang}\n{normalize_code_block(text).rstrip()}\n```\n"

    def table_sub(m):
        return "\n" + store["table"][int(m.group(1))] + "\n"

    md = re.sub(r"XCXCODE(\d+)XCX", code_sub, md)
    md = re.sub(r"XCXTABLE(\d+)XCX", table_sub, md)
    md = re.sub(r"[ \t]+\n", "\n", md)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md


def make_converter() -> "html2text.HTML2Text":
    h = html2text.HTML2Text()
    h.body_width = 0            # 不折行, 表格行保持完整
    h.skip_internal_links = True
    h.ignore_images = False
    h.ignore_links = False
    return h


def clean_title(raw: str) -> str:
    """去掉标题里混入的锚点井号和多余空白。"""
    t = re.sub(r"\s+", " ", raw).strip()
    return re.sub(r"^#+\s*", "", t)


def main(force: bool = False) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    META_DIR.mkdir(parents=True, exist_ok=True)
    h2t = make_converter()
    results, failures = [], []
    for idx, (folder, sub, fallback, rel, hint) in enumerate(MANIFEST, 1):
        url = BASE + rel
        target_dir = OUT_DIR / folder / sub if sub else OUT_DIR / folder
        target_dir.mkdir(parents=True, exist_ok=True)
        existing = target_dir / f"{fallback}.md"
        done_file = META_DIR / "done.json"
        done = json.loads(done_file.read_text("utf-8")) if done_file.exists() else {}
        if not force and done.get(rel) and existing.exists():
            results.append({"folder": folder, "sub": sub, "fallback": fallback,
                            "url": url, "title": done[rel]["title"], "file": str(existing),
                            "skipped": True})
            continue
        try:
            html = fetch(url)
            soup = BeautifulSoup(html, "html.parser")
            content = (soup.find("div", class_=re.compile(r"theme-default-content"))
                       or soup.find("main") or soup.find("div", class_="content__default"))
            if content is None:
                raise RuntimeError("content div not found")
            h1 = content.find("h1")
            title = clean_title(h1.get_text(" ", strip=True) if h1 else (hint or fallback))
            name = fallback  # 清单里的英文名已人工核对过 H1, 固定使用以保证幂等
            store = preprocess(content)
            md = h2t.handle(str(content.decode_contents()))
            md = postprocess(md, store).strip() + "\n"
            meta = f"<!-- source: {url} | 章节: {folder}{'/' + sub if sub else ''} -->\n"
            if not h1:
                meta += f"# {title}\n"
            out = target_dir / f"{name}.md"
            out.write_text(meta + "\n" + md, encoding="utf-8", newline="\n")
            results.append({"folder": folder, "sub": sub, "fallback": fallback, "name": name,
                            "url": url, "title": title, "file": str(out), "bytes": out.stat().st_size})
            done[rel] = {"title": title, "name": name}
            print(f"[{idx}/{len(MANIFEST)}] OK  {folder}/{sub} {name}.md  ({title})")
        except Exception as e:  # noqa: BLE001 单页失败不中断
            failures.append({"url": url, "folder": folder, "fallback": fallback, "error": str(e)})
            print(f"[{idx}/{len(MANIFEST)}] FAIL {url} -> {e}")
        time.sleep(0.3)
        (META_DIR / "results.json").write_text(
            json.dumps({"results": results, "failures": failures}, ensure_ascii=False, indent=1),
            encoding="utf-8")
        (META_DIR / "done.json").write_text(json.dumps(done, ensure_ascii=False), encoding="utf-8")

    print(f"\n=== done: {len(results)} ok ({sum(1 for r in results if not r.get('skipped'))} fetched, "
          f"{sum(1 for r in results if r.get('skipped'))} skipped), {len(failures)} failed ===")
    for f in failures:
        print(f"  FAIL {f['url']} : {f['error']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(force="--force" in sys.argv))
