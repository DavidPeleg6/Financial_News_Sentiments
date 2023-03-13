import requests
import pandas as pd
import json
import time
from tqdm import tqdm
import os
import string
import random
import boto3
import logging
import numpy as np
from datetime import datetime, timedelta
import logging
import boto3

# get the absolute path to the current directory and change the current directory to the current directory
# os.chdir(os.path.dirname(os.path.abspath(__file__)))
# The maximum number of stocks to scrape
MAX_STOCKS = 1000
# the number of days to look back
TIME_BACK = 5
# TIME_BACK = 365*2


def build_logger(log_name:str):
    global logger
    # if a log file already exists, delete it
    if os.path.exists(f'{log_name}.log'):
        os.remove(f'{log_name}.log')
    # set up logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    # create a file handler
    handler = logging.FileHandler(f'{log_name}.log')
    handler.setLevel(logging.INFO)
    # create a logging format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(handler)
    return logger


def get_stockprice(company_symbol: str = 'MSFT'):
    global logger
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
            logger.info(f'API key {parameters["apikey"]} has been used too many times. response note: {response.json()}')
            time.sleep(1)


def add_indicators(price_df) -> pd.DataFrame:
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
    price_df['50_day_MA'] = price_df['adj_close'].rolling(30).mean()
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
    # price_df = price_df[price_df.index > datetime.now() - timedelta(days=365*2)].apply(pd.to_numeric).dropna().sort_index(ascending=False)
    price_df = price_df[price_df.index >= datetime.now() - timedelta(days=TIME_BACK)].dropna().sort_index(ascending=False)
    return price_df


def convert_dict_to_df(stock: str, daily_prices: dict) -> pd.DataFrame:
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
    price_df = add_indicators(price_df)
    return price_df


# get stock price for all tickers
def get_stockprice_all(stocks_to_watch: list):
    global logger
    # create the prices directory relative to the current directory
    os.makedirs('prices', exist_ok=True)
    # only get stock price for stocks that are not in the directory
    seen_stocks = [f.split('.')[0] for f in os.listdir('prices') if os.path.isfile(os.path.join('prices', f))]
    stocks = [t for t in stocks_to_watch if t not in seen_stocks]
    # for ticker in tqdm([t for t in stocks_to_watch if t not in seen_stocks]):
    progress = tqdm(stocks, desc='Fetching stock prices')
    for ticker in progress:
        progress.set_postfix_str(ticker)
        data = get_stockprice(ticker)
        if data is None: 
            logger.error(f'Unnable to fetch data for {ticker}')
            continue
        with open(f'prices/{ticker}.json', 'w') as outfile:
            json.dump(data, outfile, indent=4)

logger = build_logger('price_scrape')
# define a boto resource in the ohio region
dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
table = dynamodb.Table('StockSentiment')
# get a list of all items in the Stock column sorted by frequency
sentiment_ticker_list = pd.DataFrame(table.scan()['Items'])
# convert Date column to datetime
sentiment_ticker_list['Date'] = pd.to_datetime(sentiment_ticker_list['Date'])
# make the index the Date column
sentiment_ticker_list = sentiment_ticker_list.set_index('Date').sort_index(ascending=False)

# get a list of tickers sorted by frequency
sorted_tickers = sentiment_ticker_list['Stock'].value_counts().index.tolist()
# remove any stocks that contain crypto or forex and take the first MAX_STOCKS
sorted_tickers = [t for t in sorted_tickers if 'crypto' not in t.lower() and 'forex' not in t.lower()][:MAX_STOCKS]
# print(f'Number of tickers: {len(sorted_tickers)}, tickers: {sorted_tickers}')

get_stockprice_all(sorted_tickers)


logger = build_logger('dataset_build')
prices = {}
# iterate over all json files in the prices folder
for file in tqdm(os.listdir('prices'), desc='Loading stock prices'):
    # open the json file
    with open(os.path.join('prices', file)) as f:
        daily_stock = json.load(f)
        if 'Time Series (Daily)' not in daily_stock:
            logger.error('No time series data for {}'.format(file))
            continue
        prices[daily_stock['Meta Data']['2. Symbol']] = daily_stock['Time Series (Daily)']

# iterate all the stocks and convert the data to a dataframe
stock_dfs = []
for stock, daily_prices in tqdm(prices.items(), desc='Converting to dataframes'):
    stock_dfs.append(convert_dict_to_df(stock, daily_prices))
# concatenate all the dataframes into one
stocks_df = pd.concat(stock_dfs)


# use boto3 to write the dataframe to dynamodb
dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
table = dynamodb.Table('StockPrices')
with table.batch_writer() as batch:
    # iterate over all the rows in the dataframe
    for index, row in tqdm(stocks_df.iterrows(), desc='Writing to dynamodb', total=stocks_df.shape[0]):
        # convert the index to a string
        date = str(index)
        # create a dictionary of the row data and convert all the values to strings
        row_dict = {key: str(value) for key, value in row.to_dict().items()}
        # add the date to the dictionary
        row_dict['Date'] = date
        # change the stock name to ticker
        row_dict['Stock'] = row_dict.pop('stock')
        # write the data to dynamodb
        batch.put_item(Item=row_dict)

# delete all price files once youre done moving it to the cloud
for file in os.listdir('prices'):
    os.remove(os.path.join('prices', file))


