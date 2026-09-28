# -*- coding: utf-8 -*-
"""通达信 TQ 本地 HTTP JSON-RPC 客户端 (127.0.0.1:17709)。

依赖: 仅 Python 标准库。前置条件: 通达信金融终端(支持 TQ 策略的版本)正在运行并登录。

使用示例::

    from tdx_local import TqClient

    tq = TqClient()
    tq.match("浦发银行")                        # -> [{"Code": "600000.SH", "Name": "浦发银行"}]
    bars = tq.market_data(["600000.SH"], count=120, period="1d", dividend_type="front")
    # bars["Value"]["600000.SH"] -> {"Date": [...], "Open": [...], ...}

大结果分页(KlinePaged / TPythPaged / ProDataPaged)在本类内自动续取合并,
调用方拿到的始终是完整数据。
"""
import json
import urllib.request

DEFAULT_URL = "http://127.0.0.1:17709/"


class TqError(RuntimeError):
    """TQ 服务返回错误(ErrorId != 0 或 HTTP 层失败)。"""


class TqClient:
    def __init__(self, base_url: str = DEFAULT_URL, timeout: int = 60):
        self.base_url = base_url
        self.timeout = timeout

    # ---------- 基础调用 ----------

    def call(self, method: str, **params) -> dict:
        """发送一次 JSON-RPC 请求, 返回 result 字典(原样, 不做合并)。

        注意: params 必须始终发送(空参也传 {}), 2026-09-29 实测网关对缺
        "params" 键的请求返回 -32602 "MCP参数params必须为对象"。
        """
        body = {"id": 1, "method": method, "params": params}
        req = urllib.request.Request(
            self.base_url,
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise TqError(f"TQ 服务不可达({self.base_url}): {e}") from e
        if isinstance(payload.get("error"), dict):
            raise TqError(f"{method} JSON-RPC 错误: {payload['error']}")
        result = payload.get("result", {})
        if isinstance(result, dict) and result.get("ErrorId") not in (None, "0"):
            raise TqError(f"{method} 失败: {result.get('Error') or result}")
        return result

    # ---------- 分页自动续取 ----------

    def paged(self, method: str, **params) -> dict:
        """自动处理三种分页协议, 返回合并后的 result。

        - KlinePaged (get_market_data): result.has_more + next_stock_page_index, 按 stock_page_index 续取
        - ProDataPaged (专业数据): result.stock_page_index / stock_total_pages
        - TPythPaged: result.page_token / next_page_offset -> 传 _tpyth_page_token / _tpyth_page_offset
        """
        result = self.call(method, **params)
        merged = result

        if result.get("KlinePaged") and result.get("has_more"):
            merged = self._merge_kline_pages(method, params, result)
        elif result.get("ProDataPaged") and result.get("stock_total_pages", 1) > 1:
            merged = self._merge_prodata_pages(method, params, result)
        elif result.get("page_token") or result.get("TPythPaged"):
            merged = self._merge_tpyth_pages(method, params, result)
        return merged

    def _merge_kline_pages(self, method, params, first):
        """get_market_data 大结果: 按 next_stock_page_index 续取, 逐股拼接字段序列。"""
        pages = [first]
        page_index = first.get("next_stock_page_index", 1)
        while pages[-1].get("has_more"):
            nxt = self.call(method, **{**params, "stock_page_index": page_index})
            pages.append(nxt)
            if not nxt.get("has_more"):
                break
            page_index = nxt.get("next_stock_page_index", page_index + 1)

        value = {}
        for p in pages:
            for code, fields in (p.get("Value") or {}).items():
                dst = value.setdefault(code, {})
                for key, seq in fields.items():
                    if isinstance(seq, list) and isinstance(dst.get(key), list):
                        dst[key] = dst[key] + seq
                    else:
                        dst[key] = seq
        out = dict(pages[-1])
        out["Value"] = value
        out["has_more"] = False
        return out

    def _merge_prodata_pages(self, method, params, first):
        """专业数据接口: stock_page_index 从 0 遍历到 stock_total_pages-1, 合并 Value。"""
        total = first.get("stock_total_pages", 1)
        value = dict(first.get("Value") or {})
        for idx in range(1, total):
            nxt = self.call(method, **{**params, "stock_page_index": idx})
            value.update(nxt.get("Value") or {})
        out = dict(first)
        out["Value"] = value
        return out

    def _merge_tpyth_pages(self, method, params, first):
        """通用 TPythPaged: 按 page_token/next_page_offset 游标续取, 合并 Value。"""
        pages = [first]
        cur = first
        while cur.get("has_more"):
            extra = {}
            if cur.get("page_token") is not None:
                extra["_tpyth_page_token"] = cur["page_token"]
            if cur.get("next_page_offset") is not None:
                extra["_tpyth_page_offset"] = str(cur["next_page_offset"])
            cur = self.call(method, **{**params, **extra})
            pages.append(cur)

        value = pages[0].get("Value")
        for p in pages[1:]:
            nv = p.get("Value")
            if isinstance(value, dict) and isinstance(nv, dict):
                for key, seq in nv.items():
                    if isinstance(seq, list) and isinstance(value.get(key), list):
                        value[key] = value[key] + seq
                    else:
                        value[key] = seq
            elif nv is not None:
                value = nv
        out = dict(pages[-1])
        out["Value"] = value
        out["has_more"] = False
        return out

    # ---------- 常用封装 ----------

    def match(self, key_word: str) -> list:
        """证券名称 -> 代码。凡涉及证券名称必须先走这里, 禁止凭名字猜代码。"""
        r = self.call("get_match_stkinfo", key_word=key_word)
        return r.get("Value") or []

    def market_data(self, stock_list, period="1d", count=-1, start_time="", end_time="",
                    dividend_type="front", field_list=None, fill_data=True) -> dict:
        """K线行情(自动续取分页)。count>0 取最近 n 条; count<=0 用 start/end 区间。

        2026-09-29 实测的两个服务端行为, 本方法做了客户端补救:
          - 服务端忽略 field_list(恒返回全部字段) -> 返回前按 field_list 客户端裁剪;
          - 本地无数据的代码返回每股空信封 {"ErrorId":"0","Value":[]} 或每股
            ErrorId!=0, 全部静默 -> 这些代码从 Value 移入 result["_missing"]
            ({code: 原因}), 同时剥离每股混入的 ErrorId=="0" 字段。
        """
        params = {"stock_list": stock_list, "period": period, "count": count,
                  "start_time": start_time, "end_time": end_time,
                  "dividend_type": dividend_type, "fill_data": fill_data}
        if field_list is not None:
            params["field_list"] = field_list
        result = self.paged("get_market_data", **params)
        value = result.get("Value")
        if isinstance(value, dict):
            filtered, missing = {}, {}
            for code, per in value.items():
                if (isinstance(per, dict) and set(per) == {"ErrorId", "Value"}
                        and isinstance(per.get("Value"), list)):
                    missing[code] = per.get("ErrorId") or "本地无该周期数据(空信封)"
                    continue
                if isinstance(per, dict):
                    err = per.get("ErrorId")
                    if err not in (None, "0"):
                        missing[code] = err
                        continue
                    per = {k: v for k, v in per.items() if k != "ErrorId"}
                    if field_list:
                        per = {k: v for k, v in per.items() if k in field_list}
                filtered[code] = per
            result["Value"] = filtered
            if missing:
                result["_missing"] = missing
        return result

    def divid_factors(self, stock_code: str, start_time: str = "", end_time: str = "") -> dict:
        """分红送配 -> {除息日YYYYMMDD: 每股税前派息(元)}。

        2026-09-29 实测: 返回为列式结构(result.Date/Type/Value 平行数组, 非官方
        文档的行式 dict); Bonus 列为每10股派息(元), 此处已换算为每股; 服务端忽略
        start_time/end_time(恒返回全历史)。Type=11 扩缩股/15 重新调整的行 Bonus
        恒为 0, 不影响本口径; 需要送配股比例请自行走 call() 原始接口。
        """
        r = self.call("get_divid_factors", stock_code=stock_code,
                      start_time=start_time, end_time=end_time)
        dates, rows = r.get("Date") or [], r.get("Value") or []
        out = {}
        for d, row in zip(dates, rows):
            try:
                out[str(d)] = float(row[0]) / 10.0
            except (TypeError, ValueError, IndexError):
                continue
        return out

    def snapshot(self, stock_code: str, field_list=None) -> dict:
        """实时快照(含五档)。字段平铺在 result 顶层(2026-09-29 实测,
        与 get_stock_info 同款返回结构); 兼容旧版 Value 按 code 键控的形态。"""
        r = self.call("get_market_snapshot", stock_code=stock_code,
                      field_list=field_list or [])
        v = r.get("Value")
        if isinstance(v, dict) and v:
            return v.get(stock_code, v)
        meta_keys = {"ErrorId", "Error", "Msg", "run_id", "Value", "KlinePaged"}
        flat = {k: x for k, x in r.items() if k not in meta_keys}
        return flat

    def stock_info(self, stock_code: str, field_list=None) -> dict:
        """基础信息。注意: 本接口字段平铺在 result 顶层而非 Value(见 LOCAL_NOTES)。"""
        r = self.call("get_stock_info", stock_code=stock_code, field_list=field_list or [])
        return {k: v for k, v in r.items()
                if k not in ("ErrorId", "Error", "Msg", "run_id", "KlinePaged")}

    def trading_dates(self, start_time: str, end_time: str = "", market: str = "SH") -> list:
        """交易日列表。前置: 本地有上证指数(999999)K线, 缺失时先 refresh_kline。"""
        r = self.call("get_trading_dates", market=market,
                      start_time=start_time, end_time=end_time)
        dates = r.get("Date") or r.get("Value") or []
        if not dates:  # 本地无指数K线, 按LOCAL_NOTES先刷新再取一次
            self.refresh_kline(["999999.SH"], "1d")
            r = self.call("get_trading_dates", market=market,
                          start_time=start_time, end_time=end_time)
            dates = r.get("Date") or r.get("Value") or []
        return dates

    def refresh_kline(self, stock_list, period: str = "1d") -> dict:
        """刷新K线缓存(注意: 只喂 get_market_data, 喂不到公式引擎)。"""
        return self.call("refresh_kline", stock_list=stock_list, period=period)

    def open_in_client(self, market_code: str) -> dict:
        """让客户端打开某只证券页面(会触发该股历史数据下载)。
        market_code 形如 '1#600000'(0#深 1#沪 2#京)。"""
        return self.call("exec_to_tdx", url=f"http://www.treeid/breed_{market_code}")
