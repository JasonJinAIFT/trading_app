import sqlite3
from db_crud import connect_to_db,fetch_from_table,insert_into_table
from broker_api.futu_cli import initialize_openD, get_watch_list_sec, get_stock_basic_info


def populate_stock_table():
    """
    fetch the user's watch list at broker. If new securities appear in the watch list that is not stored in DB yet, add the security information.
    The script is supposed to run routinely with scheduled task. Otherwise mannually run it for up-to-date security info.
    """

    conn = connect_to_db()
    conn.row_factory = sqlite3.Row

    # get existing securities
    resp = fetch_from_table(conn,['sec_code','sec_name'],"stock")
    sec_list = resp["data"]
    print("fetched existing securities from database")

    sec_codes, sec_names = [],[]
    for row in sec_list:
        sec_codes.append(row['sec_code'])
        sec_names.append(row['sec_name'])


    # retrieve securities from broker api
    resp = get_watch_list_sec()
    if resp["status"] != 200:
        print(f"error occurred in requesting futu watch list api, error is: {resp['message']}")
        return
    
    print("fetched watch list from broker successfully")

    df1 = resp["data"]
    sec_info = df1[["code", "name"]]
    sec_code_list = sec_info["code"].tolist()

    # also get the stocks' exchange info and add to the table
    resp = get_stock_basic_info("HK", code_list=sec_code_list)
    if resp["status"] != 200:
        print(f"error occurred in requesting futu basic info api, error is: {resp['message']}")
        return
    
    print("fetched exchange info from broker successfully")

    df2 = resp["data"]
    # Merge the two dataframes on the "code" column
    merged_df = df1.merge(df2[["code", "exchange_type"]], on="code", how="left")
    sec_info = merged_df[["code", "name", "exchange_type"]]

    for i,row in sec_info.iterrows():
        sec_code, sec_name, exchange_type = row["code"],row['name'],row['exchange_type']
        if sec_code not in sec_codes and sec_name not in sec_names:
            print(f"New security in watch list: {sec_code}: {sec_name}")

            resp = insert_into_table(conn,{"sec_code":sec_code,"sec_name":sec_name,"exchange":exchange_type},"stock")
            if resp["status"] != 200:
                print(resp["message"])

    conn.commit()
    conn.close()
    print("database updated successfully")
    return


if __name__ == "__main__":
    populate_stock_table()