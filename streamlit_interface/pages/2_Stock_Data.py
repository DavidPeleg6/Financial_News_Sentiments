import streamlit as st
import pandas as pd 
import os
import plotly.express as px


import sys
 # setting path
sys.path.append('../streamlit_interface')
 # importing
from dataLoader import getPastStockPrices, convert_column_names

if 'stock_refresh' not in st.session_state:
    st.session_state.stock_refresh = 0

# try loading DB_ACCESS_KEY from csv file - useful when you run the app locally
try:
    DB_ACCESS_KEY = pd.read_csv('streamlit_interface/db_key_pass.csv')
    os.environ['ID'] = DB_ACCESS_KEY['ID'][0]
    os.environ['PASS'] = DB_ACCESS_KEY['PASS'][0]
    os.environ['URL'] = DB_ACCESS_KEY['URL'][0]
    st.session_state.OFFLINE = True
except FileNotFoundError:
    st.session_state.OFFLINE = False

st.session_state.OFFLINE = False

refresh_stocks = st.button('Refresh')
if refresh_stocks:
    st.session_state.stock_refresh += 1
st.header('Basic Stock Data')

stock_ticker = st.text_input(label = 'Type ticker symbol below', value = 'AAPL')
stock_data = getPastStockPrices(st.session_state.stock_refresh, stock_ticker)
if not stock_data.empty:
    stock_data = convert_column_names(stock_data)
    # convert all the columns to floats except for the index column
    stock_data = stock_data.astype(float)
    # create a dataframe out of the first row of the stock data
    daily_data = pd.DataFrame(stock_data.iloc[0]).T
    # create 3 columns
    col1, col2, col3 = st.columns(3)
    # in column 1, place a table of open, close, adjusted close, high, low, volume, split, and dividend. with 2 points of precision
    col1.subheader('Daily Data')
    col1.table(daily_data[['open', 'close', 'adjusted close', 'high', 'low', 'volume', 'split', 'dividend']].T.style.format('{:.1f}'))
    # in column 2, place the 4 week low, 4 week high, 10 week low, 10 week high, 52 week low and 52 week high
    col2.subheader('Historic highs and lows')
    col2.table(daily_data[['4 week low', '4 week high', '10 week low', '10 week high', '52 week low', '52 week high']].T.style.format('{:.1f}'))
    # in column 3, place the 30 day moving average, 50 day moving average, 100 day moving average and 200 day moving average
    col3.subheader('Moving averages')
    col3.table(daily_data[['30 day moving average', '50 day moving average', '100 day moving average', '200 day moving average']].T.style.format('{:.1f}'))
    # create checkboxes for each column in the stock data, with default being close
    checkboxes = st.multiselect('Select indicators to plot', stock_data.columns, default=['close'])
    # create a plotly blank figure
    fig = px.line()
    for column in checkboxes:
        # add each column to the plotly figure
        fig.add_scatter(x=stock_data.index, y=stock_data[column], name=column)

    st.plotly_chart(fig, use_container_width=True)

    # TODO add the earnings stock data histograms pulled from the database
    # add download button
    st.download_button('Download raw stock data', stock_data.to_csv(), f'{stock_ticker}_data.csv', 'text/csv')

else:
    st.subheader('No data for this stock exists in the database')