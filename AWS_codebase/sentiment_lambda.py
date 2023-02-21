import json
import boto3
from datetime import datetime, timedelta
import random
import string
import urllib3
import time

def lambda_handler(event, context):
    sentiment_list = []
    # get the time range
    time_to = datetime.now().strftime('%Y%m%dT%H%M')
    time_from = (datetime.now() - timedelta(minutes=30)).strftime('%Y%m%dT%H%M')
    # get the news sentiment for the past week
    sentiments = get_sentiments(news_topic='financial_markets', time_from=time_from, time_to=time_to)
    if sentiments is None: return {'statusCode': 41, 'body': "failed to read from alphavantage!"}
    
    # add a new row according to: Stock, Date, Sentiment, Site, URL
    for article in sentiments["feed"]:
        def make_dict_from_sents(sents):
            sents['Stock'] = sents['ticker']
            sents.pop('ticker')
            sents['url'] = article['url']
            sents['source'] = article['source']
            sents['Date'] = article['time_published']
            return sents
        # append the sentiment to the list
        sentiment_list.extend([make_dict_from_sents(tickers_sents) for tickers_sents in article['ticker_sentiment']])
    
    # print(sentiment_list)
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('StockSentiment')
    # print('number of articles: ', len(sentiment_list))
    with table.batch_writer() as batch:
        for row in sentiment_list:
            batch.put_item(Item=row)
    
    return {'statusCode': 200, 'body': "success!"}


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
