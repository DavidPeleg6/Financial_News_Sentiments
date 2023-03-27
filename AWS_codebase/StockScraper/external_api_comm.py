import requests
import pandas as pd
import time
import string
import random
from datetime import datetime, timedelta


def get_stockprice(company_symbol: str = 'MSFT'):
    endpoint = "https://www.alphavantage.co/query"
    parameters = {
        "function": "TIME_SERIES_DAILY_ADJUSTED",
        "symbol": company_symbol,
        "outputsize": 'full'
    }
    for _ in range(100):
        parameters['apikey'] = ''.join(random.choices(string.ascii_uppercase + string.digits, k=15))
        # Send a GET request to the API endpoint
        response = requests.get(endpoint, params=parameters)
        # Check if the request was successful
        if response.status_code == 200 and 'Note' not in response.json():
            return response.json()
        else:
            time.sleep(1)


def add_indicators(price_df, time_back) -> pd.DataFrame:
    """
    Add indicators to the price dataframe
    :param price_df: the price dataframe
    :return: the price dataframe with indicators
    """
    # convert the date column to datetime from format YYYY-MM-DD
    price_df['date'] = pd.to_datetime(price_df['date'])
    # set the date column as the index
    price_df = price_df.set_index('date').sort_index(ascending=True)
    # take a moving average of the adjusted close price
    price_df['30_day_MA'] = price_df['adj_close'].rolling(30).mean()
    price_df['50_day_MA'] = price_df['adj_close'].rolling(50).mean()
    price_df['100_day_MA'] = price_df['adj_close'].rolling(100).mean()
    price_df['200_day_MA'] = price_df['adj_close'].rolling(200).mean()
    # the highs and lows
    price_df['4_week_high'] = price_df['adj_close'].rolling(4*7).max()
    price_df['4_week_low'] = price_df['adj_close'].rolling(4*7).min()
    price_df['10_week_high'] = price_df['adj_close'].rolling(10*7).max()
    price_df['10_week_low'] = price_df['adj_close'].rolling(10*7).min()
    price_df['52_week_high'] = price_df['adj_close'].rolling(52*7).max()
    price_df['52_week_low'] = price_df['adj_close'].rolling(52*7).min()
    # take only the data up to 2 years ago and convert to numeric
    price_df = price_df[price_df.index >= datetime.now() - timedelta(days=time_back)].dropna().sort_index(ascending=False)
    return price_df


def convert_dict_to_df(stock: str, daily_prices: dict, time_back=2) -> pd.DataFrame:
    """Convert a dictionary of stock data to a pandas dataframe.
    
    Args:
        stock_dict (dict): A dictionary of stock data.
    
    Returns:
        pd.DataFrame: A dataframe of stock data.
    """
    # create a row for each stock and date
    rows = []
    for date, price in daily_prices.items():
        rows.append([stock, date, price['1. open'], price['2. high'], price['3. low'], price['4. close'], price['5. adjusted close'], price['6. volume'], price['7. dividend amount'], price['8. split coefficient']])
    # create a dataframe from the rows
    price_df = pd.DataFrame(rows, columns=['stock', 'date', 'open', 'high', 'low', 'close', 'adj_close', 'volume', 'dividend', 'split'])
    # convert all columns to numeric except for the date and stock
    price_df[price_df.columns[2:]] = price_df[price_df.columns[2:]].apply(pd.to_numeric, errors='coerce')
    price_df = add_indicators(price_df, time_back)
    return price_df
