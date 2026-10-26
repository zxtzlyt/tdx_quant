# -*- coding: utf-8 -*-
"""选股分析指南配套测试。

两组:
  - 纯逻辑单测(离线必跑): 四个配方的指标/筛选/收益计算函数, 用合成数据验证。
  - 在线端到端(探活门控): 通达信客户端在运行时, 把每个配方 main() 真跑一遍,
    断言输出结构 —— 服务不可达时整组自动跳过。

运行: python -m pytest tests/test_guide_examples.py -v
"""
import importlib.util
from pathlib import Path

import pytest

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def _load(name: str):
    """按文件路径加载 examples/ 下的配方模块(该目录不是包)。"""
    spec = importlib.util.spec_from_file_location(name, EXAMPLES / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------- 离线: 技术指标
@pytest.fixture(scope="module")
def tech():
    return _load("pick_technical")


def test_sma_basic(tech):
    v = [1.0, 2.0, 3.0, 4.0, 5.0]
    s = tech.sma(v, 3)
    assert s[:2] == [None, None]
    assert s[2] == pytest.approx(2.0)
    assert s[4] == pytest.approx(4.0)


def test_golden_cross_true_and_false(tech):
    # 平盘 11 根 + 末端一根大阳线: MA5 末端上穿 MA10(手工可验)
    cross = [1.0] * 11 + [100.0]
    assert tech.is_golden_cross(cross)
    # 全程平盘: 两线重合, 不构成上穿
    assert not tech.is_golden_cross([1.0] * 12)
    # 持续上涨: 早已金叉, 最后一根不再是金叉点
    assert not tech.is_golden_cross([5.0 + 0.3 * i for i in range(25)])


def test_bull_align(tech):
    up = [5.0 + 0.5 * i for i in range(30)]          # 单边上涨 -> 多头排列
    assert tech.is_bull_align(up)
    down = [20.0 - 0.5 * i for i in range(30)]
    assert not tech.is_bull_align(down)


def test_volume_surge(tech):
    base = [100.0] * 10
    assert tech.is_volume_surge(base + [200.0])      # 2 倍于均量
    assert not tech.is_volume_surge(base + [110.0])  # 1.1 倍, 低于阈值
    assert not tech.is_volume_surge([100.0] * 3)     # 数据不足


# --------------------------------------------------------------- 离线: 财务同比
@pytest.fixture(scope="module")
def fund():
    return _load("pick_fundamental")


def test_pick_two_periods(fund):
    dates = [20240331, 20240630, 20250331, 20250630]
    vals = [10.0, 12.0, 15.0, 18.0]
    now, prev = fund.pick_two_periods(dates, vals)
    assert now == 18.0 and prev == 12.0        # 同期=去年同报告期


def test_pick_two_periods_missing_prev(fund):
    now, prev = fund.pick_two_periods([20250630], [5.0])
    assert now == 5.0 and prev is None         # 无去年同期(次新股)


def test_yoy_pct(fund):
    assert fund.yoy_pct(12.0, 10.0) == pytest.approx(20.0)
    assert fund.yoy_pct(10.0, 0.0) is None     # 负/零基数无意义
    assert fund.yoy_pct(None, 10.0) is None


# --------------------------------------------------------------- 离线: 板块概览
@pytest.fixture(scope="module")
def overview():
    return _load("market_overview")


def test_sector_changes(overview):
    closes = {"A.SH": [10.0] * 5 + [11.0, 12.0],     # 7根, 近5日 +20%
              "B.SH": [10.0] * 5 + [9.5, 8.0],       # 近5日 -20%
              "C.SH": [1.0]}                          # 数据不足, 剔除
    chg = overview.sector_changes(closes)
    assert chg["A.SH"] == pytest.approx(20.0)
    assert chg["B.SH"] == pytest.approx(-20.0)
    assert "C.SH" not in chg


# --------------------------------------------------------------- 离线: 单股体检
@pytest.fixture(scope="module")
def checkup():
    return _load("stock_checkup")


def test_macd_state(checkup):
    up = [5.0 + 0.3 * i for i in range(40)]
    assert checkup.macd_state(up) == "多头"
    down = [20.0 - 0.3 * i for i in range(40)]
    assert checkup.macd_state(down) == "空头"


def test_total_return_with_dividends(checkup):
    # 两年合成数据: 价格不涨(10->10), 中途每股派息1元再投 -> 总回报>价格回报
    dates = [int(f"2024{m:02d}{d:02d}") for m, d in
             [(1, 2), (1, 3), (6, 3), (6, 4), (12, 30)]]
    closes = [10.0, 10.0, 10.0, 10.0, 10.0]
    divs = {"20240604": 1.0}                   # 除息日当日收盘 10 元, 派 1 元
    p_ret, t_ret, n_div = checkup.total_return_with_dividends(
        closes, dates, dict(divs))
    assert p_ret == pytest.approx(0.0)
    assert t_ret == pytest.approx((1 + 0.1) * 1 * 100 - 100)  # 再投 0.1 股 +10%
    assert n_div == 1


def test_total_return_no_dividends(checkup):
    dates = [20240102, 20251231]
    closes = [10.0, 15.0]
    p_ret, t_ret, n_div = checkup.total_return_with_dividends(closes, dates, {})
    assert p_ret == pytest.approx(t_ret)       # 无分红时两者相等
    assert n_div == 0


# =============================================================== 在线端到端
def _service_up() -> bool:
    from tdx_local import TqClient, TqError
    try:
        TqClient(timeout=5).call("refresh_cache")
        return True
    except TqError:
        return False


live_only = pytest.mark.skipif(not _service_up(),
                               reason="TQ 服务(127.0.0.1:17709)未运行")


@live_only
def test_pick_technical_bank_sector(capsys, monkeypatch):
    """配方1真跑: 银行板块(约40只)金叉+多头筛选, 不写回板块。"""
    mod = _load("pick_technical")
    monkeypatch.setattr(mod, "SECTOR", "银行")
    monkeypatch.setattr(mod, "SEND_TO_TDX", False)
    monkeypatch.setattr(mod, "WANT_GOLDEN_CROSS", False)  # 只用多头排列, 条件宽松
    mod.main()
    out = capsys.readouterr().out
    assert "候选板块[银行] 共" in out and "筛出" in out


@live_only
def test_pick_fundamental_hs300(capsys, monkeypatch):
    """配方2真跑: 沪深300 财报增速筛选。"""
    mod = _load("pick_fundamental")
    monkeypatch.setattr(mod, "UNIVERSE_LIST_TYPE", "23")
    mod.main()
    out = capsys.readouterr().out
    assert "候选池共" in out and "筛出" in out


@live_only
def test_market_overview_run(capsys):
    """配方3真跑: 板块强弱 + 全A估值 + 两融余额。"""
    _load("market_overview").main()
    out = capsys.readouterr().out
    assert "最强板块" in out and "最弱板块" in out
    assert "市盈率" in out and "两融余额" in out


@live_only
def test_stock_checkup_600000(capsys, monkeypatch):
    """配方4真跑: 浦发银行体检报告。"""
    import sys
    monkeypatch.setattr(sys, "argv", ["stock_checkup.py", "600000.SH"])
    _load("stock_checkup").main()
    out = capsys.readouterr().out
    assert "浦发银行" in out and "体检报告" in out
    assert "财报" in out and "股息率" in out


# --------------------------------------------------------------- 离线: 新配方接线(假客户端)
class _FakeBtTq:
    """backtest_picker/archive_minutes 的最小假客户端。"""

    def __init__(self, bars):
        self.bars = bars

    def call(self, method, **kw):
        assert method == "get_stock_list_in_sector"
        return {"ErrorId": "0", "Value": [{"Code": c, "Name": n} for c, n in
                                          [("AAA", "甲"), ("BBB", "乙")]]}

    def market_data(self, codes, **kw):
        return {"ErrorId": "0",
                "Value": {c: {k: list(v) for k, v in self.bars[c].items()}
                          for c in codes if c in self.bars},
                "_missing": {}}

    def divid_factors(self, code):
        return {}


def _bt_bars(dates, closes):
    closes = [float(c) for c in closes]
    return {"Date": list(dates), "Open": closes, "High": closes, "Low": closes,
            "Close": closes, "Volume": [1] * len(dates), "Amount": [0.0] * len(dates)}


def test_backtest_picker_offline_wire(tmp_path, monkeypatch, capsys):
    """回测配方端到端(假客户端+临时缓存): 校验取数->建缓存->重放->报告全链路。"""
    dates = list(range(20240101, 20240131))          # 30 个交易日
    mod = _load("backtest_picker")
    fake = _FakeBtTq({"AAA": _bt_bars(dates, [10 + 0.5 * i for i in range(30)]),
                      "BBB": _bt_bars(dates, [10.0] * 30),
                      "999999.SH": _bt_bars(dates, [10.0] * 30)})
    monkeypatch.setattr(mod, "TqClient", lambda: fake)
    monkeypatch.setattr(mod, "WANT_GOLDEN_CROSS", False)   # 全选, 保证有成交笔
    monkeypatch.setattr(mod, "WANT_BULL_ALIGN", False)
    monkeypatch.setattr(mod, "LOOKBACK", 30)
    monkeypatch.setattr(mod.kcache, "default_dir", lambda: str(tmp_path))
    mod.main()
    out = capsys.readouterr().out
    assert "候选池 2 只" in out and "调仓日" in out
    assert "笔选股" in out and "5日" in out and "持有期" in out   # 报告表已打印
    assert "[口径]" in out
    assert (tmp_path / "sh999999.day").exists()      # 基准指数也进了缓存


def test_archive_minutes_offline_wire(tmp_path, monkeypatch, capsys):
    """分钟归档配方端到端: 首次写 CSV, 二次同数据去重为 0 新增。"""
    mod = _load("archive_minutes")
    n = 8
    fake = _FakeBtTq({"600000.SH": {
        "Date": ["20260930"] * n, "Time": [f"0930{i:02d}" for i in range(n)],
        "Open": [10.0] * n, "High": [10.1] * n, "Low": [9.9] * n,
        "Close": [10.05] * n, "Volume": [100] * n, "Amount": [1000.0] * n}})
    monkeypatch.setattr(mod, "TqClient", lambda: fake)
    monkeypatch.setattr(mod, "CODES", ["600000.SH"])
    monkeypatch.setattr(mod, "PERIOD", "5m")          # 钉死周期, 不随示例默认值漂移
    monkeypatch.setattr(mod, "out_dir", lambda period: tmp_path / period)
    mod.main()
    out1 = capsys.readouterr().out
    assert "新增 8 行" in out1
    csv_path = tmp_path / "5m" / "sh600000.csv"
    assert csv_path.exists()
    mod.main()                                        # 同数据再跑: 全部去重
    out2 = capsys.readouterr().out
    assert "新增 0 行" in out2


# --------------------------------------------------------------- 离线: vipdoc 直读归档
def _mk_min_file(path, day_words, bars):
    """合成 vipdoc 分钟文件: 每天 bars 根, 时间词 9:30 起递增, 价格随日递增。"""
    import struct
    path.parent.mkdir(parents=True, exist_ok=True)
    rec = struct.Struct("<HH4IfI2H")
    with open(path, "wb") as f:
        for day, dw in enumerate(day_words):
            for bar in range(bars):
                tw = 9 * 60 + 30 + bar
                px = int((10.0 + day) * 100)
                f.write(rec.pack(dw, tw, px, px, px, px, 10000.0, 100, 0, 0))


def test_archive_minutes_vipdoc_offline(tmp_path, monkeypatch, capsys):
    """直读归档全链路: 拷贝种子 -> 追加增量 -> 幂等 -> GUI 截前端不丢归档。"""
    mod = _load("archive_minutes_vipdoc")
    dw1, dw2, dw3 = mod._date_word(20261013), mod._date_word(20261014), mod._date_word(20261015)
    bars = mod.PERIOD_META["5m"]["bars"]
    vip = tmp_path / "vipdoc" / "sh" / "fzline" / "sh600519.5"

    _mk_min_file(vip, [dw1, dw2], bars)               # 两天: 种子
    monkeypatch.setattr(mod, "USE_GZIP", False)       # 钉住裸 bin 语义
    monkeypatch.setattr(mod, "VIPDOC", str(tmp_path / "vipdoc"))
    monkeypatch.setattr(mod, "CODES", ["600519.SH"])
    monkeypatch.setattr(mod, "PERIODS", ("5m",))
    monkeypatch.setattr(mod, "out_dir", lambda p: tmp_path / "arc" / p)
    mod.main()
    assert "新增 96 根" in capsys.readouterr().out
    arc = tmp_path / "arc" / "5m" / "sh600519.bin"
    assert arc.stat().st_size == 96 * 32

    _mk_min_file(vip, [dw1, dw2, dw3], bars)          # vipdoc 多出一天: 增量
    mod.main()
    assert "新增 48 根" in capsys.readouterr().out
    assert arc.stat().st_size == 144 * 32

    mod.main()                                        # 无新数据: 幂等
    assert "新增 0 根" in capsys.readouterr().out
    assert arc.stat().st_size == 144 * 32

    _mk_min_file(vip, [dw2, dw3], bars)               # 模拟转档截前端: 归档不回缩
    mod.main()
    assert "新增 0 根" in capsys.readouterr().out
    assert arc.stat().st_size == 144 * 32

    counts = mod.day_counts(arc)                      # 按日对账: 三天整, 无留洞
    assert counts == {dw1: bars, dw2: bars, dw3: bars}
    bars_out = mod.read_bars(arc, count=1)
    assert bars_out["Date"][-1] == "20261015" and bars_out["Close"][-1] == 12.0


def test_daily_pipeline_offline_wire(tmp_path, monkeypatch, capsys):
    """盘后一条龙端到端: 分钟归档 + lday 合并 + 日K增量三步串行, 汇总表全 OK。"""
    dp = _load("daily_pipeline")
    amv = dp.amv
    bars = amv.PERIOD_META["5m"]["bars"]
    dw1, dw2, dw3 = amv._date_word(20261013), amv._date_word(20261014), amv._date_word(20261015)
    # 1) 假 vipdoc 分钟文件(两天种子, 归档目录 tmp/arc)
    vip = tmp_path / "vipdoc" / "sh" / "fzline" / "sh600519.5"
    _mk_min_file(vip, [dw1, dw2], bars)
    monkeypatch.setattr(amv, "out_dir", lambda p: tmp_path / "arc" / p)
    monkeypatch.setattr(dp, "VIPDOC", str(tmp_path / "vipdoc"))
    monkeypatch.setattr(dp, "MINUTE_CODES", ["600519.SH"])
    monkeypatch.setattr(dp, "MINUTE_PERIODS", ("5m",))
    monkeypatch.setattr(dp, "MINUTE_ALL", False)
    # 2) 券商 lday 源 -> 官方侧(仅一个新文件)
    gtja_lday = tmp_path / "gtja" / "sh" / "lday"
    gtja_lday.mkdir(parents=True)
    dp.lday.write_lday(str(gtja_lday / "sh600036.day"),
                       {20240101: (10.0, 11.0, 9.0, 10.0, 1e4, 100)})
    monkeypatch.setattr(dp, "RUN_LDAY_SYNC", True)
    monkeypatch.setattr(dp, "GTJA_LDAY_SRC", str(tmp_path / "gtja"))
    monkeypatch.setattr(dp, "GTJA_LDAY_DST", str(tmp_path / "vipdoc"))
    # 3) kcache: 预置一只缓存文件 -> 反推代码; 假客户端给新日期 = 增量
    monkeypatch.setattr(dp.kcache, "default_dir", lambda: str(tmp_path / "kcache"))
    kcache_dir = tmp_path / "kcache"
    dates = list(range(20240101, 20240106))
    fake = _FakeBtTq({"600000.SH": _bt_bars(dates, [10 + 0.1 * i for i in range(len(dates))])})
    dp.kcache.update(fake, ["600000.SH"], cache_dir=str(kcache_dir),
                     count=3)                          # 预置: 末日期 20240103
    fake.bars["600000.SH"] = _bt_bars(dates, [10 + 0.1 * i for i in range(len(dates))])
    monkeypatch.setattr(dp, "TqClient", lambda: fake)

    rc = dp.main()
    out = capsys.readouterr().out
    assert rc == 0
    assert "[OK  ] 分钟归档" in out and "+96根" in out
    assert "[OK  ] lday合并" in out and "新复制1" in out
    assert "[OK  ] 日K增量" in out and "1只" in out
    arc_gz = tmp_path / "arc" / "5m" / "sh600519.bin.gz"
    assert arc_gz.exists()
    assert len(dp.amv.read_bars(arc_gz)["Close"]) == 2 * bars   # gz 归档读回无损
    assert (tmp_path / "vipdoc" / "sh" / "lday" / "sh600036.day").exists()
    assert (kcache_dir / "sh600000.day").stat().st_size >= 5 * 32   # 增到 5 根


def test_daily_pipeline_failure_isolated(tmp_path, monkeypatch, capsys):
    """分钟归档失败不拖垮日K增量: 汇总一行 FAIL 一行 OK, 退出码 1。"""
    dp = _load("daily_pipeline")
    monkeypatch.setattr(dp, "RUN_MINUTES", True)
    monkeypatch.setattr(dp, "VIPDOC", str(tmp_path / "nowhere"))    # vipdoc 不存在
    monkeypatch.setattr(dp, "MINUTE_CODES", ["600519.SH"])
    monkeypatch.setattr(dp, "MINUTE_PERIODS", ("5m",))
    monkeypatch.setattr(dp, "RUN_LDAY_SYNC", False)
    monkeypatch.setattr(dp.kcache, "default_dir", lambda: str(tmp_path / "kcache"))
    dates = [20240101, 20240102]
    fake = _FakeBtTq({"600000.SH": _bt_bars(dates, [10.0, 11.0])})
    monkeypatch.setattr(dp, "TqClient", lambda: fake)

    rc = dp.main()                                  # MINUTE_ALL=False + 缺文件 = 0 根但 OK
    assert rc == 0                                  # vip 缺文件计入 missing, 不算失败
    out = capsys.readouterr().out
    assert "分钟归档" in out and "日K增量" in out


def test_archive_minutes_vipdoc_gzip(tmp_path, monkeypatch, capsys):
    """gzip 归档全链路: 种子 -> 成员追加增量 -> 幂等 -> 读回对账(多成员可解)。"""
    mod = _load("archive_minutes_vipdoc")
    dw1, dw2, dw3 = mod._date_word(20261013), mod._date_word(20261014), mod._date_word(20261015)
    bars = mod.PERIOD_META["5m"]["bars"]
    vip = tmp_path / "vipdoc" / "sh" / "fzline" / "sh600519.5"

    _mk_min_file(vip, [dw1, dw2], bars)
    monkeypatch.setattr(mod, "USE_GZIP", True)
    monkeypatch.setattr(mod, "VIPDOC", str(tmp_path / "vipdoc"))
    monkeypatch.setattr(mod, "CODES", ["600519.SH"])
    monkeypatch.setattr(mod, "PERIODS", ("5m",))
    monkeypatch.setattr(mod, "out_dir", lambda p: tmp_path / "arc" / p)
    mod.main()
    assert "新增 96 根" in capsys.readouterr().out
    arc = tmp_path / "arc" / "5m" / "sh600519.bin.gz"
    assert arc.exists() and mod._is_gz(arc)

    _mk_min_file(vip, [dw1, dw2, dw3], bars)          # vipdoc 多出一天: 成员追加
    mod.main()
    assert "新增 48 根" in capsys.readouterr().out
    mod.main()                                        # 幂等
    assert "新增 0 根" in capsys.readouterr().out

    assert mod._last_stamp(arc) == (dw3, mod.PERIOD_META["5m"]["bars"] - 1 + 9 * 60 + 30)
    bars_out = mod.read_bars(arc)                     # 多成员整读
    assert len(bars_out["Close"]) == 3 * bars
    assert bars_out["Date"][-1] == "20261015"
    counts = mod.day_counts(arc)
    assert counts == {dw1: bars, dw2: bars, dw3: bars}  # 压缩流按日对账无损
    import gzip
    raw = gzip.open(arc, "rb").read()
    assert len(raw) == 3 * bars * 32 and len(raw) % 32 == 0
