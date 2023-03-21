import streamlit as st
import pandas as pd # REMOVE THIS LATER, YOU'RE NOT SUPPOSED TO DIRECTLY USE THAT HERE
import numpy as np # REMOVE THIS LATER, YOU'RE NOT SUPPOSED TO DIRECTLY USE THAT HERE
import os
import xgboost
import boto3
from boto3.dynamodb.conditions import Key
import plotly.express as px
from pages.Stock_Data import getPastStockPrices, convert_column_names
from typing import Dict
import xgboost as xgb


# # set to wide mode
# st.set_page_config(layout="wide")
# try loading DB_ACCESS_KEY from csv file - useful when you run the app locally
try:
    DB_ACCESS_KEY = pd.read_csv('DB_ACCESS_KEY.csv')
    # TODO ADD the flag update of offline here
    # _OFFLINE_DATA = True
    # set the environment variable
    os.environ['DB_ACCESS_KEY'] = DB_ACCESS_KEY['Access key ID'][0]
    os.environ['DB_SECRET_KEY'] = DB_ACCESS_KEY['Secret access key'][0]
    st.session_state.OFFLINE = True
except FileNotFoundError:
    st.session_state.OFFLINE = False

st.title('Financial Stock Recommendation System')

st.write('This is a stock recommendation system that uses a combination of machine learning and news sentiment analysis to recommend stocks to buy.')
# st.write('The recommendation system is still under development, so the results are not guaranteed to be accurate. in the meantime, you can use the navigation bar on the left to explore the other features of the app.')

time_step_options = ('Daily', 'Weekly', 'Monthly')
time_deltas = {'Daily': 1, 'Weekly': 7, 'Monthly': 30}
if 'recomm_refresh' not in st.session_state:
    st.session_state.recomm_refresh = 0

refresh_stocks = st.button('Refresh')
if refresh_stocks:
    st.session_state.recomm_refresh += 1


def preprocess(stock_df: pd.DataFrame):
    df = stock_df.copy()
    # sort the dataframe by date
    df.sort_index(ascending=False, inplace=True)
    # get the first row of the dataframe
    first_row = df.iloc[0]
    # raise the all the columns up by one day so that the model only gets the daily open price and the rest of the data from yesterday
    for col in set(df.columns) - {'close', 'open'}: df[col] = df[col][1:].shift(-1)
    # shift the close column by 1
    df['close'] = df['close'][:-1]
    df = df.dropna(axis=0)

    df.index = pd.to_datetime(df.index)
    df.sort_index(ascending=False, inplace=True)
    # convert all columns to numeric except for the index
    df = df.apply(pd.to_numeric, errors='ignore')
    # drop any column that contains a date time value
    # df = df.drop(columns=[col for col in df.columns if df[col].dtype != 'float64']).dropna()
    df = df.dropna(axis=0)
    return df


@st.cache_data(ttl=60*60*24*14)
def calculate_close_price(refresh: int, stock: str, stock_df: pd.DataFrame) -> Dict:
    df = preprocess(stock_df)
    # get all times before the last month
    train_df, test_df = df[df.index <= df.index.max() - pd.DateOffset(months=2)], df[df.index >= df.index.max() - pd.DateOffset(months=2)]
    reg = xgb.XGBRegressor(n_estimators=1000, early_stopping_rounds=200, eval_metric='rmse', learning_rate=0.1, max_depth=10, subsample=0.8, colsample_bytree=0.8, random_state=42)
    # split into train and test sets
    X_train, y_train = train_df.drop(columns=['close']), train_df['close']
    X_test, y_test = test_df.drop(columns=['close']), test_df['close']
    reg.fit(X_train, y_train, eval_set=[(X_train, y_train), (X_test, y_test)], verbose=False)
    # validate the model
    X_test['prediction'] = reg.predict(X_test)
    # rmse score as a percentage of the mean of the close prices
    # score = np.sqrt(mean_squared_error(y_test, X_test['prediction'])) / y_test.mean()
    # R2 score
    # r2 = r2_score(y_test, X_test['prediction'])
    # n = len(X_test)
    # p = len(X_test.columns)
    # adj_r2 = 1 - (1 - r2) * (n - 1) / (n - p - 1)
    # get predicted stock price for the entire dataset
    df['prediction'] = reg.predict(df.drop(columns=['close']))
    return {'stock': stock, 'prediction': df['prediction'], 'cur_price': df['close']}


stock_ticker = st.text_input(label = 'Type ticker symbol below', value = 'AAPL')
stock_data = getPastStockPrices(st.session_state.stock_refresh, stock_ticker)
if not stock_data.empty:
    stock_data = convert_column_names(stock_data)
    # convert all the columns to floats except for the index column
    stock_data = stock_data.astype(float)
    # run xgboost on the stock_data dataframe
    predictions = calculate_close_price(st.session_state.recomm_refresh, stock_ticker, stock_data)
    # add the prediction to the daily_data dataframe
    # st.dataframe(predictions['prediction'])

    # create checkboxes for each column in the stock data, with default being close
    # checkboxes = st.multiselect('Select indicators to plot', stock_data.columns, default=['close'])
    # create a plotly figure of close price
    fig = px.line(title=f'{stock_ticker} close price')
    # add close price to the plotly figure
    fig.add_scatter(x=stock_data.index, y=stock_data['close'], name='close')
    # add predictions to the plotly figure
    fig.add_scatter(x=stock_data.index, y=predictions['prediction'], name='prediction')
    # # create a plotly blank figure
    # fig = px.line()
    # for column in checkboxes:
    #     # add each column to the plotly figure
    #     fig.add_scatter(x=stock_data.index, y=stock_data[column], name=column)

    st.plotly_chart(fig, use_container_width=True)

    # add download button
    st.download_button('Download raw stock data', stock_data.to_csv(), f'{stock_ticker}_data.csv', 'text/csv')

else:
    st.subheader('No data for this stock exists in the database')
# st.dataframe(getPastStockPrices())
# st.dataframe(data = getRecommendedStocks(predgoal = option))

# st.write('The prediction is just a random number, everything else is constant')

# st.dataframe(data = getSentimentData())
# st.header('Past accuracy (random numbers):')

# st.line_chart(data = getPastAccuracy(), x = 'Day', y = ['Daily', 'Weekly', 'Monthly'], use_container_width = True)

# chart_data = pd.DataFrame( # REMOVE THIS LATER, YOU'RE NOT SUPPOSED TO DIRECTLY USE THAT HERE
#     np.random.randn(5, 3),
#     columns=["random", "xd", "data"])
# st.bar_chart(chart_data)

# st.write("There's fancier UI design options than just sticking everything in a big column but fuck it, we can expirement with that stuff when we know what we want.")
