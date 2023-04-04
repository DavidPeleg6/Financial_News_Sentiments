import streamlit as st
import pandas as pd
import datetime
import os
from sqlalchemy import create_engine, text

st.set_page_config(layout="wide")

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
except FileNotFoundError:
    pass

# st.session_state.OFFLINE = False

@st.cache_data(ttl=60*60*24)
def getSentimentData(refreshes, all_time=False) -> pd.DataFrame:
    """
    returns a dataframe with the sentiment data for the stocks, as taken from the AWS database.
    the dataframe has the following columns:
    Date, ticker_sentiment_score, ticker_sentiment_label, Stock, source, url, relevance_score
    :param time: the time at which the data was last updated. this is used to check if the cache needs to be updated
    :param time_step: the time step at which the data is aggregated. can be 'Daily', 'Weekly', or 'Monthly'
    """
    # if st.session_state.OFFLINE:
    #     sentiment_data = pd.read_csv("streamlit_interface/temp_data/sentiment_data.csv", ignore_index=True)
    #     sentiment_data['time_published'] = pd.to_datetime(sentiment_data['time_published'])
    #     return sentiment_data
    
    # get data from the past month unless specified to take the entire dataframe
    query = """SELECT *
               FROM Sentiments
               WHERE time_published >= DATE_SUB(NOW(), INTERVAL 1 MONTH)
            """ if not all_time else """SELECT * FROM Sentiments"""
    
    # Query the database and load results into a pandas dataframe
    engine = create_engine(f"mysql+pymysql://{os.environ['ID']}:{os.environ['PASS']}@{os.environ['URL']}/stock_data", echo=False)
    with engine.connect() as connection:
        dataframe = pd.read_sql_query(sql=text(query), con=connection, parse_dates=['time_published']).set_index('time_published').sort_index(ascending=False)
    
    return dataframe


st.cache_data(ttl=60*60*24)
def getStockData(refreshes, stock_list=["MSFT"], all_time=False) -> pd.DataFrame:
    """
    returns a dataframe with the stock data for the stocks, as taken from the AWS database.
    the dataframe has the following columns:
    """
    stocks = [f"'{stock}'" for stock in stock_list]
    # get data from the past month unless specified to take the entire dataframe
    query = f"""SELECT * FROM Prices WHERE Prices.Stock IN ({','.join(stocks)});
            """ if all_time else f"""
            SELECT *
            FROM Prices
            WHERE Date >= DATE_SUB(NOW(), INTERVAL 1 MONTH) AND Prices.Stock IN ({','.join(stocks)});
            """
    # Query the database and load results into a pandas dataframe
    engine = create_engine(f"mysql+pymysql://{os.environ['ID']}:{os.environ['PASS']}@{os.environ['URL']}/stock_data")
    with engine.connect() as connection:
        dataframe = pd.read_sql_query(sql=text(query), con=connection, parse_dates=['Date'])

    return dataframe


st.cache_data(ttl=60*60*24)
def getZscore(refreshes, stock_data) -> pd.DataFrame:
    """
    calculates the z-score of the volume of the last day for each stock in the stock_data dataframe
    """
    # convert the volume column to int
    stock_data['volume'] = stock_data['volume'].astype(int)
    # averaged volume of each stock
    mean, std = stock_data.groupby('Stock')['volume'].mean(), stock_data.groupby('Stock')['volume'].std()
    # drop all columns of stock data except for the volume and Stock
    last_day_data = stock_data[['Stock', 'volume', 'Date']].groupby('Stock').last(len(stock_data['Stock'].unique()))
    last_day_data['Stock'] = last_day_data.index
    # subtract the values of volume in stock_data from the mean of the volume of the stock
    last_day_data['Z-score'] = last_day_data.apply(lambda row: (row['volume'] - mean[row['Stock']]) / std[row['Stock']], axis=1)
    return last_day_data


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
