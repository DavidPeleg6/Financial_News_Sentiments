import streamlit as st
import pandas as pd
import datetime
import os

import sys
 # setting path
sys.path.append('../streamlit_interface')
 # importing
from dataLoader import getSentimentData
# from sqlalchemy import create_engine


time_step_options = ('Daily', 'Weekly', 'Monthly', 'All Time')
time_deltas = {'Daily': 1, 'Weekly': 7, 'Monthly': 30, 'All Time': 365*20}
if 'sentiment_refresh' not in st.session_state:
    st.session_state.sentiment_refresh = 0

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

refresh_sentiments = st.button('Refresh')
if refresh_sentiments:
    st.session_state.sentiment_refresh += 1
st.header('Sentiment Analysis of News Articles')

timeframe = st.selectbox(
    label = 'stock_date',
    options = time_step_options,
    index = 1, label_visibility='hidden')

number_of_stocks = st.slider(
    label = 'stock_num',
    min_value = 5,
    max_value = 40,
    value = 20,
    step = 1, label_visibility='hidden')
# add another slider but hide min max values

sentiment_ticker_list = getSentimentData(st.session_state.sentiment_refresh, timeframe!='All Time')
# convert data type to float
sentiment_ticker_list['sentiment'] = pd.to_numeric(sentiment_ticker_list['sentiment'])

# get only the data for the last 30 days
sentiment_data = sentiment_ticker_list.loc[sentiment_ticker_list.index >= (datetime.datetime.now() - datetime.timedelta(days=time_deltas[timeframe]))]
top_stocks = sentiment_data['stock'].value_counts().head(number_of_stocks)
# create a histogram where the x axis is the stock name and the y axis is the frequency, make the chart sorted by frequency
st.subheader('Most frequently mentioned stocks')
st.bar_chart(data = top_stocks, use_container_width = True)

# get a subset of the sentiment data that only contains the most frequently mentioned stocks
top_sentiment_data = sentiment_data[sentiment_data['stock'].isin(top_stocks.index)]

# get the mean sentiment score for each stock
st.subheader('Average sentiment of most trending stocks (bullish = 1, bearish = -1)')
st.bar_chart(data = top_sentiment_data.groupby('stock')['sentiment'].mean(), use_container_width = True)

st.subheader('Mean sentiment score over time')
# get the input from the user
stock_ticker = st.text_input(label = 'Type stock ticker below', value = 'AAPL')
# get the sentiment data for the stock the user chose
stock_sentiment_data = sentiment_ticker_list[sentiment_ticker_list['stock'] == str.upper(stock_ticker)]
# drop the hour from the index column
stock_sentiment_data.index = stock_sentiment_data.index.strftime('%Y-%m-%d')
# create a table containing the daily mean sentiment score for the stock the user chose
sentiment_over_time = stock_sentiment_data.groupby('time_published')['sentiment'].mean()
# plot the table
st.line_chart(data = sentiment_over_time, use_container_width = True)

# in preperation for the last feature of volume x sentiment, here is the query to be used
"""SELECT prices.stock_name FROM prices 
WHERE prices.stock_name IN ('stock1', 'stock2', ...) 
AND prices.volume > (SELECT AVG(prices.volume)*1.1 FROM prices.stocks);"""


# add download button
st.download_button('Download raw sentiment data', sentiment_ticker_list.to_csv(), 'sentiment_data.csv', 'text/csv')
