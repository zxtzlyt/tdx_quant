# -*- coding: utf-8 -*-
"""在线测试: TQ HTTP 服务(127.0.0.1:17709)上的 TqClient 封装与原始只读接口。

前置: 通达信金融终端(支持 TQ)正在运行并登录; 服务不可达时整组自动跳过。
注意: open_in_client 会在客户端弹出个股页面, download_file 会下载参考文件
到客户端 PYPlugins/data —— 均为被测接口的正常行为。
运行: python -m pytest tests/test_live.py -v
"""
import time

import pytest

from tdx_local import TqClient, TqError


def _service_up() -> bool:
    try:
        TqClient(timeout=5).call("refresh_cache")
        return True
    except TqError:
        return False


pytestmark = pytest.mark.skipif(not _service_up(),
                                reason="TQ 服务(127.0.0.1:17709)未运行")

TQ = TqClient(timeout=120)
STOCKS_8 = ["999999.SH", "399001.SZ", "880001.SH", "600000.SH",
            "600519.SH", "000001.SZ", "600036.SH", "000858.SZ"]


# ---------------------------------------------------------------- TqClient 封装
def test_match_chinese_name():
    r = TQ.match("浦发银行")
    hit = [x for x in r if x.get("Code") == "600000.SH"]
    assert hit and hit[0]["Name"] == "浦发银行"


def test_match_by_name_and_code():
    assert any(x.get("Code") == "600519.SH" for x in TQ.match("贵州茅台"))
    assert "600519.SH" in {x.get("Code") for x in TQ.match("600519")}


def test_market_data_recent_count():
    r = TQ.market_data(["600000.SH"], count=10, period="1d", dividend_type="front")
    v = r["Value"]["600000.SH"]
    ds = [int(d) for d in v["Date"]]
    assert len(ds) == 10 and ds == sorted(ds) and ds[-1] >= 20260901
    assert all(float(c) > 0 for c in v["Close"])


def test_market_data_date_range():
    r = TQ.market_data(["600519.SH"], count=-1, start_time="20240101",
                       end_time="20241231", dividend_type="front")
    ds = [int(d) for d in r["Value"]["600519.SH"]["Date"]]
    assert 230 <= len(ds) <= 245 and 20240102 <= ds[0] and ds[-1] <= 20241231


def test_dividend_types_none_front_back():
    def closes(dt):
        r = TQ.market_data(["600519.SH"], count=-1, start_time="20240101",
                           end_time="20241231", dividend_type=dt)
        v = r["Value"]["600519.SH"]
        return [int(d) for d in v["Date"]], [float(c) for c in v["Close"]]
    dn, cn = closes("none")
    df, cf = closes("front")
    db, cb = closes("back")
    assert dn == df == db
    diff_f = sum(1 for a, b in zip(cn, cf) if abs(a - b) > 1e-9)
    assert diff_f > 200                       # 前复权与不复权几乎全程不同
    # 实测: back(后复权)以请求窗口首日为基准 —— 窗口内首个除息日(20240619)
    # 之前 back==none, 之后才出现差异; 换窗口起点会得到不同的"后复权"序列。
    i = dn.index(20240619)
    assert all(abs(cn[k] - cb[k]) <= 1e-9 for k in range(i))
    assert any(abs(cn[k] - cb[k]) > 1e-9 for k in range(i, len(dn)))
    assert cf[i] < cn[i]


def test_market_data_missing_envelope_surface():
    """本地无 5m 数据的代码不再静默: 移入 _missing, Value 中不出现。"""
    r = TQ.market_data(["600000.SH"], period="5m", count=48)
    v = r["Value"]
    if "600000.SH" in v:
        assert len(v["600000.SH"]["Date"]) > 0    # 本地已有分钟数据时走此分支
        return
    assert "600000.SH" in r.get("_missing", {}), r.get("_missing")
    assert "Date" not in v.get("600000.SH", {})


def test_market_data_field_list_client_filter():
    """服务端忽略 field_list, 客户端裁剪后只保留请求字段。"""
    r = TQ.market_data(["600000.SH", "600519.SH"], count=5, period="1d",
                       fill_data=False, field_list=["Date", "Close"])
    for code in ("600000.SH", "600519.SH"):
        v = r["Value"][code]
        assert set(v) == {"Date", "Close"} and len(v["Date"]) == 5


def test_market_data_paging_merge_consistent():
    r = TQ.market_data(STOCKS_8, count=-1, start_time="19910101",
                       dividend_type="front")
    v = r["Value"]
    assert len(v) >= 6 and r.get("has_more") is False
    total = sum(len(x["Date"]) for x in v.values())
    assert total > 24000                          # KlinePaged 已触发并自动合并
    for x in v.values():
        assert len(x["Date"]) == len(x["Open"]) == len(x["Close"])
        ds = [int(d) for d in x["Date"]]
        assert all(a < b for a, b in zip(ds, ds[1:]))


def test_market_data_paging_matches_single_call():
    big = TQ.market_data(STOCKS_8, count=-1, start_time="19910101",
                         dividend_type="front")["Value"]["600519.SH"]
    single = TQ.market_data(["600519.SH"], count=-1, start_time="19910101",
                            dividend_type="front")["Value"]["600519.SH"]
    assert big["Date"] == single["Date"] and big["Close"] == single["Close"]


