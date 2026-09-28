# 通达信量化官方接口文档 · 本地镜像

> 来源: https://help.tdx.com.cn/quant/ (官方文档站) | 共 131 页接口文档 | 抓取脚本: scripts/crawl_tdx_docs.py (可 --force 重抓)

## 三套 API 家族怎么选

| 家族 | 调用方式 | 适用场景 | 依赖 |
|---|---|---|---|
| **tqcenter / tq** | `from tqcenter import tq` → `tq.initialize(__file__)` → `tq.xxx()` | 本地客户端策略、行情订阅、实盘交易、公式选股 | 需运行支持 TQ 的通达信客户端;全部函数亦可走 HTTP JSON-RPC(127.0.0.1:17709, method=函数名, 免py文件) |
| **tqs / TdxAiData** | `pip install tdxaidata` → `from tdxaidata import tqs` → `tqs.xxx()` | 免客户端取数: 行情/财务/专业数据/分笔/集合竞价, 跨平台 | TdxAiData.dll + Token 配置;无交易、无公式 |
| **Lambda / pylambda** | `init(context)` / `handle_bar(context, bar)` 回调 + 裸函数 `get_price`/`order`/... | 云回测/信号平台策略 | 通达信客户端内提交运行 |

关键关系: 官方文档中带星号(*)的数据接口 tqs 与 tq 签名通用; Lambda 是完全独立的第三套 API(同名函数如 get_tick_data 在两族中都存在但参数不同, 查文档时注意目录)。

## 文档目录

### 01-tqcenter-通用函数/ (14页)

- [下载特定数据文件download_file](01-tqcenter-通用函数/download_file.md)
- [调用客户端功能](01-tqcenter-通用函数/exec_to_tdx.md)
- [检索证券信息get_match_stkinfo](01-tqcenter-通用函数/get_match_stkinfo.md)
- [获得订阅列表get_subscribe_hq_stock_list](01-tqcenter-通用函数/get_subscribe_hq_stock_list.md)
- [初始化initialize](01-tqcenter-通用函数/initialize.md)
- [导出多组数据到通达信客户端 print_to_tdx](01-tqcenter-通用函数/print_to_tdx.md)
- [刷新行情缓存(最新snapshot和K线数据)refresh_cache](01-tqcenter-通用函数/refresh_cache.md)
- [刷新历史K线缓存refresh_kline](01-tqcenter-通用函数/refresh_kline.md)
- [发送回测数据send_bt_data](01-tqcenter-通用函数/send_bt_data.md)
- [发送文件到客户端send_file](01-tqcenter-通用函数/send_file.md)
- [发送消息到通达信客户端send_message](01-tqcenter-通用函数/send_message.md)
- [发送预警信号send_warn](01-tqcenter-通用函数/send_warn.md)
- [订阅行情subscribe_hq](01-tqcenter-通用函数/subscribe_hq.md)
- [取消订阅更新unsubscribe_hq](01-tqcenter-通用函数/unsubscribe_hq.md)


### 02-tqcenter-行情/ (16页)

- [获取分红送配数据get_divid_factors](02-tqcenter-行情/get_divid_factors.md)
- [获取日线统计数据get_exday_data](02-tqcenter-行情/get_exday_data.md)
- [获取每天的股本数据get_gb_info](02-tqcenter-行情/get_gb_info.md)
- [根据时间段获取股本数据get_gb_info_by_date](02-tqcenter-行情/get_gb_info_by_date.md)
- [获取新股申购信息get_ipo_info](02-tqcenter-行情/get_ipo_info.md)
- [获取K线行情get_market_data](02-tqcenter-行情/get_market_data.md)
- [获取快照数据get_market_snapshot](02-tqcenter-行情/get_market_snapshot.md)
- [快照批量get_market_snapshot_batch](02-tqcenter-行情/get_market_snapshot_batch.md)
- [获取股票更多信息get_more_info](02-tqcenter-行情/get_more_info.md)
- [扩展信息批量get_more_info_batch](02-tqcenter-行情/get_more_info_batch.md)
- [批量获取价量get_pricevol](02-tqcenter-行情/get_pricevol.md)
- [获取股票所属板块](02-tqcenter-行情/get_relation.md)
- [获取证券基本信息get_stock_info](02-tqcenter-行情/get_stock_info.md)
- [基础信息批量get_stock_info_batch](02-tqcenter-行情/get_stock_info_batch.md)
- [获取交易日列表get_trading_dates](02-tqcenter-行情/get_trading_dates.md)
- [获取股票涨跌停数据get_zdt_data](02-tqcenter-行情/get_zdt_data.md)


### 03-tqcenter-财务/ (9页)

