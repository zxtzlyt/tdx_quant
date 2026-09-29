# -*- coding: utf-8 -*-
"""通达信 TQ 本地 HTTP 直连脚本(不依赖 tqcenter, 纯标准库)。

直接向本机 TQ 服务发 JSON-RPC 请求: POST http://127.0.0.1:17709/
请求体 {"id":1, "method": TdxQuant接口名, "params": 接口参数}。
前置: 已启动并登录支持 TQ 的通达信客户端。

用法:
  无参数运行 = 自检演示(连通性 + 名称解析 + K线 + 快照):
      python examples/http_call.py
  调任意接口(method + params JSON 字符串, params 可省略):
      python examples/http_call.py get_match_stkinfo "{\"key_word\":\"茅台\"}"
      python examples/http_call.py get_market_data "{\"stock_list\":[\"600000.SH\"],\"count\":5,\"period\":\"1d\"}"
      python examples/http_call.py get_user_sector
  换服务地址:
      python examples/http_call.py --url http://127.0.0.1:17709/ get_ipo_info "{\"ipo_type\":2}"
"""
import json
import sys
import urllib.error
import urllib.request

DEFAULT_URL = "http://127.0.0.1:17709/"


class TqHttpError(RuntimeError):
    """TQ 服务返回错误(JSON-RPC error / ErrorId != 0 / HTTP 层失败)。"""


def call(method, params=None, base_url=DEFAULT_URL, timeout=60):
    """发一次 JSON-RPC 请求, 返回服务端 result 字典(原样, 不做分页合并)。

    注意 params 必须始终发送(空参也传 {}): 实测网关对缺 "params" 键的
    请求返回 -32602 "MCP参数params必须为对象"。
    """
    body = {"id": 1, "method": method, "params": params if params is not None else {}}
    req = urllib.request.Request(
        base_url,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise TqHttpError(
            f"TQ 服务不可达({base_url}): {e}\n"
            "请先启动并登录支持 TQ 的通达信客户端, 再重试。"
        ) from e
    if isinstance(payload.get("error"), dict):
        raise TqHttpError(f"{method} JSON-RPC 错误: {payload['error']}")
    result = payload.get("result", {})
    if isinstance(result, dict) and result.get("ErrorId") not in (None, "0"):
        raise TqHttpError(f"{method} 失败: {result.get('Error') or result}")
    return result


def paged(method, params=None, base_url=DEFAULT_URL, timeout=60):
    """call() + 大结果自动续取合并, 返回完整 result。

    覆盖三种分页协议(与 tdx_local.TqClient.paged 同规则):
    - KlinePaged(get_market_data): has_more + next_stock_page_index 续取, 拼接各股字段序列
    - ProDataPaged(专业数据): stock_page_index 0..stock_total_pages-1, 合并 Value
    - TPythPaged(通用): page_token / next_page_offset 游标续取
    """
    result = call(method, params, base_url, timeout)
    if not isinstance(result, dict):
        return result
    params = params if params is not None else {}

    if result.get("KlinePaged") and result.get("has_more"):
        pages = [result]
        idx = result.get("next_stock_page_index", 1)
        while pages[-1].get("has_more"):
            nxt = call(method, {**params, "stock_page_index": idx}, base_url, timeout)
            pages.append(nxt)
            if not nxt.get("has_more"):
                break
            idx = nxt.get("next_stock_page_index", idx + 1)
        value = {}
        for p in pages:
            for code, fields in (p.get("Value") or {}).items():
                dst = value.setdefault(code, {})
                for key, seq in fields.items():
                    if isinstance(seq, list) and isinstance(dst.get(key), list):
                        dst[key] = dst[key] + seq
                    else:
                        dst[key] = seq
        result = {**pages[-1], "Value": value, "has_more": False}
    elif result.get("ProDataPaged") and result.get("stock_total_pages", 1) > 1:
        value = dict(result.get("Value") or {})
        for idx in range(1, result["stock_total_pages"]):
            nxt = call(method, {**params, "stock_page_index": idx}, base_url, timeout)
            value.update(nxt.get("Value") or {})
        result = {**result, "Value": value}
    elif result.get("page_token") or result.get("TPythPaged"):
        cur = result
        while cur.get("has_more"):
            extra = {}
            if cur.get("page_token") is not None:
                extra["_tpyth_page_token"] = cur["page_token"]
            if cur.get("next_page_offset") is not None:
                extra["_tpyth_page_offset"] = str(cur["next_page_offset"])
            cur = call(method, {**params, **extra}, base_url, timeout)
            for key, seq in (cur.get("Value") or {}).items():
                dst = result.setdefault("Value", {})
                if isinstance(seq, list) and isinstance(dst.get(key), list):
                    dst[key] = dst[key] + seq
                else:
                    dst[key] = seq
        result = {**result, "has_more": False}
    return result


def demo(base_url):
    print(f"TQ 服务: {base_url}")

    r = call("get_match_stkinfo", {"key_word": "茅台"}, base_url)
    rows = r.get("Value") or []
    print(f"\n[1] 名称解析 get_match_stkinfo(茅台) -> {len(rows)} 条")
    for row in rows[:3]:
        print(f"    {row.get('Code')}  {row.get('Name')}")

    code = rows[0]["Code"] if rows else "600519.SH"
    r = paged("get_market_data",
              {"stock_list": [code], "count": 3, "period": "1d",
               "dividend_type": "front"}, base_url)
    val = (r.get("Value") or {}).get(code, {})
    dates, closes = val.get("Date") or [], val.get("Close") or []
    print(f"\n[2] 日K get_market_data({code}, 最近3根, 前复权)")
    for d, c in zip(dates[-3:], closes[-3:]):
        print(f"    {d}  收盘 {float(c):.2f}")

    r = call("get_market_snapshot", {"stock_code": code, "field_list": []}, base_url)
    meta = {"ErrorId", "Error", "Msg", "run_id", "Value", "KlinePaged"}
    snap = {k: v for k, v in r.items() if k not in meta}
    print(f"\n[3] 快照 get_market_snapshot({code}) 现价={snap.get('Now')}  "
          f"涨跌={snap.get('TickDiff')}  总手={snap.get('Volume')}")


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    base_url = DEFAULT_URL
    args = argv[:]
    if args and args[0] == "--url":
        if len(args) < 2:
            print("--url 需要一个地址参数", file=sys.stderr)
            return 2
        base_url, args = args[1], args[2:]

    if not args:
        demo(base_url)
        return 0

    method = args[0]
    params = {}
    if len(args) > 1:
        try:
            params = json.loads(args[1])
        except json.JSONDecodeError as e:
            print(f"params 不是合法 JSON: {e}\n示例: {method} '{{\"key_word\":\"茅台\"}}'",
                  file=sys.stderr)
            return 2
    print(json.dumps(paged(method, params, base_url), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except TqHttpError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
