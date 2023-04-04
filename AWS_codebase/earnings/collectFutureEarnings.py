from sqlalchemy import create_engine, text
import pymysql
import sqlalchemy
import os
import pandas as pd
import io
import requests
import random
import string
import time


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
            return response


def lambda_handler(event, context):
    # get data regarding all stocks in the Prices table
    query = text("""SELECT DISTINCT Stock FROM Prices;""")
    # Query the database and load results into a pandas dataframe
    engine = create_engine(f"mysql+pymysql://{os.environ['ID']}:{os.environ['PASS']}@{os.environ['URL']}/stock_data", echo=False)
    with engine.connect() as connection:
        dataframe = pd.read_sql_query(sql=query, con=connection)
    
    sorted_tickers = sorted(dataframe['Stock'].tolist())
    function = 'EARNINGS_CALENDAR'
    future_earnings = get_data({"function": function, "horizon": "3month"})
    future_earnings_df = pd.read_csv(io.StringIO(future_earnings.text)).rename(columns={'symbol': 'stock'}).drop(columns=['name']).drop_duplicates(subset=['stock'])
    # convert to datetime
    future_earnings_df['reportDate'] = pd.to_datetime(future_earnings_df['reportDate'])
    future_earnings_df['fiscalDateEnding'] = pd.to_datetime(future_earnings_df['fiscalDateEnding'])
    # only take tickers that are in sorted_tickers
    future_earnings_df = future_earnings_df[future_earnings_df['stock'].isin(sorted_tickers)].set_index('stock')
    
    dtypes = {
    'fiscalDateEnding': sqlalchemy.types.DATETIME,
    'reportDate': sqlalchemy.types.DATETIME,
    'stock': sqlalchemy.types.VARCHAR(10),
    'estimate': sqlalchemy.types.DECIMAL(15,2),
    'currency': sqlalchemy.types.VARCHAR(10)
    }
    url, username, password = os.environ['URL'], os.environ['ID'], os.environ['PASS']
    # Establish connection to the MySQL database
    with pymysql.connect(host=url, user=username, password=password, db='stock_data') as conn:
        engine = create_engine(f'mysql+pymysql://{username}:{password}@{url}/stock_data', echo=False)
        try:
            future_earnings_df.to_sql(name='FutureEarnings', con=engine, if_exists='replace', index=True, index_label='stock', dtype=dtypes)
        except Exception as e:
            pass

    time.sleep(10) 
    query = text("ALTER TABLE FutureEarnings ADD PRIMARY KEY (stock(10));")
    # run a query to alter the table
    engine = create_engine(f"mysql+pymysql://{os.environ['ID']}:{os.environ['PASS']}@{os.environ['URL']}/stock_data", echo=False)
    with engine.connect() as connection:
        connection.execute(query)
       
    return {
        'statusCode': 200,
        'body': "success"
    }