def test_market_data_1m_no_crash():
    r = TQ.market_data(["600000.SH"], period="1m", count=30000)
    assert ("600000.SH" in r["Value"]) or ("600000.SH" in r.get("_missing", {}))


def test_snapshot_five_levels():
    s = TQ.snapshot("600000.SH")
    assert float(s["LastClose"]) > 0
    assert len(s["Buyp"]) == 5 and len(s["Sellp"]) == 5


def test_snapshot_batch_unsupported_raises():
    with pytest.raises(TqError, match="32601"):
        TQ.call("get_market_snapshot_batch",
                stock_list=["600000.SH", "600519.SH"], field_list=[])


def test_stock_info_flat_with_j_fields():
    info = TQ.stock_info("600000.SH")
    assert info["Name"] == "浦发银行"
    assert len([k for k in info if k.startswith("J_")]) >= 10


def test_stock_info_field_list_and_silent_unknown():
    info = TQ.stock_info("600000.SH", field_list=["Name", "J_mgsy", "NoSuchFieldXyz"])
    assert info["Name"] == "浦发银行" and "J_mgsy" in info
    assert "NoSuchFieldXyz" not in info          # 猜错字段名静默忽略(实测行为)


def test_trading_dates_2024_and_2026():
    ds = [str(d) for d in TQ.trading_dates("20240101", "20241231")]
    assert 240 <= len(ds) <= 245 and ds[0] == "20240102" and ds[-1] == "20241231"
    ds2 = [str(d) for d in TQ.trading_dates("20260101")]
    assert "20260928" in ds2


def test_refresh_kline():
    r = TQ.refresh_kline(["600000.SH"], "1d")
    assert r.get("ErrorId") == "0"


def test_open_in_client():
    r = TQ.open_in_client("1#600000")            # 客户端会弹出浦发银行页面
    assert r.get("ErrorId") == "0"


def test_divid_factors_wrapper():
    """列式返回已解析为每股派息; 与茅台 2024 两次除息的公开值核对。"""
    div = TQ.divid_factors("600519.SH", start_time="20200101", end_time="20261231")
    assert abs(div["20240619"] - 30.876) < 1e-3
    assert abs(div["20241220"] - 23.882) < 1e-3
    assert len(div) >= 20                        # 服务端忽略 start/end, 返回全历史


# ---------------------------------------------------------------- 原始只读接口
def test_sector_list():
    v = TQ.call("get_sector_list").get("Value") or []
    codes = [x["Code"] if isinstance(x, dict) else x for x in v]
    assert len(codes) > 50 and any(str(c).startswith("880") for c in codes)
    v2 = TQ.call("get_sector_list", list_type=1).get("Value") or []
    assert isinstance(v2[0], dict) and "Name" in v2[0]


def test_stock_list_needs_both_params():
    with pytest.raises(TqError, match="market/list_type"):
        TQ.call("get_stock_list", market="5")
    for mkt, lo in (("5", 5000), ("50", 5000), ("32", 300), ("31", 1700)):
        v = TQ.call("get_stock_list", market=mkt, list_type=0).get("Value") or []
        assert len(v) >= lo, (mkt, len(v))


def test_stock_list_in_sector():
    r = TQ.call("get_stock_list_in_sector", block_code="880201.SH").get("Value") or []
    assert len(r) > 10
    r2 = TQ.call("get_stock_list_in_sector", block_code="黑龙江",
                 block_type=0, list_type=0).get("Value") or []
    assert [x["Code"] if isinstance(x, dict) else x for x in r2][:5] == r[:5]


def test_formula_get_all():
    v = TQ.call("formula_get_all").get("Value") or []
    assert len(v) >= 200


def test_refresh_cache():
    assert TQ.call("refresh_cache").get("ErrorId") == "0"


def test_zdt_data():
    v = TQ.call("get_zdt_data", stock_list=["600000.SH"]).get("Value")
    assert v and "600000.SH" in v


def test_kzz_info():
    v = TQ.call("get_stock_list", market="32", list_type=0).get("Value") or []
    code = next(x["Code"] if isinstance(x, dict) else x for x in v)
    kv = TQ.call("get_kzz_info", stock_code=code).get("Value") or {}
    assert kv and "ZGPrice" in str(kv)


def test_trackzs_etf_info():
    v = TQ.call("get_trackzs_etf_info", zs_code="000300.SH").get("Value")
    assert v and v != {"raw": ""}


def test_user_sector():
    assert isinstance(TQ.call("get_user_sector").get("Value") or [], list)


def test_download_file_top10_holders():
    r = TQ.call("download_file", stock_code="600519.SH",
                down_time="20241231", down_type=1)   # 落盘于客户端 PYPlugins/data
    assert r.get("ErrorId") == "0" and "成功" in (r.get("Msg") or "")


