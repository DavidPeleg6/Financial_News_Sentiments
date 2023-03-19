import streamlit as st
import pandas as pd # REMOVE THIS LATER, YOU'RE NOT SUPPOSED TO DIRECTLY USE THAT HERE
import datetime
import os
import boto3


_OFFLINE_DATA = False
time_step_options = ('Daily', 'Weekly', 'Monthly')
time_deltas = {'Daily': 1, 'Weekly': 7, 'Monthly': 30}
refresh_counter = 0
if 'sentiment_refresh' not in st.session_state:
    st.session_state.sentiment_refresh = 0

# try loading DB_ACCESS_KEY from csv file - useful when you run the app locally
try:
    DB_ACCESS_KEY = pd.read_csv('DB_ACCESS_KEY.csv')
    os.environ['DB_ACCESS_KEY'] = DB_ACCESS_KEY['Access key ID'][0]
    os.environ['DB_SECRET_KEY'] = DB_ACCESS_KEY['Secret access key'][0]
    st.session_state.OFFLINE = True
except FileNotFoundError:
    st.session_state.OFFLINE = False


@st.cache_data(ttl=60*60*24)
def getSentimentData(refreshes) -> pd.DataFrame:
    """
    returns a dataframe with the sentiment data for the stocks, as taken from the AWS database.
    the dataframe has the following columns:
    Date, ticker_sentiment_score, ticker_sentiment_label, Stock, source, url, relevance_score
    :param time: the time at which the data was last updated. this is used to check if the cache needs to be updated
    :param time_step: the time step at which the data is aggregated. can be 'Daily', 'Weekly', or 'Monthly'
    """
    if st.session_state.OFFLINE:
        sentiment_data = pd.read_csv("temp_data/sentiment_data.csv", index_col="Date")
        sentiment_data.index = pd.to_datetime(sentiment_data.index)
        return sentiment_data
    
    # specify key and secret key
    aws_access_key_id = os.environ['DB_ACCESS_KEY']
    aws_secret_access_key = os.environ['DB_SECRET_KEY']
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-2', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
    table = dynamodb.Table('StockSentiment')
    # keep scanning until we have all the data in the table
    response = table.scan()
    data = response['Items']
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])
    # convert the data to a pandas dataframe
    sentiment_ticker_list = pd.DataFrame(data)
    # convert Date column to datetime
    sentiment_ticker_list['Date'] = pd.to_datetime(sentiment_ticker_list['Date'])
    # make the index the Date column
    sentiment_ticker_list = sentiment_ticker_list.set_index('Date').sort_index(ascending=False)
    return sentiment_ticker_list


# set to wide mode
st.set_page_config(layout="wide")
refresh_sentiments = st.button('Refresh')
if refresh_sentiments:
    st.session_state.sentiment_refresh += 1
    refresh_counter = st.session_state.sentiment_refresh
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

sentiment_ticker_list = getSentimentData(refresh_counter)
# convert data type to float
sentiment_ticker_list['ticker_sentiment_score'] = pd.to_numeric(sentiment_ticker_list['ticker_sentiment_score'])
# add download button
st.download_button('Download sentiment data', sentiment_ticker_list.to_csv(), 'sentiment_data.csv', 'text/csv')
# get only the data for the last 30 days
sentiment_data = sentiment_ticker_list.loc[sentiment_ticker_list.index >= (datetime.datetime.now() - datetime.timedelta(days=time_deltas[timeframe]))]
top_stocks = sentiment_data['Stock'].value_counts().head(number_of_stocks)
# create a histogram where the x axis is the stock name and the y axis is the frequency, make the chart sorted by frequency
st.write('Number of stock mentions')
st.bar_chart(data = top_stocks, use_container_width = True)

# get a subset of the sentiment data that only contains the most frequently mentioned stocks
top_sentiment_data = sentiment_data[sentiment_data['Stock'].isin(top_stocks.index)]

# get the mean sentiment score for each stock
st.write('Average sentiment score')
st.bar_chart(data = top_sentiment_data.groupby('Stock')['ticker_sentiment_score'].mean(), use_container_width = True)

# get the input from the user
st.write('Choose custom stock')
stock_ticker = st.text_input(label = 'INPUT_STOCK', value = 'AAPL', key = None, type = 'default', help = None, on_change = None, args = None, kwargs = None)
# get the sentiment data for the stock the user chose
stock_sentiment_data = sentiment_ticker_list[sentiment_ticker_list['Stock'] == str.upper(stock_ticker)]
# drop the hour from the index column
stock_sentiment_data.index = stock_sentiment_data.index.strftime('%Y-%m-%d')
# create a table containing the daily mean sentiment score for the stock the user chose
sentiment_over_time = stock_sentiment_data.groupby('Date')['ticker_sentiment_score'].mean()
# plot the table
st.write('Mean sentiment score over time')
st.line_chart(data = sentiment_over_time, use_container_width = True)
