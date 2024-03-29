import streamlit as st
import pandas as pd
import datetime
import os
import pymysql
import datetime
import boto3
import json
from sqlalchemy import create_engine, text

@st.cache_data(ttl=60*60*24)
def getPastStockPrices(refresh_counter, stock: str = 'MSFT', alltime = False) -> pd.DataFrame:
    """
    returns a pandas dataframe structured as follows:
    company name, ticker, sentiment score, sentiment magnitude, sentiment score change, sentiment magnitude change
    """
    # get data from the past month unless specified to take the entire dataframe
    query = f"""SELECT * FROM Prices WHERE Stock = '{str.upper(stock)}';""" if alltime else f"""
            SELECT * FROM Prices Where Stock = '{str.upper(stock)}' and Date >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH);"""
    
    # Query the database and load results into a pandas dataframe
    engine = create_engine(f"mysql+pymysql://{os.environ['ID']}:{os.environ['PASS']}@{os.environ['URL']}/stock_data")
    with engine.connect() as connection:
        stock_prices = pd.read_sql_query(sql=text(query), con=connection, parse_dates=['Date']).drop(columns=['Stock']).set_index('Date').sort_index(ascending=False)
    return stock_prices

@st.cache_data(ttl=60*60*24)
def getSentimentData(refreshes, all_time=False) -> pd.DataFrame:
    """
    returns a dataframe with the sentiment data for the stocks, as taken from the AWS database.
    the dataframe has the following columns:
    Date, ticker_sentiment_score, ticker_sentiment_label, Stock, source, url, relevance_score
    :param time: the time at which the data was last updated. this is used to check if the cache needs to be updated
    :param time_step: the time step at which the data is aggregated. can be 'Daily', 'Weekly', or 'Monthly'
    """
    # get data from the past month unless specified to take the entire dataframe
    query = """SELECT *
               FROM Sentiments
               WHERE time_published >= DATE_SUB(NOW(), INTERVAL 1 MONTH)
            """ if not all_time else """SELECT * FROM Sentiments"""
    
    # Query the database and load results into a pandas dataframe
    engine = create_engine(f"mysql+pymysql://{os.environ['ID']}:{os.environ['PASS']}@{os.environ['URL']}/stock_data", echo=False)
    with engine.connect() as connection:
        dataframe = pd.read_sql_query(sql=text(query), con=connection, parse_dates=['time_published']).set_index('time_published').sort_index(ascending=False)
    
    return dataframe

_pred_days = 60 # days back from today to try and predict

@st.cache_data(ttl=60*60*24)
def get_predictions(token: str,
                   start: datetime.date = datetime.datetime.now().date() - datetime.timedelta(days=_pred_days), 
                      end: datetime.date = datetime.datetime.now().date()) -> pd.DataFrame:
    # get stock predictions from aws by invoking the lambda function called 'model_get_predictions'
    # returns an empty dataframe if it fails
    # note that if you request a prediction for days a to b, the prediction will contains the expected values for the dates a+1 to b+1
    start_s = start.strftime('%Y-%m-%d')
    end_s = end.strftime('%Y-%m-%d')
    payload = {
        'token': token.upper(),
        'start': start_s,
        'end': end_s
    }
    # get the IAM role
    # create an sts client with your IAM user credentials
    sts_client = boto3.client('sts', region_name='us-east-2',
                            aws_access_key_id=os.environ['AV_AK'],
                            aws_secret_access_key=os.environ['AV_SAK'])
    # assume an IAM role and get temporary security credentials
    response = sts_client.assume_role(RoleArn=os.environ['model_role_arn'],
                                    RoleSessionName='my-session')
    # get the temporary security credentials
    credentials = response['Credentials']
    # use the temporary security credentials to create a lambda client
    lambda_client = boto3.client('lambda', region_name='us-east-2',
                             aws_access_key_id=credentials['AccessKeyId'],
                             aws_secret_access_key=credentials['SecretAccessKey'],
                             aws_session_token=credentials['SessionToken'])
    # Send POST request to API Gateway endpoint
    response = lambda_client.invoke(FunctionName=os.environ['model_get_predictions_arn'],
                                    InvocationType='RequestResponse',
                                    Payload=json.dumps(payload).encode('utf-8'))
    json_data = json.loads(response['Payload'].read().decode('utf-8'))
    # handle response
    if json_data['statusCode'] == 200:
        # Parse JSON response and convert to Pandas DataFrame
        df = pd.read_json(json_data["body"], orient='columns')
        # Return the DataFrame
        return df
    else:
        # Print error message and return None
        print('Error:', json_data['body'])
        return pd.DataFrame()

