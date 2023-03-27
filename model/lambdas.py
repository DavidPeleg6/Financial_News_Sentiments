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
import datetime, io
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
    pred = model.predict(stock_prices.drop(['close'])) # TODO: drop adjusted close too
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

# TODO: WHAT ARE ALL OF THESE (wait for info from dudu)
_rds_host = "????"
_rds_name = "????"
_rds_pass = "????"
_rds_db = "stockdata"
_rds_table = "????"
_columns = ["???", "????"]

def get_data(token: str, start: datetime.date, end: datetime.date) -> pd.DataFrame:
    # loads and returns data from an RDS database for the date range given
    # returns an empty df if it fails
    try:
        conn = pymysql.connect(_rds_host, user=_rds_name, passwd=_rds_pass, db=_rds_db, connect_timeout=5)
        # Execute SQL query
        with conn.cursor() as cur:
            cur.execute(f"SELECT * FROM {_rds_table}") 
            rows = cur.fetchall()
        # Close database connection
        conn.close()
        # Convert query result to Pandas DataFrame
        df = pd.DataFrame(rows, columns=_columns)
    except Exception as e:
        print("Error:\t" + str(e))
        df = pd.DataFrame()
    return df
# ----------------------------------------------------------------------------------------------------------
