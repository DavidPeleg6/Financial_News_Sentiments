"""
This file is just a collection of all of the lambda functions used in aws for model related functionality
Each function is preceded by all of the imports that it has on aws, even if it already appears elsewhere in this file
Each is also encased in these big lines to signify the points between them
"""
# ----------------------------------------------------------------------------------------------------------
# model_get_predictions
import json, boto3, pymysql
import pandas as pd
import xgboost as xgb
import datetime, io, os
from boto3.dynamodb.conditions import Key, Attr

def lambda_handler(event, context):
    """
    Gets a token name and a range of dates as input
    Returns the predictions for those dates as a dictionary

    """
    # parse input
    token = event.get('token', '')
    start_s = event.get('start', '')
    end_s = event.get('end', '')
    start = datetime.strptime(start_s, '%Y-%m-%d')
    end = datetime.strptime(end_s, '%Y-%m-%d')

    # get data
    stock_prices = get_data(token, start, end)
    if stock_prices.empty:
        print("No data avilable for " + token)
        return {
            'statusCode': 500,
            'body': stock_prices.to_json()
        }
    stock_prices.set_index('Date', inplace=True)
    stock_prices.index = pd.to_datetime(stock_prices.index)
    # make the index the Date column
    stock_prices.sort_index(ascending=False, inplace=True)
    
    # get the model
    model = get_model(token)
    if model == None:
        print("No model avilable for " + token)
        return {
            'statusCode': 500,
            'body': stock_prices.to_json()
        }
    # make predictions for the data using the model
    pred = model.predict(stock_prices.drop(['close']))
    return {
            'statusCode': 200,
            'body': pred.to_json()
        }

bucket_name = "financialnewssentimentsmodel"
folder_name = "model_data/"

def get_model(token: str) -> xgb.XGBRegressor:
    # returns a model that can be used to predict the value of 'token'
    # if model loading fails it returns None
    s3 = boto3.client('s3')
    key = folder_name + token + ".bin"
    try:
        s3_object = s3.get_object(Bucket=bucket_name, Key=key)
        model_bytes = s3_object['Body'].read()
        # Load the saved XGBoost model from binary data
        model = xgb.Booster(model_file=io.BytesIO(model_bytes))
    except Exception as e:
        print("Error:\t"+ str(e))
        return None
    return model

def get_data(token: str, start: datetime.date, end: datetime.date) -> pd.DataFrame:
    # loads and returns data from an RDS database for the date range given
    # returns an empty df if it fails
    start_s = start.strftime('%Y-%m-%d')
    end_s = end.strftime('%Y-%m-%d')
    try:
        connection = pymysql.connect(
            host = os.environ['rds_host'],
            user = os.environ['rds_name'],
            passwd=os.environ['rds_pass'],
            db  =  os.environ['rds_db']
            )
        # Execute SQL query
        query = f"""SELECT *
                FROM Prices
                WHERE Date BETWEEN '{start_s}' AND '{end_s}'
                AND Stock = '{str.upper(token)}';"""
        data = pd.read_sql_query(query, connection, parse_dates=['Date'])
        connection.close()
        # convert the data to a pandas dataframe and drop the stock column
        df = pd.DataFrame(data).drop(columns=['Stock'], errors='ignore')
        df = df.set_index('Date')
        df = df.sort_index(ascending=False)
    except Exception as e:
        print("Error:\t" + str(e))
        df = pd.DataFrame()
    return df
# ----------------------------------------------------------------------------------------------------------
