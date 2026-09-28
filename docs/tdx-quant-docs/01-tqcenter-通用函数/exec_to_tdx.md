<!-- source: https://help.tdx.com.cn/quant/docs/markdown/ctx.stock.md/mindoc-1h85iq443j44c.html | 章节: 01-tqcenter-通用函数 -->

#  调用客户端功能

###  客户端根据入参执行指定功能

```python
def exec_to_tdx(url:str = ''):
```

###  输入参数

| 参数 | 是否必选 | 参数类型 | 参数说明 |
| --- | --- | --- | --- |
| url | Y | str | 功能调用串或网址 |

若是功能串，请以 http://www.treeid 开头

###  主要功能串

| 功能串 | 说明和示例 |
| --- | --- |
| inhttp | 内部打开 比如：http://www.treeid/inhttp://....... |
| dlghttp | 内部对话框打开 比如： http://www.treeid/dlghttp://.......&tdxmyietitle=标题&tdxmyiewidth=500&tdxmyieheight=300&noborder=0 |
| localurl | 内部打开(非对话框) 比如：http://www.treeid/localurlc:\pa\tips.html....... |
| dlglocalurl | 内部打开(对话框) 比如：http://www.treeid/dlglocalurlc:\pa\tips.mht....... |
| code_ | 进入某只股票(只传入代码) |
| breed_ | 到某个品种(可以传入市场和代码,如果不清楚市场,在代码前加-即可进行模糊处理), 比如到财富趋势 http://www.treeid/breed_1#688318 市场：0#为深市 1#为沪市 2#为京市 |
| zb_ | 指标公式 比如：http://www.treeid/zb_MACD |
| exp_ | 专家系统公式 |
| padcode_ | 进入用户定制版面，后面是版面简称 |
| ZXG | 自选股列表 |
| ETF | ETF基金 |
| HK | 显示港股 |
| QH | 显示期货 |
| MAINQH | 显示为主力期货合约 |
| SORT67 | 排行(67) |
| SetMark_ | 设置标识，市场#代码(0#为深市 1#为沪市 2#为京市),标识类型,标识简字 |

比如 http://ww.treeid/SetMark_1#600000|0|我是大牛 就会将客户端是沪市600000股票设置我是大牛的简字

###  接口使用

```python
from tqcenter import tq
tq.initialize(__file__)

exec_res1 = tq.exec_to_tdx(url='http://www.treeid/MAINQH')

exec_res2 = tq.exec_to_tdx(url='http://www.treeid/dlghttp://www.tdx.com.cn')
print(exec_res2)
```

###  数据样本

```text
{'ErrorId': '0', 'Msg': 'http://www.treeid/dlghttp://www.tdx.com.cn', 'run_id': '1'}
```
