import json, boto3, pymysql
import pandas as pd
import datetime, io, os
from boto3.dynamodb.conditions import Key, Attr
import traceback

table_name = "ModelsXGB"

# incosistent column names bandaid fix
colnames_dict = {
    "adj_close": "adjusted_close",
    "dividend": "dividend_amount",
    "split": "split_coefficient"
}

def lambda_handler(event, context):
    """
    Gets a token name and a range of dates as input
    Returns the predictions for those dates as a dictionary

    """
    import xgboost as xgb
    import sklearn
    # parse input
    token = event.get('token', '')
    start_s = event.get('start', '')
    end_s = event.get('end', '')
    start = datetime.datetime.strptime(start_s, '%Y-%m-%d').date()
    end = datetime.datetime.strptime(end_s, '%Y-%m-%d').date()

    # get data
    stock_prices = get_data(token, start, end)
    if stock_prices.empty:
        print("No data avilable for " + token)
        return {
            'statusCode': 500,
            'body': "No data avilable for " + token
        }
    
    # get the model
    model = get_model_ddb(token)
    if model == None:
        print("No model avilable for " + token)
        return {
            'statusCode': 500,
            'body': "No model avilable for " + token
        }
    # make predictions for the data using the model
    try:
        # rename columns (this is coz we were inconsistent in naming these)
        stock_prices = stock_prices.rename(columns=colnames_dict)
        pred = model.predict(stock_prices.drop('close', axis=1))
    except Exception as e:
        print("Failed to make predictions.")
        print(str(e))
        return {
            'statusCode': 500,
            'body': "Prediction failed for " + token
        }
    # the predictions are a numpy array, so we put them in a dataframe
    pred_df = pd.DataFrame({'Date': stock_prices.index, 'close': pred})
    return {
            'statusCode': 200,
            'body': pred_df.to_json()
        }

def get_model_ddb(token: str):
    # returns a model that can be used to predict the value of 'token'
    # if model loading fails it returns None
    import xgboost as xgb
    import pickle
    dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
    table = dynamodb.Table("ModelsXGB")
    response = table.query(KeyConditionExpression=Key('Stock').eq(token))
    if 'Items' not in response:
        return None
    try:
        item = response['Items'][0]
        # Retrieve the binary model data from the 'model_data' attribute
        model_data = item['Model'].value
        # Load the binary data into an XGBoost model using pickle
        xgb_model = pickle.loads(model_data)
    except Exception as e:
        print("Error when attempting to parse model bytes")
        print(str(e))
        return None
    return xgb_model

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
                AND Stock = "{str.upper(token)}";"""
        data = pd.read_sql_query(query, connection, parse_dates=['Date'])
        connection.close()
        # convert the data to a pandas dataframe and drop the stock column
        df = pd.DataFrame(data).drop(columns=['Stock'], errors='ignore')
        df = df.set_index('Date')
        df.index = pd.to_datetime(df.index)
        df = df.sort_index(ascending=False)
    except Exception as e:
        print("Error:\t" + str(e))
        df = pd.DataFrame()
    return df
