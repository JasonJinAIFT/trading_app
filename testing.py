# import sqlite3
# from db_crud import connect_to_db,fetch_from_table,insert_into_table
# from broker_api.futu_cli import initialize_openD,get_cur_kline,get_historical_kline
# import pandas as pd

# if __name__ == "__main__":
#     conn = connect_to_db()
#     cursor = conn.cursor()

#     query = f"""
#     SELECT *
#     FROM stock_price_intraday_1min
#     WHERE stock_id = 1
#     AND DATE(time) = DATE((SELECT MAX(time) FROM stock_price_intraday_1min))
#     """

#     cursor.execute(query)
#     res = cursor.fetchall()
#     df = pd.DataFrame(res,columns=['stock_id','time','open','high','low','close','volume'])
#     # print(df)

#     opening_start = df['time'].str.endswith('09:30:00')
#     opening_end = df['time'].str.endswith('09:45:00')

#     print(df[opening_start].index[0])
