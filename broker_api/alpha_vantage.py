import requests
import pandas as pd

# documentation_page = "https://www.alphavantage.co/documentation/"

# api_key = "B5AMLO7ANJOQQMWK"
# url = f'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=PDD&interval=30min&apikey={api_key}'
# # url = f'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={ticker}&interval=30min&outputsize=full&apikey={api_key}'
# r = requests.get(url)
# data = r.json()

# for key,val in data.items():
#     print(key)


dic = {
    "2025-01-02 19:55:00": {
        "1. open": "220.2000",
        "2. high": "220.2000",
        "3. low": "219.2000",
        "4. close": "219.2000",
        "5. volume": "174"
    },
    "2025-01-02 19:50:00": {
        "1. open": "219.9900",
        "2. high": "219.9900",
        "3. low": "219.9900",
        "4. close": "219.9900",
        "5. volume": "1"
    }
}

df = pd.DataFrame(dic).T
df.reset_index(inplace=True,names='time')
print(df)