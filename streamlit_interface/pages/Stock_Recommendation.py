import streamlit as st
import pandas as pd
import os
import plotly.express as px
from pages.Stock_Data import getPastStockPrices, convert_column_names
from typing import Dict
import xgboost as xgb
import requests
import random
import string
import time
from enum import Enum

_default_stonk = 'MSFT'

class data_sources(Enum):
    AWS = 1 # Amazon Web services (RDS)
    AlphaVantage = 2 # AlpahVantage

# set to wide mode
st.set_page_config(layout="wide")
refresh_stocks = st.button('Refresh', key='reccom_refresh')
if refresh_stocks:
    st.session_state.recomm_refresh += 1

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

def get_stockprice(token: str = _default_stonk, 
                   data_source: data_sources = data_sources.AlphaVantage) -> pd.DataFrame:
    # return a dataframe of the stock price
    # if it fails, it returns an empty dataframe
    if data_source == data_sources.AlphaVantage:
        endpoint = "https://www.alphavantage.co/query"
        parameters = {
            "function": "TIME_SERIES_DAILY_ADJUSTED",
            "symbol": token,
            "outputsize": 'full'
        }
        for _ in range(100):
            parameters['apikey'] = ''.join(random.choices(string.ascii_uppercase + string.digits, k=15))
            # Send a GET request to the API endpoint
            response = requests.get(endpoint, params=parameters)
            # Check if the request was successful
            if response.status_code == 200 and 'Note' not in response.json():
                # TODO: convert this to a dataframe
                return response.json()
            else:
                time.sleep(1)
        return pd.DataFrame
    elif data_source == data_sources.AWS:
        # TODO: replace this with a call to RDS
        return getPastStockPrices(st.session_state.stock_refresh, token)
    else:
        # what
        return pd.DataFrame

@st.cache_data(ttl=60*60*24)
def get_prediction(stock: str) -> pd.DataFrame:
    # TODO: implement
    print("implement")

stock_ticker = st.text_input(label = 'Type ticker symbol below', value = _default_stonk)
stock_data = getPastStockPrices(st.session_state.recomm_refresh, stock_ticker)
if not stock_data.empty:
    # get datas
    stock_data = convert_column_names(stock_data)
    predictions = get_prediction(stock_ticker)
    # convert all the columns to floats except for the index column
    stock_data = stock_data.astype(float)
    predictions = predictions.astype(float)

    # create a plotly figure of close price
    fig = px.line(title=f'\'{str.upper(stock_ticker)}\' stock price')
    # add close price to the plotly figure
    fig.add_scatter(x=stock_data.index, y=stock_data['close'], name='close')
    # add predictions to the plotly figure
    fig.add_scatter(x=stock_data.index, y=predictions['prediction'], name='prediction')

    st.plotly_chart(fig, use_container_width=True)

    # add download buttons
    st.download_button('Download raw stock data', stock_data.to_csv(), f'{stock_ticker}_data.csv', 'text/csv')
    st.download_button('Download raw prediction data', predictions.to_csv(), f'{stock_ticker}_data.csv', 'text/csv')

else:
    st.subheader('No data for this stock exists in the database')
