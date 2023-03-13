import streamlit as st
import pandas as pd # REMOVE THIS LATER, YOU'RE NOT SUPPOSED TO DIRECTLY USE THAT HERE
from dataLoader import getSentimentData, time_step_options

# set to wide mode
st.set_page_config(layout="wide")
st.header('Sentiment Analysis of News Articles')
timeframe = st.selectbox(
    label = '',
    options = time_step_options,
    index = 1, label_visibility='hidden')

number_of_stocks = st.slider(
    label = '',
    min_value = 5,
    max_value = 40,
    value = 20,
    step = 1, label_visibility='hidden')
# add another slider but hide min max values

sentiment_data = getSentimentData(time_step=timeframe)
top_stocks = sentiment_data['Stock'].value_counts().head(number_of_stocks)
# st.dataframe(data=top_stocks)
# get a subset of the sentiment data that only contains the top stocks
top_sentiment_data = sentiment_data[sentiment_data['Stock'].isin(top_stocks.index)]
# create a histogram where the x axis is the stock name and the y axis is the frequency, make the chart sorted by frequency
st.write('Number of stock mentions')
st.bar_chart(data = top_stocks, use_container_width = True)
# get the mean sentiment score for each stock
st.write('Average sentiment score')
st.bar_chart(data = top_sentiment_data.groupby('Stock')['ticker_sentiment_score'].mean(), use_container_width = True)

# get the input from the user
st.write('Choose custom stock')
stock_ticker = st.text_input(label = '', value = 'AAPL', key = None, type = 'default', help = None, on_change = None, args = None, kwargs = None)
# get the sentiment data for the stock the user chose
stock_sentiment_data = sentiment_data[sentiment_data['Stock'] == stock_ticker]
st.dataframe(stock_sentiment_data.groupby('Date')['ticker_sentiment_score'].mean())
# get the mean of sentiment score over the entire day
st.header('todo - add a line chart that shows the sentiment score over time for the stock the user chose')