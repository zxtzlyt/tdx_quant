# -*- coding: utf-8 -*-
"""离线测试: cw_fields / gpcw / lday 解析与包导出, 不依赖 TQ 服务在线。

gpcw/lday 的真实数据用例依赖本机数据目录(见 conftest), 缺失时自动跳过;
其余为纯逻辑用例, 任何环境可跑。运行: python -m pytest tests/test_offline.py -v
"""
import os
import json
import shutil
import struct
import subprocess
import sys
import urllib.error
from unittest.mock import patch

import pytest

from tdx_local import (TqClient, TqError, close_enough, approx_announce_date,
                       read_gpcw, read_series, scan_reports, single_quarters,
                       sync_cw, GpcwPlaceholder, GpcwCorrupt, GpcwReportGap)
from tdx_local import cw_fields, gpcw, lday, kcache, indicators as ind
from tdx_local import backtest as bt
from conftest import ROOT, CW_DIR, GTJA_LDAY

needs_cw = pytest.mark.skipif(not os.path.isdir(CW_DIR), reason=f"无数据目录 {CW_DIR}")


# ---------------------------------------------------------------- cw_fields
def test_resolve_name_alias_int():
    assert cw_fields.resolve("营业收入") == 74
    assert cw_fields.resolve("EPS") == 1
    assert cw_fields.resolve("营收") == 74
    assert cw_fields.resolve(40) == 40


def test_resolve_unknown_raises():
    with pytest.raises(LookupError):
        cw_fields.resolve("不存在的字段名")


def test_resolve_known_missing_raises():
    with pytest.raises(LookupError, match="锚点扫描"):
        cw_fields.resolve("合同负债")


def test_meta_and_unit():
    assert cw_fields.meta(1)["unit"] == "元/股"
    assert cw_fields.meta("营业收入")["period"] == "累计"
    assert cw_fields.meta("营业收入")["verified"] is True
    assert cw_fields.unit("毛利率") == "%"
    m = cw_fields.meta(500)
    assert m["name"] == "FN500" and m["verified"] is False


@needs_cw
def test_find_slot_anchors():
    rd, stocks = read_gpcw(os.path.join(CW_DIR, "gpcw20241231.dat"))
    rd2, stocks2 = read_gpcw(os.path.join(CW_DIR, "gpcw20231231.dat"))
    records = {rd: stocks["600519"], rd2: stocks2["600519"]}
    targets = {d: rec[73] for d, rec in records.items()}   # FN74 营业收入
    slots = cw_fields.find_slot(records, targets)
    assert 74 in slots
    assert cw_fields.find_slot(records, {d: -12345.678 for d in records}) == []


# ---------------------------------------------------------------- gpcw 解析
@needs_cw
def test_read_gpcw_anchor_2025q3():
    rd, stocks = read_gpcw(os.path.join(CW_DIR, "gpcw20250930.dat"))
    assert rd == "20250930" and "600519" in stocks
    rec = stocks["600519"]
    # 锚值为公开财报四舍五入值(2位小数), 用 0.005 绝对容差(见 close_enough 提示)
    assert abs(rec[0] - 51.53) < 0.005      # 基本每股收益
    assert abs(rec[3] - 205.28) < 0.005     # 每股净资产
    assert len(rec) == 584


def test_read_gpcw_placeholder_and_corrupt(tmp_path):
    p = tmp_path / "gpcw19990101.dat"
    p.write_bytes(b"\x00" * 20)
    with pytest.raises(GpcwPlaceholder):
        read_gpcw(p)
    p.write_bytes(b"\x01" * 5000)
    with pytest.raises(GpcwCorrupt):
        read_gpcw(p)


def test_read_gpcw_cache_independent_copies():
    """缓存命中返回浅拷贝: 外层 dict 改动不影响后续读取。"""
    path = os.path.join(CW_DIR, "gpcw20241231.dat")
    _, s1 = read_gpcw(path)
    _, s2 = read_gpcw(path)
    assert s1 == s2
    s2["999999"] = ()
    _, s3 = read_gpcw(path)
    assert "999999" not in s3


@needs_cw
def test_list_reports_sorted():
    files = gpcw.list_reports(CW_DIR)
    dates = [os.path.basename(f)[4:-4] for f in files]
    assert dates == sorted(dates) and len(dates) > 100


