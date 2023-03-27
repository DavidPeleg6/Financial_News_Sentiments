import streamlit as st
import pandas as pd
import datetime
import os
import pymysql
from sqlalchemy import create_engine


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

@st.cache_data(ttl=60*60*24)
def getSentimentData(refreshes, all_time=False) -> pd.DataFrame:
    """
    returns a dataframe with the sentiment data for the stocks, as taken from the AWS database.
    the dataframe has the following columns:
    Date, ticker_sentiment_score, ticker_sentiment_label, Stock, source, url, relevance_score
    :param time: the time at which the data was last updated. this is used to check if the cache needs to be updated
    :param time_step: the time step at which the data is aggregated. can be 'Daily', 'Weekly', or 'Monthly'
    """
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
    query = """SELECT *
               FROM Sentiments
               WHERE time_published >= DATE_SUB(NOW(), INTERVAL 1 MONTH)
            """ if all_time else """SELECT * FROM Sentiments"""
    # Query the database and load results into a pandas dataframe
    dataframe = pd.read_sql_query(query, connection)
    connection.close()
    dataframe['time_published'] = pd.to_datetime(dataframe['time_published'])
    dataframe = dataframe.set_index('time_published').sort_index(ascending=False)
    return dataframe


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

# add download button
st.download_button('Download raw sentiment data', sentiment_ticker_list.to_csv(), 'sentiment_data.csv', 'text/csv')