# TODO: COMBINE THE TWO FUNCTIONS BELOW

# this one is used in data
@st.cache_data(ttl=60*60*24*30)
def getStockEarnings(refresh_counter, stock: str) -> pd.DataFrame:
    """
    returns a dataframe with all the company's earnings data from the past 2 years along with prediction for the next quarter
    """
    # get data from the past month unless specified to take the entire dataframe
    earnings_query = f"""SELECT * FROM Earnings WHERE stock = '{str.upper(stock)}';"""
    future_earnings_query = f"""SELECT * FROM FutureEarnings WHERE stock = '{str.upper(stock)}';"""

    # Query the database and load results into a pandas dataframe
    engine = create_engine(f"mysql+pymysql://{os.environ['ID']}:{os.environ['PASS']}@{os.environ['URL']}/stock_data")
    with engine.connect() as connection:
        earnings = pd.read_sql_query(sql=text(earnings_query), con=connection, parse_dates=['fiscalDateEnding', 'reportedDate']).drop(columns=['stock']).sort_values(by='fiscalDateEnding', ascending=False)
        future_earnings = pd.read_sql_query(sql=text(future_earnings_query), con=connection, parse_dates=['fiscalDateEnding', 'reportDate']).drop(columns=['stock', 'currency']).rename(columns={'reportDate': 'reportedDate', 'estimate': 'estimatedEPS'})
    
    return pd.concat([earnings, future_earnings], axis=0, ignore_index=True).sort_values(by='fiscalDateEnding', ascending=False)

# this one is used in recommendations
@st.cache_data(ttl=60*60*24*30)
def getStockEarnings2(refresh_counter) -> pd.DataFrame:
    """
    returns two dataframes, one for the best earning in the past quarter and one for the best predicted earning
    """
    # get data from the past month unless specified to take the entire dataframe
    earnings_query = f"""SELECT * FROM Earnings;"""
    future_earnings_query = f"""SELECT * FROM FutureEarnings"""

    # Query the database and load results into a pandas dataframe
    engine = create_engine(f"mysql+pymysql://{os.environ['ID']}:{os.environ['PASS']}@{os.environ['URL']}/stock_data")
    with engine.connect() as connection:
        earnings = pd.read_sql_query(sql=text(earnings_query), con=connection, parse_dates=['fiscalDateEnding', 'reportedDate']).sort_values(by='fiscalDateEnding', ascending=False)
        future_earnings = pd.read_sql_query(sql=text(future_earnings_query), con=connection, parse_dates=['fiscalDateEnding', 'reportDate']).drop(columns=['currency']).rename(columns={'reportDate': 'reportedDate', 'estimate': 'estimatedEPS'})
    
    combined_earnings = pd.concat([earnings, future_earnings], axis=0, ignore_index=True)
    sorted_earnings = combined_earnings.groupby('stock').apply(lambda x: x.sort_values(by='fiscalDateEnding')).reset_index(drop=True)
    return sorted_earnings

