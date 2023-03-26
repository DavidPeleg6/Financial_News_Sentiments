"""
Download data from online sources.

Note that all of the preprocessesing and dtype conversions are only in offline_data.

If you want data just use the functions in offline_data
"""

from time import sleep
import string
from random import choices
import pandas as pd
import requests
import boto3
import logging

import consts



def _get_data(parameters):
    """
    TODO: dudu plz write documentation for this idk how this function works
    also I deleted all the logging stuff inside it, it was the only function that used that crap anyways
    """
    for _ in range(100):
        parameters['apikey'] = ''.join(choices(string.ascii_uppercase + string.digits, k=15))
        # Send a GET request to the API endpoint
        response = requests.get(consts.price_data_source, params=parameters)
        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            if 'Note' not in data: 
                break
            data = None
            sleep(1)
    return data

def get_price_data(
    token: str, function: str = 'TIME_SERIES_DAILY_ADJUSTED', outputsize: str = 'full') -> pd.DataFrame:
    """
    returns a pandas dataframe containing raw stock price data, by default the data for each day
    The columns of the data are named according to consts.stock_col_names
    Returns an empty dataframe if it could not obtain data

    token:     the ticker of the desired stock (e.g, MSFT for Microsoft)
    function:   TODO: what is this
    outputsize: TODO: what is this
    """
    parameters = {
        "function": function,
        "symbol": token,
        "outputsize": outputsize
    }
    try:
        data = _get_data(parameters)
        # convert from a dictionary to a pandas dataframe
        price_df = pd.DataFrame.from_dict(data['Time Series (Daily)'], orient='index')
        return price_df
    except:
        return pd.DataFrame()

def get_news_sentiments(token: str = None) -> pd.DataFrame:
    # returns the news sentiments for token, if no token is provided sentiments for all tokens is returned
    # returns an empty dataframe if it couldn't obtain the data for whatever reason

    # TODO: this code currently doesn't work. some sorta type error, fix it later. (there's no data anyways)
    return pd.DataFrame()

    _waste_money = False
    # due to 'running this actually costs money' we doing this instead.
    # TODO: remove this variable to test things for real
    if not _waste_money:
        try:
            sentiment_df = pd.read_csv("news_sentiments.csv", index_col="Date")
        except:
            print("Failed to read news_sentiments.csv, put it in this folder.")
            return pd.DataFrame()
    else:
        # TODO: this code gets ALL of the sentiments, it should get modified to obtain sentiments for only one token
        # TODO (part2): note that the code below would also need to be modified
        # define a boto resource in the ohio region
        dynamodb = boto3.resource('dynamodb', region_name='us-east-2',
                                aws_access_key_id=consts.aws_access_key_id,
                                aws_secret_access_key=consts.aws_secret_access_key)
        table = dynamodb.Table('StockSentiment')
        # keep scanning until we have all the data in the table
        response = table.scan()
        data = response['Items']
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            data.extend(response['Items'])
    # convert the data to a pandas dataframe
    sentiment_df = pd.DataFrame(data)
    if token == None:
        return sentiment_df
    # take only the rows with the right token
    sentiment_df = sentiment_df.loc[sentiment_df[consts.sentiment_col_names_dic['Stock']] == token]
    sentiment_df = sentiment_df.drop(consts.sentiment_col_names_dic['Stock'], axis=1)
    return sentiment_df

def get_earnings_report(token: str, horizon: str = "12month") -> pd.DataFrame:
    """
    get data from the quaterly reports for the stock 'token' for the past 'horizon' time (defaults to 1 year).
    returns an empty dataframe if it could not obtain data
    """
    try:
        functions = consts.financial_sheets_functions
        # TODO: right now only 'EARNINGS' is actually used for anything, maybe use the other stuff too?
        overviews = [_get_data({"function": function, "symbol": token, "horizon": horizon}) for function in functions]
        earnings_df = pd.DataFrame.from_dict(overviews[4]['quarterlyEarnings'])
        return earnings_df
    except:
        return pd.DataFrame()

def write_to_DDB(table: str, data: dict) -> bool:
    """
    Write 'data' to the dynamoDB table called 'table'.
    Returns if the write was succsussful or not
    """
    try:
        # get client
        dynamodb = boto3.client('dynamodb', region_name='us-east-2',
                                aws_access_key_id=consts.aws_access_key_id,
                                aws_secret_access_key=consts.aws_secret_access_key)
        # put the item in the table
        response = dynamodb.put_item(
            TableName=table,
            Item=data
        )
        # Check response to see if it wrote good
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            logging.info(f"Successfully wrote item to {table}")
            return True
        else:
            logging.error(f"Failed to write item to {table}")
            return False
    except Exception as e:
        logging.error(f"Error writing item to {table}: {e}")
        return False