import requests
import pandas as pd
import time
import string
import random
from datetime import datetime, timedelta
import sqlalchemy
import pymysql
import os


def get_data(parameters):
    """
    Get data from the API endpoint.
    """
    endpoint = "https://www.alphavantage.co/query"
    for _ in range(100):
        parameters['apikey'] = ''.join(random.choices(string.ascii_uppercase + string.digits, k=15))
        # Send a GET request to the API endpoint
        response = requests.get(endpoint, params=parameters)
        # Check if the request was successful
        if response.status_code == 200:
            return response.json()


def lambda_handler(event, context):
    # ---------------------------------------------- GET THE DATA ----------------------------------------------
    # functions = ['OVERVIEW', 'INCOME_STATEMENT', 'BALANCE_SHEET', 'CASH_FLOW', 'EARNINGS']
    function = 'EARNINGS'
    companies = [str.upper(stock) for stock in event['body']]
    df = pd.DataFrame()
    for company in companies:
        earnings = get_data({"function": function, "symbol": company})
        earnings = pd.DataFrame(earnings['quarterlyEarnings']).drop(columns=['surprise'])
        # add a column with the stock symbol
        earnings['stock'] = company
        # convert the date column to datetime from format YYYY-MM-DD
        earnings['reportedDate'] = pd.to_datetime(earnings['reportedDate'])
        earnings['fiscalDateEnding'] = pd.to_datetime(earnings['fiscalDateEnding'])
        # take only the data up to 2 years ago and convert to numeric
        earnings = earnings[earnings['reportedDate'] >= datetime.now() - timedelta(days=2*365)].sort_index(ascending=False)
        df = pd.concat([df, earnings], ignore_index=True)

    # ---------------------------------------------- WRITE DATA TO DB ----------------------------------------------
    dtypes = {
        'fiscalDateEnding': sqlalchemy.types.DATETIME,
        'reportedDate': sqlalchemy.types.DATETIME,
        'stock': sqlalchemy.types.VARCHAR(10),
        'reportedEPS': sqlalchemy.types.DECIMAL(15,2),
        'estimatedEPS': sqlalchemy.types.DECIMAL(15,2),
        'surprise': sqlalchemy.types.DECIMAL(15,2)
        }
    url, username, password = os.environ['URL'], os.environ['ID'], os.environ['PASS']
    # Establish connection to the MySQL database
    with pymysql.connect(host=url, user=username, password=password, db='stock_data') as conn:
        # Create a SQLAlchemy engine object
        engine = sqlalchemy.create_engine(f'mysql+pymysql://{username}:{password}@{url}/stock_data', echo=False)
        for stock in companies:
            # for collecting all previous data
            sub_df = df[df['stock'] == stock].set_index(['stock','fiscalDateEnding'])
            # for colleccting only the latest data
            # sub_df = df[df['stock'] == stock].iloc[0:1].set_index(['stock','fiscalDateEnding'])
            try:
                sub_df.to_sql(name='Earnings', con=engine, if_exists='append', index=True, index_label=['stock', 'fiscalDateEnding'], dtype=dtypes)
            except Exception:
                print(f'exception on {stock}')
                continue