def convert_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Converts the column names of a dataframe to more readable names.
    
    Args:
        df (pd.DataFrame): A dataframe.
    
    Returns:
        pd.DataFrame: A dataframe with the column names converted.
    """
    # replace all spaces with underscores
    df.columns = df.columns.str.replace('_', ' ')
    df.columns = df.columns.str.replace('MA', 'moving average')
    # convert all column names to lowercase
    df.columns = df.columns.str.lower()
    # sort columns by string length
    df = df.reindex(sorted(df.columns, key=len), axis=1)
    df.columns = df.columns.str.replace('adj', 'adjusted')
    return df

st.cache_data(ttl=60*60*24)
def getStockData(refreshes, stock_list=["MSFT"], all_time=False) -> pd.DataFrame:
    """
    returns a dataframe with the stock data for the stocks, as taken from the AWS database.
    the dataframe has the following columns:
    """
    stocks = [f"'{stock}'" for stock in stock_list]
    # get data from the past month unless specified to take the entire dataframe
    query = f"""SELECT * FROM Prices WHERE Prices.Stock IN ({','.join(stocks)});
            """ if all_time else f"""
            SELECT *
            FROM Prices
            WHERE Date >= DATE_SUB(NOW(), INTERVAL 1 MONTH) AND Prices.Stock IN ({','.join(stocks)});
            """
    # Query the database and load results into a pandas dataframe
    engine = create_engine(f"mysql+pymysql://{os.environ['ID']}:{os.environ['PASS']}@{os.environ['URL']}/stock_data")
    with engine.connect() as connection:
        dataframe = pd.read_sql_query(sql=text(query), con=connection, parse_dates=['Date'])

    return dataframe

st.cache_data(ttl=60*60*24)
def getZscore(refreshes, stock_data) -> pd.DataFrame:
    """
    calculates the z-score of the volume of the last day for each stock in the stock_data dataframe
    """
    # convert the volume column to int
    stock_data['volume'] = stock_data['volume'].astype(int)
    # averaged volume of each stock
    mean, std = stock_data.groupby('Stock')['volume'].mean(), stock_data.groupby('Stock')['volume'].std()
    # drop all columns of stock data except for the volume and Stock
    last_day_data = stock_data[['Stock', 'volume', 'Date']].groupby('Stock').last(len(stock_data['Stock'].unique()))
    last_day_data['Stock'] = last_day_data.index
    # subtract the values of volume in stock_data from the mean of the volume of the stock
    last_day_data['Z-score'] = last_day_data.apply(lambda row: (row['volume'] - mean[row['Stock']]) / std[row['Stock']], axis=1)
    return last_day_data

"""

a buncha functions for loading locally stored data
was used for some early testing, not used anymore

old version, doesn't work anymore due to changes in the aws code
@st.cache_data(ttl=60*60*24)
def getSentimentData(refreshes, all_time=False) -> pd.DataFrame:
    ""
    returns a dataframe with the sentiment data for the stocks, as taken from the AWS database.
    the dataframe has the following columns:
    Date, ticker_sentiment_score, ticker_sentiment_label, Stock, source, url, relevance_score
    :param time: the time at which the data was last updated. this is used to check if the cache needs to be updated
    :param time_step: the time step at which the data is aggregated. can be 'Daily', 'Weekly', or 'Monthly'
    ""
    if st.session_state.OFFLINE:
        sentiment_data = pd.read_csv("streamlit_interface/temp_data/sentiment_data.csv", ignore_index=True)
        sentiment_data['time_published'] = pd.to_datetime(sentiment_data['time_published'])
        return sentiment_data
    
    # Connect to the database
    connection = pymysql.connect(
        host=os.environ['URL'],
        user=os.environ['ID'],
        passwd=os.environ['PASS'],
        db="stock_data"
    )
    # get data from the past month unless specified to take the entire dataframe
    query = ""SELECT *
               FROM Sentiments
               WHERE time_published >= DATE_SUB(NOW(), INTERVAL 1 MONTH)
            "" if all_time else ""SELECT * FROM Sentiments""
    # Query the database and load results into a pandas dataframe
    dataframe = pd.read_sql_query(query, connection, parse_dates=['time_published'])
    connection.close()
    # dataframe['time_published'] = pd.to_datetime(dataframe['time_published'])
    dataframe = dataframe.set_index('time_published').sort_index(ascending=False)
    return dataframe