- [获取板块交易数据get_bkjy_value](03-tqcenter-财务/get_bkjy_value.md)
- [获取指定日期板块交易数据get_bkjy_value_by_date](03-tqcenter-财务/get_bkjy_value_by_date.md)
- [获取专业财务数据get_financial_data](03-tqcenter-财务/get_financial_data.md)
- [获取指定日期专业财务数据get_financial_data_by_date](03-tqcenter-财务/get_financial_data_by_date.md)
- [获取股票的单个财务数据get_gp_one_data](03-tqcenter-财务/get_gp_one_data.md)
- [获取股票交易数据get_gpjy_value](03-tqcenter-财务/get_gpjy_value.md)
- [获取指定日期股票交易数据get_gpjy_value_by_date](03-tqcenter-财务/get_gpjy_value_by_date.md)
- [获取市场交易数据](03-tqcenter-财务/get_scjy_value.md)
- [获取指定日期市场交易数据get_scjy_value_by_date](03-tqcenter-财务/get_scjy_value_by_date.md)


### 04-tqcenter-板块与自选股/ (9页)

- [清空自定义板块成份股](04-tqcenter-板块与自选股/clear_sector.md)
- [创建自定义板块](04-tqcenter-板块与自选股/create_sector.md)
- [删除自定义板块](04-tqcenter-板块与自选股/delete_sector.md)
- [获取A股板块代码列表get_sector_list](04-tqcenter-板块与自选股/get_sector_list.md)
- [获取系统分类成份股get_stock_list](04-tqcenter-板块与自选股/get_stock_list.md)
- [获取板块成份股get_stock_list_in_sector](04-tqcenter-板块与自选股/get_stock_list_in_sector.md)
- [获取自定义板块列表get_user_sector](04-tqcenter-板块与自选股/get_user_sector.md)
- [重命名自定义板块](04-tqcenter-板块与自选股/rename_sector.md)
- [添加自定义板块成份股](04-tqcenter-板块与自选股/send_user_block.md)


### 05-tqcenter-ETF可转债期货/ (3页)

- [获取可转债信息get_kzz_info](05-tqcenter-ETF可转债期货/get_kzz_info.md)
- [可转债信息批量get_kzz_info_batch](05-tqcenter-ETF可转债期货/get_kzz_info_batch.md)
- [获取跟踪指数的ETF信息get_trackzs_etf_info](05-tqcenter-ETF可转债期货/get_trackzs_etf_info.md)


### 06-tqcenter-公式/ (8页)

- [格式化K线数据formula_format_data](06-tqcenter-公式/formula_format_data.md)
- [获取指定种类的公式列表formula_get_all](06-tqcenter-公式/formula_get_all.md)
- [获取公式中的设置数据formula_get_data](06-tqcenter-公式/formula_get_data.md)
- [获取指定公式信息formula_get_info](06-tqcenter-公式/formula_get_info.md)
- [批量调用通达信公式formula_process_mul_xg/zb/exp](06-tqcenter-公式/formula_process_mul_xg_zb.md)
- [向通达信公式设置数据formula_set_data](06-tqcenter-公式/formula_set_data.md)
- [向通达信公式设置数据信息formula_set_data_info](06-tqcenter-公式/formula_set_data_info.md)
- [调用通达信公式进行计算formula_zb/xg/exp](06-tqcenter-公式/formula_zb_xg_exp.md)


### 07-tqcenter-交易/ (7页)

- [撤单](07-tqcenter-交易/cancel_order_stock.md)
- [交易执行函数](07-tqcenter-交易/order_stock.md)
- [查询历史成交query_history_trade](07-tqcenter-交易/query_history_trade.md)
- [查询账户资产信息](07-tqcenter-交易/query_stock_asset.md)
- [查询账户委托信息](07-tqcenter-交易/query_stock_orders.md)
- [查询账户持仓信息](07-tqcenter-交易/query_stock_positions.md)
- [获取资金账户句柄](07-tqcenter-交易/stock_account.md)


### 08-HTTP调用/ (1页)

- [HTTP方式调用](08-HTTP调用/http_json_rpc.md)


### 09-tqs-TdxAiData/ (8页)

- [TdxAiData后台接口总览](09-tqs-TdxAiData/tdxaidata_overview.md)
- [集合竞价get_call_auction](09-tqs-TdxAiData/tqs_get_call_auction.md)
- [集合竞价批量get_call_auction_batch](09-tqs-TdxAiData/tqs_get_call_auction_batch.md)
- [分钟数据get_minute_data](09-tqs-TdxAiData/tqs_get_minute_data.md)
- [分笔数据get_tick_data](09-tqs-TdxAiData/tqs_get_tick_data.md)
- [中证高管持股股票列表get_zzgz_stocklist](09-tqs-TdxAiData/tqs_get_zzgz_stocklist.md)
- [订阅行情subscribe](09-tqs-TdxAiData/tqs_subscribe.md)
- [取消订阅unsubscribe](09-tqs-TdxAiData/tqs_unsubscribe.md)


### 10-lambda-pylambda/ (55页)

#### 01-生命周期

- [盘后回调after_trading](10-lambda-pylambda/01-生命周期/after_trading.md)
- [盘前回调before_trading](10-lambda-pylambda/01-生命周期/before_trading.md)
- [K线回调handle_bar](10-lambda-pylambda/01-生命周期/handle_bar.md)
- [初始化init](10-lambda-pylambda/01-生命周期/init.md)
- [订单回调on_order](10-lambda-pylambda/01-生命周期/on_order.md)
- [策略结束on_strategy_end](10-lambda-pylambda/01-生命周期/on_strategy_end.md)
- [成交回调on_trade](10-lambda-pylambda/01-生命周期/on_trade.md)

