from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from database.db_crud import connect_to_db,fetch_from_table,fetch_with_query,insert_into_table
import pandas as pd
from broker_api import utils
import datetime as dt
import sqlite3

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/")
def index(request:Request):

    curr_date = dt.date.today().strftime("%Y-%m-%d %H:%M:%S")

    stock_filter = request.query_params.get("filter", False)
    if stock_filter == "new_closing_high":
        query = f"""
        select * from (
            select sec_code,sec_name,stock_id,max(close),date from stock_price
            group by stock_id
            order by sec_code
            )
        where date = {curr_date}
        """
    elif stock_filter == "new_closing_low":
        query = f"""
        select * from (
            select sec_code,sec_name,stock_id,min(close),date from stock_price
            group by stock_id
            order by sec_code
            )
        where date = {curr_date}
        """
    else:
        query = """
        select sec_code,sec_name from stock order by sec_code
        """
    
    conn = connect_to_db()
    # fetch_res = fetch_from_table(conn,["sec_code","sec_name"],"stock")
    fetch_res = fetch_with_query(conn,query)
    fetched_data = fetch_res["data"]

    return templates.TemplateResponse(
        request=request, name="index.html", context={"data":fetched_data}
    )


@app.get("/stock/{sec_name}")
def get_stock_price_info(request:Request, sec_name:str):
    conn = connect_to_db()

    # ============== get the price data for the selected security ==============
    query = f"""
    SELECT stock.id,stock.sec_code,date,open,high,low,close,volume,turnover,exchange
    from stock
    left join stock_price
    on stock.id = stock_price.stock_id
    where stock.sec_name = '{sec_name}'
    order by date desc
    """

    fetch_res = fetch_with_query(conn,query)
    if not fetch_res["status"] == 200:
        print(fetch_res["message"])
        return
    
    fetched_data = fetch_res["data"]
    df = pd.DataFrame(fetched_data)
    df.columns = ["stock_id","sec_code","date","open","high","low","close","volume","turnover","exchange"]

    # obtain sec_code and exchange, then drop them from the dataframe because we don't need them in every single row
    stock_id = df["stock_id"].iloc[0]
    sec_code = df["sec_code"].iloc[0]
    exchange = df["exchange"].iloc[0]

    df.drop(columns=["stock_id"],inplace=True)
    df.drop(columns=["sec_code"],inplace=True)
    df.drop(columns=["exchange"],inplace=True)

    formatted_ticker_dic = utils.format_ticker_for_tradingview(sec_code)
    tradingview_symbol = formatted_ticker_dic["symbol"]
    tradingview_exchange = formatted_ticker_dic["exchange"]

    # ========================================================================

    # ======================== get the strategy list  ========================
    query = f"""
    SELECT * from strategy
    """
    fetch_res = fetch_with_query(conn,query,row_factory=True)
    available_strategies = fetch_res["data"]
    # available_strategies.columns = ["id","name","description"]

    conn.close()

    return templates.TemplateResponse(
        request=request, 
        name="market_data_table.html", 
        context={
            "data":df.values,
            "stock_id":stock_id,
            "sec_name":sec_name,
            "sec_code":sec_code,
            "exchange":tradingview_exchange,
            "symbol":tradingview_symbol,
            "strategies":available_strategies
        }
    )


@app.post("/apply_strategy")
def apply_strategy(strat_id:int=Form(...), stock_id:int=Form(...)):
    conn = connect_to_db()

    print(f"strategy id: {strat_id}, stock id: {stock_id}")

    insert_query = f"""
        INSERT OR IGNORE INTO stock_strategy (stock_id,strategy_id) VALUES ({stock_id},{strat_id})
    """

    res = fetch_with_query(conn,insert_query)
    if res["status"] != 200:
        print(res["message"])
    conn.commit()
    conn.close()
    
    return RedirectResponse(url=f"strategy/{strat_id}", status_code=303)


@app.get("/strategy/{strat_id}")
def strategy(request:Request, strat_id:int):
    conn = connect_to_db()

    # 找到选中策略的信息
    query = f"""
    SELECT id,name,description FROM strategy WHERE id={strat_id}
    """

    fetch_res = fetch_with_query(conn,query,row_factory=True)
    if not fetch_res["status"] == 200:
        print(fetch_res["message"])
        return
    
    strategy = fetch_res["data"][0]

    # 找到所选策略的所有股票
    query = f"""
    SELECT sec_code,sec_name
    FROM stock join stock_strategy on stock.id = stock_strategy.stock_id
    WHERE strategy_id = {strat_id}
    """

    fetch_res = fetch_with_query(conn,query,row_factory=True)
    if not fetch_res["status"] == 200:
        print(fetch_res["message"])
        return
    
    stocks_in_strategy = fetch_res["data"]
    
    return templates.TemplateResponse(
        request=request,
        name="strategy.html",
        context={"strategy":strategy,"stocks_in_strategy":stocks_in_strategy}
    )