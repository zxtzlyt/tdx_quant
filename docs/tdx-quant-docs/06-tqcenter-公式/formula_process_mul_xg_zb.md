<!-- source: https://help.tdx.com.cn/quant/docs/markdown/mindoc-1h3hrvkp4sc0g/mindoc-1h4ad5lisvdfg.html | 章节: 06-tqcenter-公式 -->

#  批量调用通达信公式formula_process_mul_xg/zb/exp

###  批量调用通达信公式无需使用formula_set_data和formula_set_data_info提前设置，formula_set_data和formula_set_data_info的设置也对批量调用不生效

```python
#批量调用选股公式
def formula_process_mul_xg(formula_name: str = '',
                           formula_arg: str = '',
                           return_count: int = 1,
                           return_date:bool = False,
                           stock_list: List[str] = [],
                           stock_period: str = '1d',
                           start_time: str = '',
                           end_time: str = '',
                           count: int = 0,
                           dividend_type: int = 0):
#批量调用指标公式
def formula_process_mul_zb(formula_name: str = '',
                            formula_arg: str = '',
                            xsflag: int = -1,
                            return_count: int = 1,
                            return_date:bool = False,
                            stock_list: List[str] = [],
                            stock_period: str = '1d',
                            start_time: str = '',
                            end_time: str = '',
                            count: int = 0,
                            dividend_type: int = 0):
```

###  输入参数

| 参数 | 是否必选 | 参数类型 | 参数说明 |
| --- | --- | --- | --- |
| formula_name | Y | str | 公式名称 |
| formula_arg | Y | str | 公式参数 |
| xsflag | Y | int | 数据精度 |
| retrun_count | Y | int | 设置每个返回值的返回数 |
| formula_arg | Y | bool | 设置是否返回日期 |
| stock_list | Y | List[str] | 股票代码列表 |
| stock_period | Y | str | K线周期 |
| start_time | Y | str | 起始时间 |
| end_time | Y | str | 结束时间 |
| count | Y | int | 截取K线数量 |
| dividend_type | Y | int | 复权类型 |

  * 需要先在下载对应的盘后数据
  * dividend_type的取值为：0不复权 1前复权 2后复权
  * count为截取最新交易日开始往前的n条K线，当count参数不为0时，start_time和end_time失效
  * count=-1时，获取所有数据，count=-2时，使用无序列数据
  * count=-1时如果 return_count=0，返回结果的日期区间受start_time和end_time限制
  * 当count为0时，start_time和end_time生效，指定K线为对应时间段内
  * count最大值为24000，count为-1时为获取对应股票全部K线
  * 正常每个返回值的数据个数应该与count相同，但是return_count可以限制返回个数，去掉用不到的数据，以此提高能够返回的有效数据量；对于选股和多股指标排行场景，一般只需要返回最后一个数据进行判断股票是否选中或显示最后一个指标数据，return_count为1就可以。
  * xsflag小于0时返回默认精度，最大可返回8位小数。
  * 请注意一定要完整下载对应的盘后数据（或使用refresh_kline），以及retrun_count设置正确，保证结果都能返回。
  * 得到结果与客户端不一致通常是由于设置的K线数量不足导致。

###  接口使用

```python
from tqcenter import tq

tq.initialize(__file__)

#批量调用UPN 选股公式
mul_xg_res = tq.formula_process_mul_xg(
    formula_name='UPN',
    formula_arg='3',
    return_count=3,
    return_date=True,
    stock_list=['688318.SH','600519.SH','000001.SZ'],
    stock_period='1d',
    count=5,
    dividend_type=1)
print(mul_xg_res)

#批量调用CYX 指标公式
mul_zb_res = tq.formula_process_mul_zb(
    formula_name='CYX',
    formula_arg='12',
    return_count=3,
    return_date=True,
    stock_list=['688318.SH','600519.SH','000001.SZ'],
    stock_period='1d',
    count=5,
    dividend_type=1)
print(mul_zb_res)
```

###  数据样本

```text
{'000001.SZ': {'UP3': [{'Date': '20260203', 'Value': '0'}, {'Date': '20260204', 'Value': '0'}, {'Date': '20260205', 'Value': '0'}]},
'600519.SH': {'UP3': [{'Date': '20260203', 'Value': '0'}, {'Date': '20260204', 'Value': '1'}, {'Date': '20260205', 'Value': '1'}]},
'688318.SH': {'UP3': [{'Date': '20260203', 'Value': '0'}, {'Date': '20260204', 'Value': '0'}, {'Date': '20260205', 'Value': '0'}]}, 'ErrorId': '0'}

{'000001.SZ': {'NOTEXT1': [{'Date': '20260203', 'Value': '11.06'}, {'Date': '20260204', 'Value': '11.08'}, {'Date': '20260205', 'Value': '11.11'}], 'NOTEXT2': [{'Date': '20260203', 'Value': '10.85'}, {'Date': '20260204', 'Value': '10.91'}, {'Date': '20260205', 'Value': '10.96'}], 'OUTPUT1': ['全国性银行 深圳板块 跨境支付CIPS ']},
'600519.SH': {'NOTEXT1': [{'Date': '20260203', 'Value': '1494.05'}, {'Date': '20260204', 'Value': '1529.53'}, {'Date': '20260205', 'Value': '1565.00'}], 'NOTEXT2': [{'Date': '20260203', 'Value': '1446.08'}, {'Date': '20260204', 'Value': '1480.54'}, {'Date': '20260205', 'Value': '1515.00'}], 'OUTPUT1': ['酿酒 贵州板块 通达信88 白酒概念 ']},
'688318.SH': {'NOTEXT1': [{'Date': '20260203', 'Value': '136.60'}, {'Date': '20260204', 'Value': '135.30'}, {'Date': '20260205', 'Value': '134.00'}], 'NOTEXT2': [{'Date': '20260203', 'Value': '131.74'}, {'Date': '20260204', 'Value': '131.48'}, {'Date': '20260205', 'Value': '131.22'}], 'OUTPUT1': ['软件服务 深圳板块 腾讯概念 华为鸿蒙 国产软件 互联金融 人工智能 ']}, 'ErrorId': '0'}
```
