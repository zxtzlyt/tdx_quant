# -*- coding: utf-8 -*-
"""离线测试: cw_fields / gpcw / lday 解析与包导出, 不依赖 TQ 服务在线。

gpcw/lday 的真实数据用例依赖本机数据目录(见 conftest), 缺失时自动跳过;
其余为纯逻辑用例, 任何环境可跑。运行: python -m pytest tests/test_offline.py -v
"""
import os
import shutil
import struct
import subprocess
import sys
from unittest.mock import patch

import pytest

from tdx_local import (TqClient, TqError, close_enough, approx_announce_date,
                       read_gpcw, read_series, scan_reports, single_quarters,
                       sync_cw, GpcwPlaceholder, GpcwCorrupt, GpcwReportGap)
from tdx_local import cw_fields, gpcw, lday
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