def test_financial_data_calendar_only():
    """隐藏参数 table_list/report_type + start_time/end_time(实测必填)。

    table_list=[] 语义为"不选任何表": ErrorId=0 但 FN 数值通道全空,
    只回 announce_time/tag_time 日历两列 —— 数值取数必须
    table_list=field_list(2026-09-30 实测, 见 LOCAL_NOTES)。"""
    r = TQ.call("get_financial_data", stock_list=["600519.SH"],
                table_list=[], report_type="announce_time",
                start_time="20200101", end_time="20261231")
    per = (r.get("Value") or {}).get("600519.SH") or {}
    assert "announce_time" in per and "tag_time" in per
    assert not [k for k in per if k.upper().startswith("FN")]
    assert r.get("ProDataPaged") is True


def test_financial_data_fn_numeric_channel():
    """FN 数值通道 HTTP 可用: table_list 必须等于 field_list(2026-09-30 实测,
    推翻此前"table_list=[] 也补齐"的结论 —— 空表即不取数)。

    茅台 2026 中报 FN96 归母净利 445.17 亿与东财 F10 经营评述互证。"""
    fields = ["FN1", "FN40", "FN95", "FN96", "FN107"]
    r = TQ.call("get_financial_data", stock_list=["600519.SH"],
                field_list=fields, table_list=fields,
                report_type="tag_time",
                start_time="20240101", end_time="20261231")
    per = (r.get("Value") or {}).get("600519.SH") or {}
    fn96 = [float(x) for x in (per.get("FN96") or []) if x not in (None, "")]
    assert fn96, "FN 数值通道为空 —— table_list=field_list 未生效?"
    assert max(fn96) == 86228148224.0          # 2024 年报归母净利(茅台, 元)
    assert per.get("tag_time") and "20260630" in per["tag_time"]


def test_gp_one_data_snapshot():
    """红宝书 GPONEDAT 族: GO 单值快照(table_list=field_list 必填)。"""
    r = TQ.call("get_gp_one_data", stock_list=["600000.SH"],
                field_list=["GO1", "GO33"], table_list=["GO1", "GO33"])
    rec = (r.get("Value") or {}).get("600000.SH") or {}
    assert float(rec.get("GO1", 0)) == 10.0     # 浦发发行价
    assert float(rec.get("GO33", 0)) > 0        # 最新总股本(万股)


def test_gpjy_value_series():
    """红宝书 GPJYVALUE 族: GP 日序列(融资余额/总市值/股息率)。"""
    r = TQ.call("get_gpjy_value", stock_list=["600000.SH"],
                field_list=["GP3", "GP16", "GP21"],
                table_list=["GP3", "GP16", "GP21"],
                start_time="20260921", end_time="20260928")
    rec = (r.get("Value") or {}).get("600000.SH") or {}
    gp16 = rec.get("GP16") or []
    assert gp16 and float(gp16[-1]["Value"][0]) > 0     # 总市值(万元)
    gp21 = rec.get("GP21") or []
    assert gp21 and 0 < float(gp21[-1]["Value"][0]) < 100  # 股息率(%)


def test_scjy_value_market():
    """红宝书 SCJYVALUE 族: SC 市场序列(沪深两融余额, 万亿量级)。"""
    r = TQ.call("get_scjy_value", field_list=["SC1"], table_list=["SC1"],
                start_time="20260921", end_time="20260928")
    sc1 = (r.get("Value") or {}).get("SC1") or []
    assert sc1 and float(sc1[-1]["Value"][0]) > 1e8     # >1万亿元(口径:万元)


def test_bkjy_value_sector():
    """红宝书 BKJYVALUE 族: BK 板块估值(全A 市盈率TTM 整体法)。"""
    r = TQ.call("get_bkjy_value", stock_list=["880001.SH"],
                field_list=["BK5", "BK10"], table_list=["BK5", "BK10"],
                start_time="20260921", end_time="20260928")
    rec = (r.get("Value") or {}).get("880001.SH") or {}
    bk5 = rec.get("BK5") or []
    assert bk5 and 0 < float(bk5[-1]["Value"][0]) < 100  # PE(TTM) 合理区间


def test_formula_engine_broken_on_http():
    """复现 LOCAL_NOTES 结论: 公式引擎 HTTP 通路不生效, 恒全 0。"""
    TQ.call("formula_set_data_info", stock_code="600000.SH", stock_period="1d",
            count=50, dividend_type=1)
    r = TQ.call("formula_zb", formula_name="MACD", formula_arg="12,26,9")
    v = r.get("Value") or {}
    assert v and not [x for seq in v.values() for x in (seq or [])
                      if isinstance(x, (int, float)) and x != 0]


# ---------------------------------------------------------------- 错误处理
def test_unknown_method_raises():
    with pytest.raises(TqError, match="32601"):
        TQ.call("no_such_method_zzz")


def test_missing_required_param_raises():
    with pytest.raises(TqError, match="stock_code"):
        TQ.call("get_market_snapshot")


def test_service_latency_sanity():
    """大结果分页取数应在数秒级(8 股全历史实测 ~1.5s)。"""
    t0 = time.time()
    TQ.market_data(STOCKS_8, count=-1, start_time="19910101",
                   dividend_type="front")
    assert time.time() - t0 < 30
