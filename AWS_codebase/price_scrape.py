import requests
from pprint import pprint
import csv
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import time
from tqdm import tqdm
import calendar
import os
import string
import random
import boto3


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
        if response.status_code == 200:
            data = response.json()
            if 'Note' not in data: 
                break
            print(f'API key {parameters["apikey"]} has been used too many times. response note: {data["Note"]}')
            data = None
            time.sleep(1)
        else: 
            print(f'API key {parameters["apikey"]} has returned an error. response note: {response.json()}')
    return data


# get stock price for all tickers
def get_stockprice_all(stocks_to_watch: list):
    os.makedirs('prices', exist_ok=True)
    # only get stock price for stocks that are not in the directory
    seen_stocks = [f.split('.')[0] for f in os.listdir('prices') if os.path.isfile(os.path.join('prices', f))]
    for ticker in tqdm([t for t in stocks_to_watch if t not in seen_stocks]):
        data = get_stockprice(ticker)
        if data is None: 
            print(f'Unnable to fetch data for {ticker}')
            continue
        with open(f'prices/{ticker}.json', 'w') as outfile:
            json.dump(data, outfile, indent=4)

# get table from dynamodb
def get_table(table_name: str):
    
    return table

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('StockSentiment')
# get the a list of tickers sorted by frequency
sentiment_ticker_list = get_table('sentiment').scan()['Items']
print(sentiment_ticker_list)
# get a list of tickers sorted by frequency
# sentiment_ticker_list = sentiment_df['ticker'].value_counts().index.tolist()