#### 02-全局运行对象

- [Bar对象](10-lambda-pylambda/02-全局运行对象/bar_object.md)
- [context.params](10-lambda-pylambda/02-全局运行对象/context_params.md)
- [context.portfolio](10-lambda-pylambda/02-全局运行对象/context_portfolio.md)
- [context.run_info](10-lambda-pylambda/02-全局运行对象/context_run_info.md)
- [context.stock](10-lambda-pylambda/02-全局运行对象/context_stock.md)
- [Order对象](10-lambda-pylambda/02-全局运行对象/order_object.md)
- [positions对象](10-lambda-pylambda/02-全局运行对象/position.md)
- [Trade对象](10-lambda-pylambda/02-全局运行对象/trade_object.md)

#### 03-回测设置

- [性能分析enable_profile](10-lambda-pylambda/03-回测设置/enable_profile.md)
- [其他设置函数](10-lambda-pylambda/03-回测设置/other_settings.md)
- [设置基准set_benchmark](10-lambda-pylambda/03-回测设置/set_benchmark.md)
- [设置佣金set_commission](10-lambda-pylambda/03-回测设置/set_commission.md)
- [设置执行方式set_execution](10-lambda-pylambda/03-回测设置/set_execution.md)
- [设置选项set_option](10-lambda-pylambda/03-回测设置/set_option.md)
- [设置滑点set_slippage](10-lambda-pylambda/03-回测设置/set_slippage.md)

#### 04-定时任务

- [每日定时run_daily](10-lambda-pylambda/04-定时任务/run_daily.md)
- [按周月定时](10-lambda-pylambda/04-定时任务/run_weekly_monthly.md)

#### 05-特有行情

- [分钟数据get_minute_data](10-lambda-pylambda/05-特有行情/lambda_get_minute_data.md)
- [分笔数据get_tick_data](10-lambda-pylambda/05-特有行情/lambda_get_tick_data.md)
- [中证高管持股列表get_zzgz_stocklist](10-lambda-pylambda/05-特有行情/lambda_get_zzgz_stocklist.md)

#### 06-数据函数

- [属性历史attribute_history](10-lambda-pylambda/06-数据函数/attribute_history.md)
- [批量因子calc_factor_batch](10-lambda-pylambda/06-数据函数/calc_factor_batch.md)
- [全部证券get_all_securities](10-lambda-pylambda/06-数据函数/get_all_securities.md)
- [批量K线get_bars_batch](10-lambda-pylambda/06-数据函数/get_bars_batch.md)
- [当前数据get_current](10-lambda-pylambda/06-数据函数/get_current.md)
- [因子缓存信息get_factor_cache_info](10-lambda-pylambda/06-数据函数/get_factor_cache_info.md)
- [历史价格get_price](10-lambda-pylambda/06-数据函数/get_price.md)
- [证券信息get_security_info](10-lambda-pylambda/06-数据函数/get_security_info.md)
- [历史数据history](10-lambda-pylambda/06-数据函数/history.md)
- [获取指数行业和概念成份](10-lambda-pylambda/06-数据函数/index_industry_concept.md)
- [原生指标MA/MACD](10-lambda-pylambda/06-数据函数/native_indicators_ma_macd.md)
- [时间函数](10-lambda-pylambda/06-数据函数/time_functions.md)
- [交易日历函数](10-lambda-pylambda/06-数据函数/trading_calendar.md)

#### 07-交易函数

- [提交撤单](10-lambda-pylambda/07-交易函数/cancel_order.md)
- [下单order](10-lambda-pylambda/07-交易函数/order.md)
- [比例目标市值下单](10-lambda-pylambda/07-交易函数/order_percent_target_value.md)
- [目标数量下单order_target](10-lambda-pylambda/07-交易函数/order_target.md)
- [按价值下单order_value](10-lambda-pylambda/07-交易函数/order_value.md)
- [订单和成交查询](10-lambda-pylambda/07-交易函数/query_orders_trades.md)
- [组合目标权重调仓](10-lambda-pylambda/07-交易函数/rebalance_target_weights.md)

#### 08-账户查询

- [获取资金get_cash](10-lambda-pylambda/08-账户查询/get_cash.md)
- [获取组合get_portfolio](10-lambda-pylambda/08-账户查询/get_portfolio.md)
- [获取单持仓get_position](10-lambda-pylambda/08-账户查询/get_position.md)
- [获取持仓列表get_positions](10-lambda-pylambda/08-账户查询/get_positions.md)

#### 09-其他

- [代码转换函数](10-lambda-pylambda/09-其他/code_convert.md)
- [完整示例](10-lambda-pylambda/09-其他/full_example.md)
- [常见问题](10-lambda-pylambda/09-其他/lambda_faq.md)
- [记录和日志](10-lambda-pylambda/09-其他/logging_and_helpers.md)


### 11-常量枚举/ (1页)

- [常量枚举](11-常量枚举/constants.md)

