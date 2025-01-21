import sqlite3
from db_crud import connect_to_db,fetch_from_table,insert_into_table,fetch_with_query,insert_multi_rows_into_table
from broker_api.futu_cli import initialize_openD,get_cur_kline,get_historical_kline
from broker_api.utils import get_intraday_data_from_alphaVantage
import datetime as dt
import requests
import pandas as pd
import time


def populate_prices_table():
    """
    fetch the user's watch list at broker. If new securities appear in the watch list that is not stored in DB yet, add the security information.
    The script is supposed to run routinely with scheduled task. Otherwise mannually run it for up-to-date security info.
    """

    conn = connect_to_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # get the security list from database
    resp = fetch_from_table(conn,['id','sec_code','sec_name','exchange'],"stock")
    sec_list = resp["data"]

    # get price data from current date
    # resp = get_cur_kline(sec_codes)

    # get price data from last update date to current date
    latest_date = fetch_with_query(conn,"SELECT max(date) from stock_price")["data"][0][0]
    start_date = dt.datetime.strptime(latest_date,"%Y-%m-%d %H:%M:%S") + dt.timedelta(days=1)
    start_date = start_date.strftime("%Y-%m-%d")

    # start_date = (dt.date.today() - dt.timedelta(days=30)).strftime("%Y-%m-%d")
    end_date = dt.date.today().strftime("%Y-%m-%d")
    print(f"updating price data from {start_date} to {end_date}")

    for row in sec_list:
        stock_id, sec_code, sec_name, exchange = row['id'],row['sec_code'],row['sec_name'],row['exchange']
        # if exchange in ["NASDAQ","NYSE","CBOE","OSE"]:
        if exchange != "HKEX":
            continue

        resp = get_historical_kline(sec_code,start=start_date,end=end_date)
        if resp["status"] != 200:
            print(f"error occured in requesting futu api for {sec_code} {sec_name}, error is: {resp['message']}")
            return

        print("fetched price data from broker successfully")

        # add securities into database
        df = resp["data"]
        for i,row in df.iterrows():
            field_val_pairs = {
                "stock_id": stock_id,
                "sec_code": row["code"],
                "sec_name": row["name"],
                "date": row["time_key"],
                "open": row["open"],
                "high": row['high'], 
                "low": row['low'], 
                "close": row['close'], 
                "volume": row['volume'], 
                "turnover": row['turnover']
            }
            insert_into_table(conn,field_val_pairs,"stock_price")

    conn.commit()


def populate_intraday_prices_table_single_stock(conn, sec, interval:str):
    """
    针对某一特定ticker获取特定粒度的价格数据
    :param conn: connection object
    :param sec: Sqlite.Row object, contains id, sec_code, sec_name
    :param interval: str, format is like '1min','15min' etc.

    :return df: pd.DataFrame
    """
    # sqlite里存的股票代码格式和alpha vantage api不一样，需要做一些转换，如 US.PDD -> PDD
    symbol = sec["sec_code"].split(".")[1]
    data = get_intraday_data_from_alphaVantage(symbol,interval=interval)
    if not data:
        print("get intraday data failed")
        return

    for key,_ in data.items():
        print(key)

    # 将数据转换成dataframe，api返回的数据格式如下{"Meta Data":dict, "Time Series (*min)":dict}，需要transpose
    df_data = data[f"Time Series ({interval})"]
    df = pd.DataFrame(df_data).T
    df.columns = ["open","high","low","close","volume"]
    print(df.head())

    df["stock_id"] = sec["id"]
    df.reset_index(inplace=True,names="time")

    resp = insert_multi_rows_into_table(conn,f"stock_price_intraday_{interval}",list(df.columns),df)
    if not resp["status"] == 200:
        print(resp["message"])
        return
    
    return df


def populate_intraday_prices_table(interval:str):
    """
    将数据存入stock_price_intraday_{interval}表

    1. 从stock表中获取所有股票代码
    2. 从所有股票代码中筛选出美股代码，记录下sec_code和sec_name
    3. 从alpha vantage api获取过去一个月的分钟级别数据
    4. 将数据存入表

    :param interval: str, format is like '1min','15min' etc.
    """
    conn = connect_to_db()
    conn.row_factory = sqlite3.Row
    fetch_res = fetch_with_query(conn,"SELECT id,sec_code,sec_name from stock")
    if not fetch_res["status"] == 200:
        print(fetch_res["message"])
        return
    
    sec_list = fetch_res["data"]
    for sec in sec_list:
        if not sec["sec_code"].startswith("US"):
            continue

        print(sec["sec_code"],sec["sec_name"])
        populate_intraday_prices_table_single_stock(conn,sec,interval)

        print("="*50)
        time.sleep(15)



if __name__ == "__main__":
    interval = "1min"
    populate_intraday_prices_table(interval)
    # data = get_intraday_data_from_alphaVantage("PDD",interval=interval)
    # for key,val in data.items():
    #     print(key)