# old version, doesn't work anymore due to changes in the aws code
@st.cache_data(ttl=60*60*24)
def getPastStockPrices(refresh_counter, stock: str = 'MSFT') -> pd.DataFrame:
    ""
    returns a pandas dataframe structured as follows:
    company name, ticker, sentiment score, sentiment magnitude, sentiment score change, sentiment magnitude change
    ""
    if st.session_state.OFFLINE:
        stock_prices = pd.read_csv("streamlit_interface/temp_data/stock_df.csv", index_col="Date")
        # get stock prices of a stock in the Stock column
        stock_prices = stock_prices[stock_prices['Stock'] == str.upper(stock)].drop(columns=['Stock'], errors='ignore')
    else:
        # # specify key and secret key
        # aws_access_key_id = os.environ['DB_ACCESS_KEY']
        # aws_secret_access_key = os.environ['DB_SECRET_KEY']
        # # # create a boto3 client and import all stock prices from it
        # dynamodb = boto3.resource('dynamodb', region_name='us-east-2', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
        # table = dynamodb.Table('StockPrices')
        # # keep scanning until we have all the data in the table
        # # create a filter expression to only get the data for the specified stock
        # response = table.query(KeyConditionExpression=Key('Stock').eq(str.upper(stock)))
        # if len(response['Items']) == 0:
        #     st.write('No data for this stock')
        #     return pd.DataFrame()
        # data = response['Items']
        # # create a progress bar to show the user that the data is being loaded
        # while 'LastEvaluatedKey' in response:
        #     response = table.query(KeyConditionExpression=Key('Stock').eq(stock), ExclusiveStartKey=response['LastEvaluatedKey'])
        #     data.extend(response['Items'])
        #     # show the number of items loaded so far
        #     st.write(len(data))
        # Connect to the database
        connection = pymysql.connect(
            host=os.environ['URL'],
            user=os.environ['ID'],
            passwd=os.environ['PASS'],
            db="stock_data"
        )
        # get data from the past month unless specified to take the entire dataframe
        query = f""SELECT *
                FROM Prices
                WHERE Stock = '{str.upper(stock)}';""
        # Query the database and load results into a pandas dataframe
        data = pd.read_sql_query(query, connection, parse_dates=['Date'])
        connection.close()
        # convert the data to a pandas dataframe and drop the stock column
        stock_prices = pd.DataFrame(data).drop(columns=['Stock'], errors='ignore')
        stock_prices.set_index('Date', inplace=True)
    # convert Date column to datetime
    # stock_prices.index = pd.to_datetime(stock_prices.index)
    # make the index the Date column
    stock_prices.sort_index(ascending=False, inplace=True)
    return stock_prices

_update_interval = datetime.timedelta(days=1)

_recommended_stocks_cache_filename = "recommended_stocks_cache"
_past_accuracy_cache_filename = "past_accuracy_cache"

_datapth = 'temp_data/'
_datetime_format = "%Y-%m-%d %H:%M:%S"
time_step_options = ('Daily', 'Weekly', 'Monthly')
time_deltas = {'Daily': 1, 'Weekly': 7, 'Monthly': 30}


def cache_dec(filename: str):
    # this decorator MUST be used alongside @st.cache_data. this one should come first
    # the function which is decorated should have a 'time' variable, preferabbly with a default value of 'None'.
    def decorator(func):
        def wrapper(*args, **kwargs):
            # if "time" not in kwargs:
            #     raise Exception(f"Invalid use of the cache_dec decorator. {func} must have a time variable")
            cachedata_fname = filename
            if "predgoal" in kwargs:
                cachedata_fname = cachedata_fname + "_" + kwargs["predgoal"]
            time = _checkIfCacheUpdate(cachedata_fname)
            result = func(*args, time = time, **kwargs)
            return result
        return wrapper
    return decorator


def _checkIfCacheUpdate(filename : str) -> datetime.datetime:
    ""
    checks if more than a day has passed since the time stored in filename
    if true, update the time in filename and return the current time
    otherwise, do nothing and return the time stored in filename
    ""
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


@cache_dec(_recommended_stocks_cache_filename)
@st.cache_data
def getRecommendedStocks(predgoal : str = 'Weekly', time : datetime.datetime = None) -> pd.DataFrame:
    ""
    gets as input a string detailing prediction targer, must be in the set time_step_options
    returns a pandas dataframe structured as follows:
    company name, ticker, model predictions, past accuracy for this stock
    
    if less than a day has passed since the last call to this function, the cached result will be used
    ""
    if predgoal not in time_step_options:
        return None
    # (I took this from https://www.nasdaq.com/, it's just the top 5 I sawthere)
    # this if statement should actually do different stuff based on predgoal
    if predgoal == time_step_options[0]:
        return pd.read_csv(os.path.join(os.path.dirname(os.path.realpath(__file__)), _datapth, 'daily_recommendations.csv'))
    if predgoal == time_step_options[1]:
        return pd.read_csv(os.path.join(os.path.dirname(os.path.realpath(__file__)), _datapth, 'weekly_recommendations.csv'))
    return pd.read_csv(os.path.join(os.path.dirname(os.path.realpath(__file__)), _datapth, 'monthly_recommendations.csv'))


@cache_dec(_past_accuracy_cache_filename)
@st.cache_data
def getPastAccuracy(time_back: int = 100, time : datetime.datetime = None) -> pd.DataFrame:
    ""
    returns a pandas dataframe listing the accuracy of the model in the past for each type of prediction
    the input is how many days back from right now you want it to show
    
    if less than a day has passed since the last call to this function, the cached result will be used
    ""
    return pd.read_csv(os.path.join(os.path.dirname(os.path.realpath(__file__)), _datapth, 'past_accuracy.csv'))
"""