@needs_cw
def test_scan_reports_statuses():
    rows = scan_reports(CW_DIR)
    dates = [r["date"] for r in rows]
    assert dates == sorted(dates)
    assert {r["status"] for r in rows} <= {"ok", "placeholder", "suspect"}


@needs_cw
def test_read_series_by_name_slot_full():
    s = read_series(CW_DIR, "600519", fields=["营业收入", "归母净利润", "EPS"])
    assert "20241231" in s and s["20241231"]["FN74"] > 1e11
    s2 = read_series(CW_DIR, "600519", fields=[74])
    assert close_enough(s["20241231"]["FN74"], s2["20241231"]["FN74"])
    s3 = read_series(CW_DIR, "600519")
    assert len(s3["20241231"]) == 584


@needs_cw
def test_cumulative_quarter_ends_only():
    cum = gpcw.cumulative(CW_DIR, "600519", "营业收入")
    assert {d[4:] for d in cum} <= {"0331", "0630", "0930", "1231"}
    s = read_series(CW_DIR, "600519", fields=[74])
    assert close_enough(cum["20241231"], s["20241231"]["FN74"])


@needs_cw
def test_single_quarters_sum_matches_annual():
    sq = single_quarters(CW_DIR, "600519", "营业收入",
                         start="20240331", end="20241231")
    assert set(sq) == {"20240331", "20240630", "20240930", "20241231"}
    cum = gpcw.cumulative(CW_DIR, "600519", "营业收入")
    assert close_enough(sum(sq.values()), cum["20241231"])
    assert close_enough(sq["20240331"], cum["20240331"])


@needs_cw
def test_single_quarters_gap_raise_and_skip(tmp_path):
    d = tmp_path / "cw_gap"
    d.mkdir()
    shutil.copy2(os.path.join(CW_DIR, "gpcw20241231.dat"), d / "gpcw20241231.dat")
    with pytest.raises(GpcwReportGap, match="20241231"):
        single_quarters(str(d), "600519", "营业收入")
    assert single_quarters(str(d), "600519", "营业收入", on_missing="skip") == {}


def test_approx_announce_date():
    assert approx_announce_date("20240331") == "20240430"
    assert approx_announce_date("20240630") == "20240831"
    assert approx_announce_date("20240930") == "20241031"
    assert approx_announce_date("20241231") == "20250430"
    with pytest.raises(ValueError):
        approx_announce_date("20240115")


def test_close_enough_float32_noise():
    assert close_enough(86228148224.0, 86228146421.62) is True
    assert close_enough(100.0, 100.00005) is True
    assert close_enough(100.0, 100.001) is False
    assert close_enough(None, None) is True
    assert close_enough(None, 1.0) is False


@needs_cw
def test_sync_cw_placeholder_and_idempotent(tmp_path):
    src, dst = tmp_path / "src", tmp_path / "dst"
    src.mkdir()
    dst.mkdir()
    for f in ["gpcw20241231.dat", "gpcw20250930.dat", "gpcw20240630.dat"]:
        shutil.copy2(os.path.join(CW_DIR, f), src / f)
    (src / "gpcw20260331.dat").write_bytes(b"\x00" * 20)   # 下载占位
    rep = sync_cw(str(src), str(dst))
    assert len(rep["copied"]) == 3 and rep["skipped_placeholder"] == 1
    rep2 = sync_cw(str(src), str(dst))
    assert rep2["copied"] == [] and len(rep2["up_to_date"]) == 3
    dst2 = tmp_path / "dst_dry"
    dst2.mkdir()
    rep3 = sync_cw(str(src), str(dst2), dry_run=True)
    assert len(rep3["copied"]) == 3 and rep3["dry_run"] and not any(dst2.iterdir())


