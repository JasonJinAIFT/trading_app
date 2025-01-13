from futu import *
import pandas as pd
import subprocess
import broker_api.futu_api_config as futu_api_config
from .utils import market_mapping, exchange_mapping

"""
EXAMPLE: 

print(quote_ctx.get_market_snapshot('HK.00700'))  # 获取港股 HK.00700 的快照数据
quote_ctx.close() # 关闭对象，防止连接条数用尽
trd_ctx = OpenSecTradeContext(host='127.0.0.1', port=11111)  # 创建交易对象
print(trd_ctx.place_order(price=500.0, qty=100, code="HK.00700", trd_side=TrdSide.BUY, trd_env=TrdEnv.SIMULATE))  # 模拟交易，下单（如果是真实环境交易，在此之前需要先解锁交易密码
"""

openD_connected_bool = False

def initialize_openD():
    # 运行futu api需要的openD
    global openD_connected_bool
    if not openD_connected_bool:
        args = [f"-login_account={futu_api_config.account}",
                f"-login_pwd={futu_api_config.password}"]
        command = [futu_api_config.executable_path] + args

        try:
            result = subprocess.run(command, check=True)
            openD_connected_bool = True
        except Exception as e:
            err_message = f"Start openD failed, error is {e}"
            print(err_message)


def get_watch_list_sec(group_name="全部"):
    quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)  # 创建行情对象
    ret,data = quote_ctx.get_user_security(group_name)
    if ret == RET_OK:
        # print(data)
        res = {"status":200,"data":data,"message":"success"}

    else:
        res = {"status":500,"data":pd.DataFrame(),"message":data}

    quote_ctx.close()  # 关闭对象，防止连接条数用尽
    return res


def get_cur_kline(sec_code_list, num=1, ktype=KLType.K_DAY, autype=AuType.QFQ):
    """
    get most recent K-line, default is to get 1 daily bar
    :returns dict {sec_code: pd.DataFrame}
    """

    # restriction: don't have permission to get US market data yet
    sec_code_list = [sec_code for sec_code in sec_code_list if not sec_code.startswith("US")]
    sec_code_list = ['HK.00700']
    print(sec_code_list)

    quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)

    price_dict = {}
    ret_sub, err_message = quote_ctx.subscribe(sec_code_list, [SubType.K_DAY], subscribe_push=False)
    # 先订阅 K 线类型。订阅成功后 OpenD 将持续收到服务器的推送，False 代表暂时不需要推送给脚本
    if ret_sub == RET_OK:  # 订阅成功
        for sec_code in sec_code_list:
            ret, data = quote_ctx.get_cur_kline(sec_code, num, ktype, autype)  # 获取sec_code最近num个 K 线数据
            if ret == RET_OK:
                price_dict[sec_code] = data
            else:
                print(f"failed to get price data for {sec_code}")
                price_dict[sec_code] = pd.DataFrame()

        res = {"status":200,"data":price_dict,"message":"success"}
    else:
        res = {"status":500,"data":{},"message":data}
    quote_ctx.close()  # 关闭当条连接，OpenD 会在1分钟后自动取消相应股票相应类型的订阅
    
    return res


def get_historical_kline(sec_code, start, end, max_count=None):

    quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
    df = pd.DataFrame()
    ret, data, page_req_key = quote_ctx.request_history_kline(sec_code, start=start, end=end, max_count=max_count)  # 每页5个，请求第一页
    if ret == RET_OK:
        df = pd.concat([df,data],axis=0,ignore_index=True)
    else:
        res = {"status":500,"data":df,"message":data}
        quote_ctx.close()
        return res
    
    while page_req_key != None:  # 请求后面的所有结果
        print('*************************************')
        ret, data, page_req_key = quote_ctx.request_history_kline(sec_code, start=start, end=end, max_count=max_count, page_req_key=page_req_key) # 请求翻页后的数据
        if ret == RET_OK:
            df = pd.concat([df,data],axis=0,ignore_index=True)
        else:
            res = {"status":500,"data":df,"message":data}
            quote_ctx.close()
            return res

    print('All pages are finished!')
    quote_ctx.close() # 结束后记得关闭当条连接，防止连接条数用尽
    res = {"status":200,"data":df,"message":"success"}

    return res


def get_stock_basic_info(market:str, stock_type=SecurityType.STOCK, code_list:list=None):

    market_type = market_mapping[market]

    quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
    ret, data = quote_ctx.get_stock_basicinfo(market_type, stock_type, code_list)
    if ret == RET_OK:
        data["exchange_type"] = data["exchange_type"].map(exchange_mapping)
        res = {"status":200,"data":data,"message":"success"}
    else:
        res = {"status":500,"data":pd.DataFrame(),"message":data}
    quote_ctx.close()
    return res


if __name__ == "__main__":
    initialize_openD()