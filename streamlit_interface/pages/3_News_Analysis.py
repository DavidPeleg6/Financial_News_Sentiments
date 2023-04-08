import streamlit as st
import pandas as pd
import datetime
from dataLoader import getStockData, getZscore, getSentimentData

st.set_page_config(layout="wide")

time_step_options = ('Daily', 'Weekly', 'Monthly', 'All Time')
time_deltas = {'Daily': 1, 'Weekly': 7, 'Monthly': 30, 'All Time': 365*20}
if 'sentiment_refresh' not in st.session_state:
    st.session_state.sentiment_refresh = 0

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

# ------------------------------------- Get top sentiments and their values -------------------------------------
sentiment_ticker_list = getSentimentData(st.session_state.sentiment_refresh, timeframe=='All Time')
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


# ------------------------------------- Get the change in volumes for each of the most trending stocks -------------------------------------
st.subheader('Trading volumes of the last day (higher = more volume than average)')
# get the top stocks
stock_data = getStockData(st.session_state.sentiment_refresh, top_stocks.index.to_list(), timeframe=='All Time')
stock_data = stock_data.loc[stock_data.Date >= (datetime.datetime.now() - datetime.timedelta(days=time_deltas['Monthly']))]
last_day_data = getZscore(st.session_state.sentiment_refresh, stock_data)
# create a st table with the values of volume, where each value is color coded from red to green depending on the standard deviation column. where -1 is most red and 1 is most green
st.bar_chart(data = last_day_data['Z-score'], use_container_width = True)


# ------------------------------------- Get a list of articles for a chosen stock -------------------------------------
st.subheader(f'Most trending articles:')
# get the input from the user
stock_ticker = st.text_input(label = 'Type stock ticker below', value = 'AAPL')
# get the sentiment data for the stock the user chose
stock_sentiment_data = sentiment_data[sentiment_data['stock'] == str.upper(stock_ticker)]
# drop the hour from the index column
stock_sentiment_data.index = stock_sentiment_data.index.strftime('%Y-%m-%d')
# get the top 10 rows with the highest relevance_score. filter out only articles that have a relevance score of at least 0.5
top_articles = stock_sentiment_data[(stock_sentiment_data['relevance_score'] >= 0.3) & abs(stock_sentiment_data['sentiment'] >= 0.2)].sort_values(by='relevance_score', ascending=False).head(10)

# create a list in st of urls to the articles
for url in top_articles['article_url']:
    # parse out the name of the article from the url
    article_name = ' '.join(url.split('/')[-1].split('-'))
    # create a link to the article, where the name is the name of the article
    st.write(f'[{article_name}]({url})')

# ------------------------------------- Get the change in sentiment over time for a chosen stock -------------------------------------
if timeframe != 'Daily':
    st.subheader(f'{stock_ticker} mean sentiment score over time')
    # create a table containing the daily mean sentiment score for the stock the user chose
    sentiment_over_time = stock_sentiment_data.groupby('time_published')['sentiment'].mean()
    # plot the table
    st.line_chart(data = sentiment_over_time, use_container_width = True)

# add download button
st.download_button('Download raw sentiment data', sentiment_ticker_list.to_csv(), 'sentiment_data.csv', 'text/csv')