@needs_cw
def test_sync_cw_only_missing_never_overwrites(tmp_path):
    """only_missing 模式: 目标已有的文件即使与源大小不同也不覆盖(双源分叉场景)。"""
    src, dst = tmp_path / "src", tmp_path / "dst"
    src.mkdir()
    dst.mkdir()
    shutil.copy2(os.path.join(CW_DIR, "gpcw20241231.dat"), src / "gpcw20241231.dat")
    # 目标侧放一个内容不同(截短)的同名文件, 模拟"官方新版"
    blob = open(os.path.join(CW_DIR, "gpcw20241231.dat"), "rb").read()
    truncated = blob[:len(blob) - 4096]          # 截短但仍是合法头
    (dst / "gpcw20241231.dat").write_bytes(truncated)
    rep = sync_cw(str(src), str(dst), only_missing=True)
    assert rep["copied"] == [] and len(rep["up_to_date"]) == 1
    assert (dst / "gpcw20241231.dat").read_bytes() == truncated   # 未被覆盖
    # 对照: 默认模式(不带 only_missing)会因大小不一致而覆盖
    rep2 = sync_cw(str(src), str(dst))
    assert rep2["copied"] == ["gpcw20241231.dat"]
    assert os.path.getsize(dst / "gpcw20241231.dat") == len(blob)


@needs_cw
def test_cli_gpcw(tmp_path):
    env = dict(os.environ, PYTHONPATH=str(ROOT),
               PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, "-m", "tdx_local.gpcw", CW_DIR, "600519"],
                       capture_output=True, timeout=120, env=env, cwd=str(ROOT))
    out = r.stdout.decode("utf-8", "replace")
    assert r.returncode == 0 and "财务历史序列" in out and "20241231" in out
    r2 = subprocess.run([sys.executable, "-m", "tdx_local.gpcw",
                         os.path.join(CW_DIR, "gpcw20241231.dat"), "600519"],
                        capture_output=True, timeout=120, env=env, cwd=str(ROOT))
    assert r2.returncode == 0 and "每股收益" in r2.stdout.decode("utf-8", "replace")


