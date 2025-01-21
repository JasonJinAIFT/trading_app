import pandas as pd
import sqlite3
import sys
import os
import datetime as dt

# curr_dir = os.path.dirname(__file__)
# project_root = os.path.dirname(curr_dir)
# sys.path.append(project_root)

from ..broker_api import utils
import datetime as dt
from ..database import db_crud,populate_prices_table
# from populate_prices_table import populate_intraday_prices_table_single_stock

from strategies.portfolio_manager import PortfolioManager,Order

def get_stock_intraday_data(conn, sec, interval):
    """
    根据sec_code获取股票的当日分钟线数据
    1. 根据stock_id从stock_price_intraday_15min表中获取当日分钟线数据
    2. 如果当日数据不存在，从alpha vantage api获取，然后存入stock_price_intraday_{interval}表

    :param conn: sqlite3 connection object
    :param sec: sqlite3 row object, contains stock_id, sec_code, sec_name

    :returns: pandas dataframe, contains stock_id, time, open, high, low, close, volume
    """

    # get the last available date
    # curr_date = dt.date.today() - dt.timedelta(days=1)
    # while curr_date.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
    #     curr_date -= dt.timedelta(days=1)
    # curr_date = curr_date.strftime("%Y-%m-%d")

    # query = f"""
    # SELECT * from stock_price_intraday_{interval}
    # WHERE stock_id = {sec['id']} and time like '{curr_date}%'
    # """

    query = f"""
    SELECT *
    FROM stock_price_intraday_1min
    WHERE stock_id = {sec['id']}
    AND DATE(time) = DATE((SELECT MAX(time) FROM stock_price_intraday_{interval}));
    """

    # 尝试从sqlite中获取当日分钟线数据
    fetch_res = db_crud.fetch_with_query(conn,query)
    if not fetch_res['status'] == 200:
        print(fetch_res['message'])
        return
    
    intraday_data = fetch_res['data']
    intraday_data = pd.DataFrame(intraday_data,columns=["stock_id","time","open","high","low","close","volume"])

    # 如果sqlite table中没有当日分钟线数据，从alpha vantage获取
    # if len(intraday_data) == 0:
    #     print(f"intraday data for {sec['sec_code']} {sec['sec_name']} at {curr_date} not found in sqlite, fetching from alpha vantage")
    #     df = populate_intraday_prices_table_single_stock(conn,sec,interval)
    #     if df is None:
    #         print("failed to get intraday data from alpha vantage")
    #         return
    # else:
    #     print(f"intraday data for {sec['sec_code']} {sec['sec_name']} at {curr_date} found in sqlite")


    return intraday_data


def main():
    conn = db_crud.connect_to_db()
    conn.row_factory = sqlite3.Row

    # 拿到opening_range_breakout的strategy_id
    query = """
    SELECT id from strategy where name = 'opening_range_breakout'
    """

    fetch_res = db_crud.fetch_with_query(conn,query)
    if not fetch_res['status'] == 200:
        print(fetch_res['message'])
        return
    
    strategy_id = fetch_res['data'][0]['id']
    print(strategy_id)

    # 通过strategy_id找到所有stock_strategy中associated的股票
    query = f"""
    SELECT id,sec_code,sec_name
    FROM stock join stock_strategy on stock.id = stock_strategy.stock_id
    WHERE strategy_id = {strategy_id}
    """

    fetch_res = db_crud.fetch_with_query(conn,query)
    if not fetch_res['status'] == 200:
        print(fetch_res['message'])
        return
    
    stocks_in_strategy = fetch_res['data']
    portfolio = PortfolioManager()

    for stock in stocks_in_strategy:
        print(stock['id'],stock['sec_code'],stock['sec_name'])
        # get the stock intraday price data
        intraday_data = get_stock_intraday_data(conn,stock,interval='1min')

        # convert datatype into float
        float_columns = ['open','high','low','close']
        int_columns = ['volume']
        intraday_data[float_columns] = intraday_data[float_columns].astype(float)
        intraday_data[int_columns] = intraday_data[int_columns].astype(int)
        # print(intraday_data)

        # 找到开盘后的前15分钟的rows
        opening_start = intraday_data['time'].str.endswith('09:30:00')
        opening_end = intraday_data['time'].str.endswith('09:45:00')
        opening_start_idx = intraday_data[opening_start].index[0]
        opening_end_idx = intraday_data[opening_end].index[0]
        
        opening_range_bars = intraday_data.loc[opening_start_idx:opening_end_idx]
        print(opening_range_bars)

        # ======================= 计算opening range =======================

        # 1. 找到lowest low和highest high
        opening_lowest_low = opening_range_bars['low'].min()
        opening_highest_high = opening_range_bars['high'].max()

        # 2. 计算opening range
        opening_range = opening_highest_high - opening_lowest_low
        print(opening_lowest_low,opening_highest_high,opening_range)

        # 3. 在开盘15分钟后的bars中，一旦价格突破opening_range_high，则开多仓
        after_opening_bars = intraday_data.loc[opening_end_idx+1:]
        
        # 遍历每个bar找到符合开仓条件的时机
        position_is_opened_bool = False
        buy_price = None
        sell_price = None
        order_size = None
        for i, bar in after_opening_bars.iterrows():
            if (not position_is_opened_bool) and bar['close'] > opening_highest_high:
                # 开多仓
                buy_price = bar['close']
                order_size = 100
                buy_order = Order(
                    ticker=stock['sec_code'],
                    order_type="limit",
                    order_direction="buy",
                    price=buy_price,
                    num_shares=order_size
                )
                place_order_message = portfolio.place_order(buy_order)
                print(place_order_message)
                position_is_opened_bool = True

            else:
                # 平仓逻辑
                if position_is_opened_bool:
                    take_profit_criteria = opening_range * 1.5 + buy_price
                    stop_loss_criteria = opening_range * -1 + buy_price

                    close_position_1 = (i == max(after_opening_bars.index))     # 收盘时间
                    close_position_2 = (bar['close'] >= take_profit_criteria or bar['close'] <= stop_loss_criteria)     # 价格达到止盈止损位置
                    if close_position_1 or close_position_2:
                        sell_price = bar['close']
                        sell_order = Order(
                            ticker=stock['sec_code'],
                            order_type="limit",
                            order_direction="sell",
                            price=sell_price,
                            num_shares=order_size
                        )
                        place_order_message = portfolio.place_order(sell_order)
                        print(place_order_message)
                        position_is_opened_bool = False


        print("="*50)
    


if __name__ == '__main__':
    main()