import sqlite3
import os
import sys
import pandas as pd

def connect_to_db():
    curr_dir = os.path.dirname(__file__)
    db_path = os.path.join(curr_dir,'trading_app.db')
    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA encoding="UTF-8";')
    return conn


def fetch_from_table(conn, fields:list, table:str):
    """
    fetch rows from sqlite DB for any given table
    :param conn: the connection object returned from connect_to_db()
    :param fields: the fields that you want to select
    :param table: the name of table

    :returns: dict with 3 keys: 'status', 'data', 'message'
        {
            'status': 200,
            'data': list of tuples,
            'message': success
        }
    """
    cursor = conn.cursor()

    query = f"SELECT {','.join(fields)} FROM {table}"
    print(query)
    try:
        cursor.execute(query)
        sec_list = cursor.fetchall()
        message = "success"
        status_code = 200
    except Exception as e:
        message = f"fetch security information failed, error is {e}"
        print(message)
        sec_list = []
        status_code = 500

    return {"status":status_code, "data":sec_list, "message":message}


def fetch_with_query(conn,query:str, row_factory:bool=False):
    """
    this function will execute the query input as parameter
    :param conn: the connection object from connect_to_db()
    :param query: the actual query to execute
    
    :returns dict with 3 keys: 'status', 'data', 'message'
        {
            'status': 200,
            'data': list of tuples,
            'message': success
        }
    """
    if row_factory:
        conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    print(query)
    try:
        cursor.execute(query)
        sec_list = cursor.fetchall()
        message = "success"
        status_code = 200
    except Exception as e:
        message = f"fetch security information failed, error is {e}"
        print(message)
        sec_list = []
        status_code = 500

    return {"status":status_code, "data":sec_list, "message":message}


def insert_into_table(conn, field_value_pairs:dict, table:str):
    cursor = conn.cursor()
    field_list = list(field_value_pairs.keys())
    val_list = tuple(field_value_pairs.values())
    v = ",".join(["?"]*len(val_list))
    # val_list = ["'"+val+"'" if type(val)==str else val for val in val_list]
    
    query = f"INSERT INTO {table} ({','.join(field_list)}) VALUES ({v})"
    print(query)
    try:
        cursor.execute(query,val_list)
        message = "success"
        status_code = 200
        conn.commit()
        
    except Exception as e:
        message = f"insert into {table} table failed, error is {e}"
        print(message)
        status_code = 500

    print(message)
    return {"status":status_code, "message":message}


def insert_multi_rows_into_table(conn, table, col_names:list, df):
    """
    df 可以是pd.DataFrame，也可以是pd.DataFrame.values.tolist()
    """
    cursor = conn.cursor()
    columns = ','.join(col_names)
    placeholders = ','.join('?' * len(col_names))
    query = f"INSERT OR IGNORE INTO {table} ({columns}) VALUES ({placeholders})"

    if type(df) == pd.DataFrame:
        df = df.values.tolist()

    try:
        cursor.executemany(query, df)
        conn.commit()
        message = "success"
        status_code = 200
    except Exception as e:
        message = f"insert into {table} table failed, error is {e}"
        status_code = 500
    
    return {"status":status_code, "message":message}


def test():
    conn = connect_to_db()
    conn.row_factory = sqlite3.Row
    query = """
    SELECT * from stock_price_intraday_15min
    limit 20
    """
    res = fetch_with_query(conn,query)
    data = res['data']
    df = pd.DataFrame(data)
    print(df)



if __name__ == "__main__":
    # conn = connect_to_db()
    # cursor = conn.cursor()
    # res = fetch_from_table(conn,["123"],"abc")
    # print(res)

    test()