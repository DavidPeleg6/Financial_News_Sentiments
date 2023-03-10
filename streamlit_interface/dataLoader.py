# this version just loads constant data, it's only for use as an example

import streamlit as st
import pandas as pd
import numpy as np
import datetime
import os
import boto3

# This is the "don't waste money" variable, it makes the code load local data instead of accessing AWS
# Set this to false to waste money (and also test the actual thing)
_OFFLINE_DATA = False

_update_interval = datetime.timedelta(days=1)

_recommended_stocks_cache_filename = "recommended_stocks_cache"
_past_accuracy_cache_filename = "past_accuracy_cache"
_sentiment_data_cache_filename = "sentiment_data_cache"
_past_stock_prices_cache_filename = "past_stock_prices_cache"

_datapth = 'temp_data/'
_datetime_format = "%Y-%m-%d %H:%M:%S"
_valid_predgoals = ['Daily', 'Weekly', 'Monthly']

def cache_dec(filename: str):
    # this decorator MUST be used alongside @st.cache_data. this one should come first
    # the function which is decorated should have a 'time' variable, preferabbly with a default value of 'None'.
    def decorator(func):
        def wrapper(*args, **kwargs):
            if "time" not in kwargs:
                print(f"Invalid use of the cache_dec decorator. {func} must have a time variable")
            cachedata_fname = filename
            if "predgoal" in kwargs:
                cachedata_fname = cachedata_fname + "_" + kwargs["predgoal"]
            time = _checkIfCacheUpdate(cachedata_fname)
            result = func(*args, time = time, **kwargs)
            return result
        return wrapper
    return decorator

def _checkIfCacheUpdate(filename : str) -> datetime.datetime:
    """
    checks if more than a day has passed since the time stored in filename
    if true, update the time in filename and return the current time
    otherwise, do nothing and return the time stored in filename
    """
    now = datetime.datetime.now()
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            f.write(now.strftime(_datetime_format))
        last = now
    else:
        with open(filename, "r") as f:
            last = datetime.datetime.strptime(f.read().strip(), _datetime_format)
    # now that you got 'now' and 'last', check their difference
    difference = now - last
    if _update_interval.total_seconds() < difference.total_seconds():
        # elapsed time is greater than _update_interval. Update the cache and time  
        with open(filename, "w") as f:
            f.write(now.strftime(_datetime_format))
        return now
    # elapsed time is smaller than _update_interval. Keep cache the same
    return last

@cache_dec(_sentiment_data_cache_filename)
@st.cache_data
def getSentimentData(time : datetime.datetime = None) -> pd.DataFrame:
    """
    TODO: write documentation here
    """
    if _OFFLINE_DATA:
        return pd.read_csv("news_sentiments.csv", index_col="Date")
    # specify key and secret key
    aws_access_key_id = os.environ['DB_ACCESS_KEY']
    aws_secret_access_key = os.environ['DB_SECRET_KEY']
    # # create a boto3 client
    # dynamodb = boto3.client('dynamodb', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name='us-east-2')
    # # get a list of all items in the Stock column sorted by frequency
    # sentiment_ticker_list = pd.DataFrame(dynamodb.scan(TableName='StockSentiment')['Items'])
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-2', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
    table = dynamodb.Table('StockSentiment')
    # keep scanning until we have all the data in the table
    response = table.scan()
    data = response['Items']
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])
    # convert the data to a pandas dataframe
    sentiment_ticker_list = pd.DataFrame(data)
    # convert Date column to datetime
    sentiment_ticker_list['Date'] = pd.to_datetime(sentiment_ticker_list['Date'])
    # make the index the Date column
    sentiment_ticker_list = sentiment_ticker_list.set_index('Date').sort_index(ascending=False)
    return sentiment_ticker_list

@cache_dec(_past_stock_prices_cache_filename)
@st.cache_data
def getPastStockPrices(time : datetime.datetime = None) -> pd.DataFrame:
    """
    returns a pandas dataframe structured as follows:
    company name, ticker, sentiment score, sentiment magnitude, sentiment score change, sentiment magnitude change
    """
    if _OFFLINE_DATA:
        return pd.read_csv("news_sentiments.csv", index_col="Date")
    # specify key and secret key
    aws_access_key_id = os.environ['DB_ACCESS_KEY']
    aws_secret_access_key = os.environ['DB_SECRET_KEY']
    # # create a boto3 client
    # dynamodb = boto3.client('dynamodb', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name='us-east-2')
    # # get a list of all items in the Stock column sorted by frequency
    # stock_prices = pd.DataFrame(dynamodb.scan(TableName='StockPrices')['Items'])
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-2', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
    table = dynamodb.Table('StockPrices')
    # get a list of all items in the Stock column sorted by frequency
    stock_prices = pd.DataFrame(table.scan()['Items'])
    # convert Date column to datetime
    stock_prices['Date'] = pd.to_datetime(stock_prices['Date'])
    # make the index the Date column
    stock_prices = stock_prices.set_index('Date').sort_index(ascending=False)
    return stock_prices

@cache_dec(_recommended_stocks_cache_filename)
@st.cache_data
def getRecommendedStocks(predgoal : str = 'Weekly', time : datetime.datetime = None) -> pd.DataFrame:
    """
    gets as input a string detailing prediction targer, must be in the set _valid_predgoals
    returns a pandas dataframe structured as follows:
    company name, ticker, model predictions, past accuracy for this stock
    
    if less than a day has passed since the last call to this function, the cached result will be used
    """
    if predgoal not in _valid_predgoals:
        return None
    # TODO: actually aquire data from the model, right now it just returns this constant thing
    # (I took this from https://www.nasdaq.com/, it's just the top 5 I sawthere)
    # this if statement should actually do different stuff based on predgoal
    if predgoal == _valid_predgoals[0]:
        return pd.read_csv(os.path.join(os.path.dirname(os.path.realpath(__file__)), _datapth, 'daily_recommendations.csv'))
    if predgoal == _valid_predgoals[1]:
        return pd.read_csv(os.path.join(os.path.dirname(os.path.realpath(__file__)), _datapth, 'weekly_recommendations.csv'))
    return pd.read_csv(os.path.join(os.path.dirname(os.path.realpath(__file__)), _datapth, 'monthly_recommendations.csv'))

@cache_dec(_past_accuracy_cache_filename)
@st.cache_data
def getPastAccuracy(time_back: int = 100, time : datetime.datetime = None) -> pd.DataFrame:
    """
    returns a pandas dataframe listing the accuracy of the model in the past for each type of prediction
    the input is how many days back from right now you want it to show
    
    if less than a day has passed since the last call to this function, the cached result will be used
    """
    # TODO: actually do this, right now it just returns a randomly generated list
    # TODO: when this thing actually returns a real value, use 'time_back' to truncate it
    return pd.read_csv(os.path.join(os.path.dirname(os.path.realpath(__file__)), _datapth, 'past_accuracy.csv'))