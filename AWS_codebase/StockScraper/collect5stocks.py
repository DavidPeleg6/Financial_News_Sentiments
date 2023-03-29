from external_api_comm import get_stockprice, convert_dict_to_df
import pandas as pd
import os
import pymysql
import sqlalchemy

# the number of days to look back
TIME_BACK = 15
# TIME_BACK = 365*2


def lambda_handler(event, context):
    write_stocks(event['body'])


def write_stocks(stock_list):
    stocks_to_watch = [str.upper(stock) for stock in stock_list]
    failed_stocks = []
    df = pd.DataFrame()
    # iterate over all stocks and log into database
    for stock in stocks_to_watch:
        # get stockprice from alpha vantage
        json_stock_data = get_stockprice(stock)
        if json_stock_data is None or 'Time Series (Daily)' not in json_stock_data: 
            failed_stocks.append(stock)
            continue
        # convert stock data into a dataframe and add indicators and take only 2 years back
        stocks_df = convert_dict_to_df(stock, json_stock_data['Time Series (Daily)'], TIME_BACK)
        # rename the columns of the stocks_df
        stocks_df = stocks_df.rename(columns={'stock': 'Stock'})
        stocks_df['Date'] = pd.to_datetime(stocks_df.index)
        # concatenate all the rows of the stocks_df to the df
        df = pd.concat([df, stocks_df], ignore_index=True)
    # convert Date column to datetime
    df = df.set_index(['Stock','Date'])

    #-------------------------------------------- WRITE TO DATABASE ---------------------------------------------------#
    dtypes = {column_name: sqlalchemy.types.DECIMAL(10,2) for column_name in df.columns if column_name not in ('Date', 'Stock')}
    dtypes['Date'] = sqlalchemy.types.DATETIME
    dtypes['Stock'] = sqlalchemy.types.VARCHAR(10)
    url, username, password = os.environ['URL'], os.environ['ID'], os.environ['PASS']
    # Establish connection to the MySQL database
    conn = pymysql.connect(host=url, user=username, password=password, db='stock_data')
    # Create a SQLAlchemy engine object
    engine = sqlalchemy.create_engine(f'mysql+pymysql://{username}:{password}@{url}/stock_data', echo=False)
    for i in range(len(df)):
        try:
            df.iloc[i:i+1].to_sql(name='Prices', con=engine, if_exists='append', index=True, index_label=['Stock', 'Date'], dtype=dtypes)
        except Exception as e:
            print(e)
            pass
    # Close the connection
    conn.close()

    return failed_stocks
