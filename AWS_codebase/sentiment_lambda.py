import json
from datetime import datetime, timedelta
import random
import string
import urllib3
import time
import pandas as pd
import pymysql
from sqlalchemy import create_engine
import os
import sqlalchemy


def get_sentiments(company_symbol='', news_topic='', time_from='', time_to='', sort_by='LATEST'):
    http = urllib3.PoolManager()
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
        response = http.request('GET', url=endpoint, fields=parameters)
        # Check if the request was successful
        if response.status == 200:
            data = json.loads(response.data.decode('utf-8'))
            if 'Note' not in data: 
                break
            data = None
            time.sleep(1)
        else: 
            return
    return data


def lambda_handler(event, context):
    #-------------------------------------------- GET RECENT NEWS SENTIMENT --------------------------------------------#
    sentiment_list = []
    # get the time range
    time_to = datetime.now().strftime('%Y%m%dT%H%M')
    time_from = (datetime.now() - timedelta(minutes=300)).strftime('%Y%m%dT%H%M')
    # get the news sentiment for the past week
    sentiments = get_sentiments(news_topic='financial_markets', time_from=time_from, time_to=time_to)

    # add a new row according to: Stock, Date, Sentiment, Site, URL
    for article in sentiments["feed"]:
        def make_dict_from_sents(sents):
            sents['article_url'] = article['url']
            sents['source'] = article['source']
            sents['time_published'] = article['time_published']
            return sents
        # append the sentiment to the list
        sentiment_list.extend([make_dict_from_sents(tickers_sents) for tickers_sents in article['ticker_sentiment']])

    #-------------------------------------------- CONVERT TO DATAFRAME ------------------------------------------------#
    sentiment_df = pd.DataFrame(sentiment_list).rename(columns={'ticker': 'stock', 'ticker_sentiment_score': 'sentiment', 'ticker_sentiment_label': 'sentiment_label', 'url': 'article_url'})
    # convert Date column to datetime
    sentiment_df['time_published'] = pd.to_datetime(sentiment_df['time_published'])
    sentiment_df = sentiment_df.set_index(['time_published','stock'])

    #-------------------------------------------- WRITE TO DATABASE ---------------------------------------------------#
    dtypes = {'time_published': sqlalchemy.types.DATETIME, 'relevance_score': sqlalchemy.types.DECIMAL(6,5), 'sentiment': sqlalchemy.types.DECIMAL(6,5),
                                'stock': sqlalchemy.types.VARCHAR(10), 'sentiment_label': sqlalchemy.types.VARCHAR(10), 'article_url': sqlalchemy.types.VARCHAR(200), 'source': sqlalchemy.types.VARCHAR(50)}
    url, username, password = os.environ['URL'], os.environ['ID'], os.environ['PASS']
    # Establish connection to the MySQL database
    conn = pymysql.connect(host=url, user=username, password=password, db='stock_data')
    # Create a SQLAlchemy engine object
    engine = create_engine(f'mysql+pymysql://{username}:{password}@{url}/stock_data', echo=False)
    for i in range(len(sentiment_df)):
        try:
            sentiment_df.iloc[i:i+1].to_sql(name='Sentiments', con=engine, if_exists='append', index=True, index_label=['time_published', 'stock'], dtype=dtypes)
        except Exception as e:
            # print(sentiment_df.iloc[i:i+1])
            pass
    # Close the connection
    conn.close()
    
    return {'statusCode': 200, 'body': "success!"}



