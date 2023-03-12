import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from tqdm import tqdm
from pprint import pprint
import logging
import boto3

# if a log file already exists, delete it
if os.path.exists('dataset_build.log'):
    os.remove('dataset_build.log')
# set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# create a file handler
handler = logging.FileHandler('dataset_build.log')
handler.setLevel(logging.INFO)
# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(handler)


prices = {}
# iterate over all json files in the prices folder
for file in tqdm(os.listdir('prices')):
    # open the json file
    with open(os.path.join('prices', file)) as f:
        daily_stock = json.load(f)
        if 'Time Series (Daily)' not in daily_stock:
            logger.error('No time series data for {}'.format(file))
            continue
        prices[daily_stock['Meta Data']['2. Symbol']] = daily_stock['Time Series (Daily)']


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
    price_df = price_df[price_df.index > datetime.now() - timedelta(days=365*2)].dropna().sort_index(ascending=False)
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


# iterate all the stocks and convert the data to a dataframe
stock_dfs = []
for stock, daily_prices in tqdm(prices.items()):
    stock_dfs.append(convert_dict_to_df(stock, daily_prices))
# concatenate all the dataframes into one
stocks_df = pd.concat(stock_dfs)


# use boto3 to write the dataframe to dynamodb
dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
table = dynamodb.Table('StockPrices')
# iterate over all the rows in the dataframe
for index, row in tqdm(stocks_df.iterrows()):
    # convert the index to a string
    date = str(index)
    # create a dictionary of the row data and convert all the values to strings
    row_dict = {key: str(value) for key, value in row.to_dict().items()}
    # add the date to the dictionary
    row_dict['Date'] = date
    # change the stock name to ticker
    row_dict['Stock'] = row_dict.pop('stock')
    # write the data to dynamodb
    table.put_item(Item=row_dict)


