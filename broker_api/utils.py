from futu import *
import requests

market_mapping = {
    "HK":Market.HK,
    "US":Market.US,
    "SH":Market.SH,
    "SZ":Market.SZ,
    "SG":Market.SG,
    "JP":Market.JP
}
exchange_mapping = {
    ExchType.HK_MAINBOARD: "HKEX",
    ExchType.HK_GEMBOARD: "HKEX",
    ExchType.HK_HKEX: "HKEX",
    ExchType.US_NYSE: "NYSE",
    ExchType.US_NASDAQ: "NASDAQ",
    ExchType.US_CBOE: "CBOE",
    ExchType.JP_OSE: "OSE",
}

def format_ticker_for_tradingview(ticker:str) -> dict:
    """
    Convert ticker to tradingview format
    :return dict {"exchange":str,"symbol":str}
    """
    if ticker.startswith("HK"):
        ticker_body = ticker[3:]
        while ticker_body and ticker_body[0] == "0":
            ticker_body = ticker_body[1:]
        return {"exchange": "HKEX", "symbol": ticker_body}
    
    elif ticker.startswith("US"):
        ticker_body = ticker[3:]
        return {"exchange": "NASDAQ", "symbol": ticker_body}
    
    else:
        print(f"currently only support HK and US market, your ticker is {ticker}")
        return {"exchange": "NA", "symbol": ticker}
    

def get_intraday_data_from_alphaVantage(ticker,month=None,interval:str='15min'):
    """
    从alpha vantage api获取股票过去一个月的分钟级别数据，需提供具体ticker
    :param ticker: 股票代码
    :param month: 月份，格式为YYYY-MM，如果不填的话默认为None，api会返回最近一个月的数据
    """

    api_key = "B5AMLO7ANJOQQMWK"
    if not month:
        alpha_vantage_api_url = f'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={ticker}&interval={interval}&outputsize=full&apikey={api_key}'
    else:
        alpha_vantage_api_url = f'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={ticker}&interval={interval}&month={month}&outputsize=full&apikey={api_key}'
    resp = requests.get(alpha_vantage_api_url)
    
    if resp.status_code != 200:
        print(f"failed to get data from alpha vantage for {ticker}")
        return {}
    
    data = resp.json()
    return data