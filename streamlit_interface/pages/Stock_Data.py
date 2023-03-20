import streamlit as st
import pandas as pd # REMOVE THIS LATER, YOU'RE NOT SUPPOSED TO DIRECTLY USE THAT HERE
import datetime
import os
import boto3
from boto3.dynamodb.conditions import Key, Attr
import plotly.express as px


_OFFLINE_DATA = False
time_step_options = ('Daily', 'Weekly', 'Monthly')
time_deltas = {'Daily': 1, 'Weekly': 7, 'Monthly': 30}
refresh_counter = 0
if 'stock_refresh' not in st.session_state:
    st.session_state.stock_refresh = 0

# try loading DB_ACCESS_KEY from csv file - useful when you run the app locally
try:
    DB_ACCESS_KEY = pd.read_csv('DB_ACCESS_KEY.csv')
    os.environ['DB_ACCESS_KEY'] = DB_ACCESS_KEY['Access key ID'][0]
    os.environ['DB_SECRET_KEY'] = DB_ACCESS_KEY['Secret access key'][0]
    st.session_state.OFFLINE = True
except FileNotFoundError:
    st.session_state.OFFLINE = False


@st.cache_data(ttl=60*60*24)
def getPastStockPrices(refresh_counter, stock: str = 'MSFT') -> pd.DataFrame:
    """
    returns a pandas dataframe structured as follows:
    company name, ticker, sentiment score, sentiment magnitude, sentiment score change, sentiment magnitude change
    """
    if _OFFLINE_DATA:
        return pd.read_csv("temp_data/stock_df.csv", index_col="Date")
    # specify key and secret key
    aws_access_key_id = os.environ['DB_ACCESS_KEY']
    aws_secret_access_key = os.environ['DB_SECRET_KEY']
    # # create a boto3 client and import all stock prices from it
    dynamodb = boto3.resource('dynamodb', region_name='us-east-2', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
    table = dynamodb.Table('StockPrices')
    # keep scanning until we have all the data in the table
    # create a filter expression to only get the data for the specified stock
    response = table.query(KeyConditionExpression=Key('Stock').eq(str.upper(stock)))
    if len(response['Items']) == 0:
        st.write('No data for this stock')
        return pd.DataFrame()
    data = response['Items']
    # create a progress bar to show the user that the data is being loaded
    while 'LastEvaluatedKey' in response:
        response = table.query(KeyConditionExpression=Key('Stock').eq(stock), ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])
        # show the number of items loaded so far
        st.write(len(data))
    # convert the data to a pandas dataframe
    stock_prices = pd.DataFrame(data)
    # convert Date column to datetime
    stock_prices['Date'] = pd.to_datetime(stock_prices['Date'])
    # make the index the Date column
    stock_prices = stock_prices.set_index('Date').sort_index(ascending=False)
    return stock_prices


# set to wide mode
st.set_page_config(layout="wide")
refresh_stocks = st.button('Refresh')
if refresh_stocks:
    st.session_state.stock_refresh += 1
    refresh_counter = st.session_state.stock_refresh
st.header('Basic Stock Data')

stock_ticker = st.text_input(label = 'INPUT_STOCK', value = 'AAPL', label_visibility='hidden')
stock_data = getPastStockPrices(refresh_counter, stock_ticker)
if not stock_data.empty:
    # drop the Stock column
    stock_data = stock_data.drop(columns=['Stock'])
    # convert all the columns to floats except for the index column
    stock_data = stock_data.astype(float)
    # create a dataframe out of the first row of the stock data
    st.dataframe(stock_data.iloc[0])
    # create checkboxes for each column in the stock data, with default being close
    checkboxes = st.multiselect('Select indicators to plot', stock_data.columns, default=['close'])
    # create a plotly blank figure
    fig = px.line()
    for column in checkboxes:
        # add each column to the plotly figure
        fig.add_scatter(x=stock_data.index, y=stock_data[column], name=column)
    # # create a plotly chart of the stock data
    # # create a plotly figure
    # fig = px.line(stock_data, x=stock_data.index, y='close')
    # # add to the same plot the open price as a function of time
    # fig.add_scatter(x=stock_data.index, y=stock_data['open'])
    # # add to the same plot the high price as a function of time
    # fig.add_scatter(x=stock_data.index, y=stock_data['high'])
    # # add to the same plot the low price as a function of time
    # fig.add_scatter(x=stock_data.index, y=stock_data['low'])

    # # plot the close price as a function of time
    # px.line(stock_data, x=stock_data.index, y='close')
    # # add to the same plot the open price as a function of time
    # px.line(stock_data, x=stock_data.index, y='open')

    st.plotly_chart(fig, use_container_width=True)