@needs_cw
def test_cli_gpcw_sync_dry_run(tmp_path):
    env = dict(os.environ, PYTHONPATH=str(ROOT), PYTHONIOENCODING="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    shutil.copy2(os.path.join(CW_DIR, "gpcw20241231.dat"), src / "gpcw20241231.dat")
    r = subprocess.run([sys.executable, "-m", "tdx_local.gpcw", "sync",
                        str(src), str(tmp_path / "dst"), "--dry-run"],
                       capture_output=True, timeout=120, env=env, cwd=str(ROOT))
    out = r.stdout.decode("utf-8", "replace")
    assert r.returncode == 0 and "dry-run" in out and "复制 1" in out


# ---------------------------------------------------------------- lday
@pytest.mark.skipif(not os.path.isdir(GTJA_LDAY), reason="无 gtja lday 目录")
class TestLday:
    def test_read_lday_real(self):
        bars = lday.read_lday(os.path.join(GTJA_LDAY, "sh600519.day"))
        ds = sorted(bars)
        assert len(ds) > 5000 and 19900101 < ds[0] < ds[-1] <= 20261231
        o, h, l, c, amt, vol = bars[ds[-1]]
        assert 0 < l <= h and c > 0 and amt > 0 and vol > 0

    def test_write_read_roundtrip(self, tmp_path):
        src = os.path.join(GTJA_LDAY, "sh600519.day")
        bars = lday.read_lday(src)
        p = tmp_path / "roundtrip.day"
        assert lday.write_lday(str(p), bars) == len(bars)
        assert lday.read_lday(str(p)) == bars

    def test_merge_noop_when_covered(self, tmp_path):
        src = os.path.join(GTJA_LDAY, "sh600519.day")
        dst = tmp_path / "nop.day"
        shutil.copy2(src, dst)
        rep = lday.merge_day(src, str(dst))
        assert rep["changed"] is False and rep["added"] == 0

    def test_merge_restores_tail(self, tmp_path):
        src = os.path.join(GTJA_LDAY, "sh600519.day")
        dst = tmp_path / "add.day"
        bars = lday.read_lday(src)
        cut = sorted(bars)[:-100]
        lday.write_lday(str(dst), {d: bars[d] for d in cut})
        rep = lday.merge_day(src, str(dst))
        assert rep["changed"] is True and rep["added"] == 100
        assert lday.read_lday(str(dst)) == bars

    def test_sync_dry_run_counts(self, tmp_path):
        dst = tmp_path / "dst"
        dst.mkdir()
        rep = lday.sync_lday(GTJA_LDAY, str(dst), dry_run=True)
        assert rep["copied"] > 5000 and not any(dst.iterdir())

    def test_sync_merge_and_only_missing(self, tmp_path):
        src, dst = tmp_path / "src", tmp_path / "dst"
        src.mkdir()
        dst.mkdir()
        for f in ["sh600519.day", "sh600000.day"]:
            shutil.copy2(os.path.join(GTJA_LDAY, f), src / f)
        bars = lday.read_lday(src / "sh600519.day")
        cut = sorted(bars)[:-50]
        lday.write_lday(str(dst / "sh600519.day"), {d: bars[d] for d in cut})
        shutil.copy2(src / "sh600000.day", dst / "sh600000.day")
        rep = lday.sync_lday(str(src), str(dst))
        assert rep["copied"] == 0 and rep["merged"] == 1
        assert lday.read_lday(str(dst / "sh600519.day")) == bars
        rep2 = lday.sync_lday(str(src), str(dst), only_missing=True)
        assert rep2["skipped"] == 2 and rep2["copied"] == 0

    def test_cli_sync(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        shutil.copy2(os.path.join(GTJA_LDAY, "sh600519.day"), src / "sh600519.day")
        env = dict(os.environ, PYTHONPATH=str(ROOT), PYTHONIOENCODING="utf-8")
        r = subprocess.run([sys.executable, "-m", "tdx_local.lday", "sync",
                            str(src), str(tmp_path / "dst"),
                            "--only-missing", "--dry-run"],
                           capture_output=True, timeout=120, env=env, cwd=str(ROOT))
        out = r.stdout.decode("utf-8", "replace")
        assert r.returncode == 0 and "同步dry-run" in out and "新复制 1" in out


# ---------------------------------------------------------------- 包导出
def test_package_exports_and_lazy_loading():
    import tdx_local
    names = ["read_gpcw", "read_series", "scan_reports", "single_quarters", "sync_cw",
             "close_enough", "approx_announce_date", "GpcwPlaceholder", "GpcwCorrupt",
             "GpcwReportGap", "TqClient", "TqError", "cw_fields"]
    for n in names:
        assert getattr(tdx_local, n), n
    with pytest.raises(AttributeError):
        tdx_local.no_such_thing


def test_tqerror_on_unreachable():
    bad = TqClient(base_url="http://127.0.0.1:1/", timeout=3)
    with pytest.raises(TqError, match="TQ 服务不可达"):
        bad.match("浦发银行")


# ---------------------------------------------------------------- TqClient 纯逻辑(mock, 不依赖服务)
def test_market_data_filters_field_list_and_surfaces_missing(monkeypatch):
    """服务端补救逻辑: field_list 客户端裁剪; 空信封/每股错误移入 _missing。"""
    tq = TqClient()
    fake = {"ErrorId": "0", "KlinePaged": True, "has_more": False,
            "Value": {
                "600000.SH": {"ErrorId": "0", "Date": [1, 2], "Close": [1.0, 2.0],
                              "Open": [1.0, 1.0]},
                "000001.SZ": {"ErrorId": "0", "Value": []},      # 空信封(本地无数据)
                "600036.SH": {"ErrorId": "2", "Error": "内部错误"},
            }}
    monkeypatch.setattr(tq, "paged", lambda method, **params: fake)
    r = tq.market_data(["600000.SH", "000001.SZ", "600036.SH"],
                       field_list=["Date", "Close"])
    assert set(r["Value"]) == {"600000.SH"}
    assert set(r["Value"]["600000.SH"]) == {"Date", "Close"}    # 已裁剪, ErrorId 已剥离
    assert set(r["_missing"]) == {"000001.SZ", "600036.SH"}


def test_market_data_passthrough_without_value(monkeypatch):
    tq = TqClient()
    monkeypatch.setattr(tq, "paged", lambda method, **params: {"ErrorId": "0"})
    assert tq.market_data(["600000.SH"]) == {"ErrorId": "0"}


def test_divid_factors_parses_columnar_per10(monkeypatch):
    """列式返回 + 每10股 -> 每股换算; 坏行跳过。"""
    tq = TqClient()
    fake = {"ErrorId": "0",
            "Date": ["20240619", "20241220", "20250626", "20260626"],
            "Type": ["1", "1", "1", "1"],
            "Value": [["308.76", "0.00", "0.00", "0.00"],
                      ["238.82", "0.00", "0.00", "0.00"],
                      ["280.242", "0.00", "0.00", "0.00"],
                      []]}                                   # 坏行(缺数据)
    monkeypatch.setattr(tq, "call", lambda method, **params: fake)
    div = tq.divid_factors("600519.SH")
    assert abs(div["20240619"] - 30.876) < 1e-9
    assert abs(div["20241220"] - 23.882) < 1e-9
    assert abs(div["20250626"] - 28.0242) < 1e-9
    assert "20260626" not in div


# ---------------------------------------------------------------- 网络层重试(mock urlopen)
class _FakeResp:
    def __init__(self, data: bytes):
        self._data = data

    def read(self):
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_call_retries_once_on_network_error():
    """首次连接失败自动重试一次并成功, 中间仅退避 0.5s(测试中打桩)。"""
    tq = TqClient()
    ok = json.dumps({"result": {"ErrorId": "0", "Value": 42}}).encode()
    calls = []

    def flaky(url, timeout=None):
        calls.append(url)
        if len(calls) == 1:
            raise urllib.error.URLError("connection refused")
        return _FakeResp(ok)

    with patch("urllib.request.urlopen", flaky), patch("time.sleep"):
        r = tq.call("get_match_stkinfo", key_word="x")
    assert len(calls) == 2 and r["Value"] == 42


def test_call_tqerror_after_retry_exhausted():
    tq = TqClient()

    def always_down(url, timeout=None):
        raise urllib.error.URLError("refused")

    with patch("urllib.request.urlopen", always_down), patch("time.sleep"):
        with pytest.raises(TqError, match="TQ 服务不可达"):
            tq.call("get_match_stkinfo", key_word="x")


def test_call_non_json_response_becomes_tqerror():
    """网关 200 但返回 HTML 错误页 -> 统一 TqError, 不裸抛 JSONDecodeError。"""
    tq = TqClient()
    bad = _FakeResp(b"<html>Service Unavailable</html>")
    with patch("urllib.request.urlopen", lambda url, timeout=None: bad):
        with pytest.raises(TqError, match="非 JSON"):
            tq.call("get_match_stkinfo", key_word="x")


# ---------------------------------------------------------------- 指标库(tdx_local.indicators)
def test_ind_sma_series_and_last():
    assert ind.sma([1, 2, 3, 4, 5], 3) == [None, None, 2.0, 3.0, 4.0]
    assert ind.ma([1, 2, 3, 4, 5], 3) == 4.0
    assert ind.ma([1, 2], 3) is None          # 数据不足 n 根


def test_ind_ema_guards_and_constant():
    assert ind.ema([], 12) == []              # 空列表不炸(原散落版会 IndexError)
    assert ind.ema([7.0], 12) == [7.0]
    assert ind.ema([5.0] * 10, 12) == [5.0] * 10   # 常数序列 EMA 恒等


def test_ind_macd_flat_is_zero():
    dif, dea, hist = ind.macd([10.0] * 40)
    assert all(abs(x) < 1e-9 for x in dif + dea + hist)
    assert len(hist) == 40


def test_ind_macd_state_cross():
    assert ind.macd_state([10.0] * 30 + [20.0]) == "金叉"   # 末端跳空
    assert ind.macd_state([20.0] * 30 + [10.0]) == "死叉"   # 末端跳水
    assert ind.macd_state([1.0]) == "数据不足"


def test_ind_golden_cross_bull_align_volume_surge():
    assert ind.is_golden_cross([1.0] * 11 + [100.0])          # 末端大阳线
    assert not ind.is_golden_cross([100.0] * 11 + [1.0])      # 末端跳水
    up = [5.0 + 0.5 * i for i in range(21)]
    assert ind.is_bull_align(up)
    assert not ind.is_bull_align(up[::-1])                    # 下跌排列必假
    assert ind.is_volume_surge([10.0] * 5 + [100.0])
    assert not ind.is_volume_surge([10.0] * 6)                # 无放量


def test_ind_total_return_reinvest_and_nonmutating():
    closes = [10.0] * 3
    dates = [20240101, 20240102, 20240103]
    divs = {20240102: 1.0}
    p_ret, t_ret, n_div = ind.total_return_with_dividends(closes, dates, divs)
    assert p_ret == 0.0 and n_div == 1
    assert t_ret == pytest.approx(10.0)       # 每股派1元按10元再投 -> 10%份额增益
    assert divs == {20240102: 1.0}            # 回归: 不修改入参(原实现原地 pop)


def test_ind_max_drawdown():
    assert ind.max_drawdown([10.0, 12.0, 6.0, 8.0]) == pytest.approx(-50.0)
    assert ind.max_drawdown([1.0, 2.0, 3.0]) == 0.0    # 一路新高无回撤
    assert ind.max_drawdown([5.0]) == 0.0


# ---------------------------------------------------------------- 日线缓存(tdx_local.kcache)
class _FakeKlineClient:
    """market_data 打桩: 按 TQ 列式形态返回合成日K。"""

    def __init__(self, bars_by_code):
        self.bars = bars_by_code

    def market_data(self, codes, **kw):
        value, missing = {}, {}
        for c in codes:
            b = self.bars.get(c)
            if b is None:
                missing[c] = "本地无数据"
            else:
                value[c] = {k: list(v) for k, v in b.items()}
        return {"ErrorId": "0", "Value": value, "_missing": missing}


def _synth_bars(dates, base=10.0):
    closes = [base + i for i in range(len(dates))]
    return {"Date": list(dates),
            "Open": [c - 0.5 for c in closes],
            "High": [c + 0.5 for c in closes],
            "Low": [c - 1.0 for c in closes],
            "Close": closes,
            "Volume": [1000 + i for i in range(len(dates))],
            "Amount": [c * 1000.0 for c in closes]}


def test_kcache_path_for(tmp_path):
    assert kcache.path_for(tmp_path, "600000.SH").name == "sh600000.day"
    assert kcache.path_for(tmp_path, "000001.SZ").name == "sz000001.day"
    assert kcache.path_for(tmp_path, "430047.BJ").name == "bj430047.day"


def test_kcache_update_read_roundtrip_and_merge(tmp_path):
    fake = _FakeKlineClient({
        "600000.SH": _synth_bars([20240101, 20240102, 20240103]),
    })
    stats = kcache.update(fake, ["600000.SH", "000858.SZ"], cache_dir=str(tmp_path))
    assert stats["600000.SH"]["added"] == 3
    assert "000858.SZ" in stats["_missing"]        # 无数据代码进 _missing 不炸
    bars = kcache.read(str(tmp_path), "600000.SH")
    assert bars["Date"] == [20240101, 20240102, 20240103]
    assert bars["Close"] == [10.0, 11.0, 12.0]     # ×100 定点存储往返无损
    assert bars["Volume"][0] == 1000

    # 增量: 多两根 + 重叠日数据变化 -> 日期并集, 重叠日以 TQ 侧为准
    fake.bars["600000.SH"] = _synth_bars([20240102, 20240103, 20240104, 20240105])
    stats2 = kcache.update(fake, ["600000.SH"], cache_dir=str(tmp_path))
    assert stats2["600000.SH"] == {"added": 2, "updated": 2, "total": 5}
    assert kcache.read(str(tmp_path), "600000.SH")["Close"] == [10.0, 10.0, 11.0, 12.0, 13.0]


def test_kcache_read_point_in_time(tmp_path):
    fake = _FakeKlineClient({"600519.SH": _synth_bars(
        [20240101, 20240102, 20240103, 20240104])})
    kcache.update(fake, ["600519.SH"], cache_dir=str(tmp_path))
    b = kcache.read(str(tmp_path), "600519.SH", end_date=20240102)
    assert b["Date"] == [20240101, 20240102]       # 截至: 未来K线不可见
    b = kcache.read(str(tmp_path), "600519.SH", count=2)
    assert b["Date"] == [20240103, 20240104]       # 末端 n 根
    assert kcache.read(str(tmp_path), "600000.SH") == {}   # 无缓存文件返回空


def test_kcache_read_many_skips_missing(tmp_path):
    fake = _FakeKlineClient({"600000.SH": _synth_bars([20240101])})
    kcache.update(fake, ["600000.SH"], cache_dir=str(tmp_path))
    got = kcache.read_many(str(tmp_path), ["600000.SH", "000001.SZ"])
    assert set(got) == {"600000.SH"}


# ---------------------------------------------------------------- 回测引擎(tdx_local.backtest)
def _bt_bars(dates, closes):
    closes = [float(c) for c in closes]
    return {"Date": list(dates), "Open": closes, "High": closes,
            "Low": closes, "Close": closes,
            "Volume": [1] * len(dates), "Amount": [0.0] * len(dates)}


def test_bt_slice_asof_no_lookahead():
    bars = _bt_bars([1, 2, 3, 4, 5], [10, 11, 12, 13, 14])
    s = bt.slice_asof(bars, 3)
    assert s["Date"] == [1, 2, 3]              # 截断: >T 的K线不可见
    s = bt.slice_asof(bars, 99, window=2)
    assert s["Date"] == [4, 5]                 # 末端 window 根
    assert bt.slice_asof(bars, 0)["Date"] == []


def test_bt_make_rebalances():
    cal = list(range(100, 130))                # 30 个交易日
    r = bt.make_rebalances(cal, last_n=30, step=10)
    assert r == [100, 110, 120, 129]           # 每10根一个 + 末端必收
    assert bt.make_rebalances([], 10, 5) == []


def test_bt_forward_return_plain_and_short():
    dates = [20240101, 20240102, 20240103, 20240104]
    closes = [10.0, 11.0, 12.0, 9.0]
    assert bt.forward_return(dates, closes, 0, 2) == pytest.approx(20.0)  # 10->12
    assert bt.forward_return(dates, closes, 2, 5) is None                 # 卖不出


def test_bt_forward_return_dividends():
    dates = [20240101, 20240102, 20240103]
    closes = [10.0, 10.0, 10.0]
    r = bt.forward_return(dates, closes, 0, 2, {"20240102": 1.0})
    assert r == pytest.approx(10.0)            # 持有期除息再投 -> +10%
    r2 = bt.forward_return(dates, closes, 1, 1, {"20240102": 1.0})
    assert r2 == pytest.approx(0.0)            # 买入当日除息归前手, 不计


def test_bt_run_point_in_time_and_benchmark():
    dates = list(range(20240101, 20240131))    # 30 个交易日
    up = _bt_bars(dates, [10 + 0.5 * i for i in range(30)])
    flat = _bt_bars(dates, [10.0] * 30)
    bars = {"AAA": up, "999999.SH": flat}
    rebal = bt.make_rebalances(dates, last_n=30, step=10)

    res = bt.run(bars, rebal, lambda asof: ["AAA"], horizons=(5,),
                 dividends_by_code={}, benchmark="999999.SH")
    assert all(p["code"] == "AAA" for p in res["picks"])
    m = res["summary"][5]
    # 末端调仓日买在最后一根K线无法结算(ret=None), 记入 picks 但不计入统计
    assert len(res["picks"]) == 4 and m["n"] == 3 and m["win"] == 100.0
    assert m["avg_excess"] == pytest.approx(m["avg"])   # 基准平盘 -> 超额=绝对收益

    seen = []

    def spy(asof):
        seen.extend(asof["AAA"]["Date"])
        return []

    bt.run(bars, rebal, spy, horizons=(5,))
    assert max(seen) <= max(rebal)             # 回归: 策略只见 <= 调仓日的K线


def test_bt_run_dividend_callable_and_report():
    dates = list(range(20240101, 20240131))
    flat = _bt_bars(dates, [10.0] * 30)
    bars = {"AAA": flat, "999999.SH": _bt_bars(dates, [10.0] * 30)}
    calls = []

    def div_getter(code):
        calls.append(code)
        return {"20240105": 0.5}

    res = bt.run(bars, bt.make_rebalances(dates, 30, 10),
                 lambda asof: ["AAA"], horizons=(5,),
                 dividends_by_code=div_getter, benchmark="999999.SH")
    assert calls.count("AAA") == 1             # callable 逐股只调一次(记忆化)
    text = bt.report(res)
    assert "持有期" in text and "胜率" in text and "5日" in text


def test_total_return_with_splits():
    """10送10+派息: 不带送转的模型把腰斩当亏损, 带送转才是真总回报。"""
    dates = [20240101, 20240102, 20240103]
    closes = [100.0, 50.0, 51.0]               # 除权日 100 -> 50(10送10)
    divs, spl = {"20240102": 0.3}, {"20240102": 1.0}
    p, t, n = ind.total_return_with_dividends(closes, dates, divs, spl, years=5)
    assert (p, n) == (pytest.approx(-49.0), 1)
    # 1股 -> 派0.3元 + 变2股 -> 再投 0.3/50 -> (2.006*51)/100 - 1
    assert t == pytest.approx(2.306, abs=1e-3)
    _, t0, _ = ind.total_return_with_dividends(closes, dates, divs, years=5)
    assert t0 == pytest.approx(-48.694, abs=1e-3)   # 不带送转: 亏损假象
    # 送转在窗口外不产生影响
    _, t2, _ = ind.total_return_with_dividends(closes, dates, divs,
                                               {"20200101": 1.0}, years=5)
    assert t2 == pytest.approx(t0)


def test_bt_forward_return_splits_and_costs():
    dates = [20240101, 20240102, 20240103]
    closes = [100.0, 50.0, 51.0]
    r = bt.forward_return(dates, closes, 0, 2, {"20240102": 0.3},
                          {"20240102": 1.0})
    assert r == pytest.approx(2.306, abs=1e-3)
    # 成本: 毛+20% -> (1.2*0.99/1.01 - 1)
    r2 = bt.forward_return([1, 2], [100.0, 110.0], 0, 1,
                           cost_in=0.01, cost_out=0.01)
    assert r2 == pytest.approx((1.10 * 0.99 / 1.01 - 1) * 100)
    # 无成本路径数值不受影响(向后兼容)
    assert bt.forward_return([1, 2], [100.0, 110.0], 0, 1) == pytest.approx(10.0)


def test_bt_forward_return_sell_rule():
    bars = {"Date": [1, 2, 3, 4], "Close": [100.0, 105.0, 103.0, 104.0]}

    def rule(asof, held_days):
        cl = asof["Close"]
        return len(cl) >= 3 and cl[-1] < cl[-2]    # 收盘跌破前日即卖

    r = bt.forward_return(bars["Date"], bars["Close"], 0, 3,
                          sell_rule=rule, bars=bars)
    assert r == pytest.approx(3.0)                 # 第3根 103 提前卖, 非 104
    assert bt.forward_return(bars["Date"], bars["Close"], 0, 3) == \
        pytest.approx(4.0)
    with pytest.raises(TypeError):
        bt.forward_return(bars["Date"], bars["Close"], 0, 3, sell_rule=rule)


def test_bt_run_sell_rule_yearly_curve():
    dates = list(range(20240101, 20240131))
    up = _bt_bars(dates, [10 + 0.5 * i for i in range(30)])
    bars = {"AAA": up, "999999.SH": _bt_bars(dates, [10.0] * 30)}

    def sell_at_15(asof, held_days):
        return held_days >= 2 and max(asof["Date"]) >= 20240115

    res = bt.run(bars, bt.make_rebalances(dates, 30, 10), lambda a: ["AAA"],
                 horizons=(5,), benchmark="999999.SH", sell_rule=sell_at_15)
    assert res["picks"]
    for p in res["picks"]:
        sd = p["sell_date"].get(5)
        if sd is None:
            continue
        if p["early"].get(5):
            assert sd - p["date"] < 5              # 提前触发必早于到期
        else:
            assert sd - p["date"] == 5             # 未触发自然到期
    # 分年与曲线结构
    y = res["yearly"][5]
    assert all(set(m) >= {"n", "win", "avg", "avg_excess"} for m in y.values())
    curve = res["curve"][5]
    assert curve and all(nav > 0 for _, nav in curve)
    assert curve == sorted(curve)                  # 卖出日升序
    assert bt.report_yearly(res).startswith("分年")


def test_bt_costs_default_zero_is_unchanged():
    """默认无成本时, 新版 run 与旧版逐笔收益一致(兼容回归)。"""
    dates = list(range(20240101, 20240131))
    bars = {"AAA": _bt_bars(dates, [10 + 0.1 * i for i in range(30)]),
            "999999.SH": _bt_bars(dates, [10.0] * 30)}
    rebal = bt.make_rebalances(dates, 30, 10)
    res = bt.run(bars, rebal, lambda a: ["AAA"], horizons=(5,),
                 benchmark="999999.SH")
    m = res["summary"][5]
    assert m["n"] >= 1 and m["win"] == pytest.approx(100.0)
    assert m["avg"] > 0                            # 单调上涨股必有正收益
