""" create a lambda function that samples an api and sends results to dynamodb """
import json
import requests
import random
import boto3
import time
import os
from datetime import datetime, timedelta


def lambda_handler(event, context):
    data = get_sentiments()
    articles = data['articles']
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('news_sentiment_dataset')
    for article in articles:
        table.put_item(
            Item={
                'title': article['title'],
                'description': article['description'],
                'url': article['url'],
                'source': article['source']['name'],
                'publishedAt': article['publishedAt']
            }
        )

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }

import string 

def get_sentiments(company_symbol='', news_topic='', time_from='', time_to='', sort_by='LATEST'):
    endpoint = "https://www.alphavantage.co/query"
    parameters = {
        "function": "NEWS_SENTIMENT",
        "sort": sort_by,
        "limit": "200"
    }
    if time_from and time_to: parameters['time_from'] = time_from; parameters['time_to'] = time_to
    if news_topic: parameters['topics'] = news_topic
    if company_symbol: parameters['tickers'] = company_symbol
    for i in range(100):
        parameters['apikey'] = ''.join(random.choices(string.ascii_uppercase + string.digits, k=15))
        # Send a GET request to the API endpoint
        response = requests.get(endpoint, params=parameters)
        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            if 'Note' not in data: 
                break
            data = None
            time.sleep(1)
        else: 
            return
    return data


def sweep_news_in_range(start_time: datetime, day_range: int = 100):
    # create a folder to store the sentiments and ignore if it already exists
    os.makedirs('sentiments', exist_ok=True)
    sentiment_list = []
    for i in tqdm(range(day_range)):
        # repeat the process for ealiest and latest
        for sort_by in ['LATEST', 'EARLIEST', 'RELEVANCE']:
            # get the time range
            time_to = (start_time - timedelta(days=i)).strftime('%Y%m%dT%H%M')
            time_from = (start_time - timedelta(days=i+1)).strftime('%Y%m%dT%H%M')
            # get the news sentiment for the past week
            sentiment = get_sentiments(news_topic='financial_markets', time_from=time_from, time_to=time_to, sort_by=sort_by)
            if sentiment is None:
                logger.error(f'Unnable to fetch sentiment data for {sort_by} from {time_from} to {time_to}')
                continue
            with open(os.path.join('sentiments', f'sentiments_{sort_by}_{time_from}.json'), 'w') as f:
                json.dump(sentiment, f, indent=4)
            # append the sentiment to the list
            sentiment_list.append(sentiment)
    return sentiment_list


""" use urllib3 to get daily stocks from yahoo finance """
import urllib3
import json
import os
import pandas as pd
from datetime import datetime, timedelta
from tqdm import tqdm

def get_daily_stocks(ticker: str, start_date: datetime, end_date: datetime):
    urllib3.disable_warnings()
    http = urllib3.PoolManager()
    # create a folder to store the stocks and ignore if it already exists
    os.makedirs('stocks', exist_ok=True)
    # get the start and end date
    start_date = start_date.strftime('%Y-%m-%d')
    end_date = end_date.strftime('%Y-%m-%d')
    # get the stock data
    url = f'https://query1.finance.yahoo.com/v7/finance/download/{ticker}?period1=0&period2=9999999999&interval=1d&events=history&includeAdjustedClose=true'
    r = http.request('GET', url)
    r.json = json.loads(r.data.decode('utf-8'))
    # convert the data to a dataframe
    df = pd.read_csv(r, index_col='Date', parse_dates=True)
    # filter the data by the start and end date
    df = df.loc[start_date:end_date]
    # save the data to dynamodb
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('stocks')
    for index, row in df.iterrows():
        table.put_item(
            Item={
                'ticker': ticker,
                'date': index.strftime('%Y-%m-%d'),
                'open': row['Open'],
                'high': row['High'],
                'low': row['Low'],
                'close': row['Close'],
                'adj_close': row['Adj Close'],
                'volume': row['Volume']
            }
        )
    # save the data to a csv file
    df.to_csv(os.path.join('stocks', f'{ticker}.csv'))
    return df

