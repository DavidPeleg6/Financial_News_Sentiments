import streamlit as st
import pandas as pd
import os
import plotly.express as px
from typing import Dict

from dataLoader import getPastStockPrices, convert_column_names, get_predictions

_default_stonk = 'MSFT'

# set to wide mode
st.set_page_config(layout="wide")
refresh_stocks = st.button('Refresh', key='reccom_refresh')
if refresh_stocks:
    st.session_state.recomm_refresh += 1

# try loading DB_ACCESS_KEY from csv file - useful when you run the app locally
try:
    DB_ACCESS_KEY = pd.read_csv('DB_ACCESS_KEY.csv')
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

stock_ticker = st.text_input(label = 'Type ticker symbol below', value = _default_stonk).upper()

stock_data = getPastStockPrices(st.session_state.recomm_refresh, stock_ticker)
predictions = get_predictions(stock_ticker)
if not stock_data.empty and not predictions.empty:
    # get datas
    stock_data = convert_column_names(stock_data)
    # convert all the columns to floats except for the index column
    stock_data = stock_data.astype(float)
    predictions["close"] = predictions["close"].astype(float)

    # create a plotly figure of close price
    fig = px.line(title=f'\'{str.upper(stock_ticker)}\' stock price')
    # add close price to the plotly figure
    fig.add_scatter(x=stock_data.index, y=stock_data['close'], name='close')
    # add predictions to the plotly figure
    fig.add_scatter(x=stock_data.index, y=predictions['close'], name='prediction')

    st.plotly_chart(fig, use_container_width=True)

    # add download buttons
    st.download_button('Download raw stock data', stock_data.to_csv(), f'{stock_ticker}_data.csv', 'text/csv')
    st.download_button('Download raw prediction data', predictions.to_csv(), f'{stock_ticker}_data.csv', 'text/csv')
elif not stock_data.empty:
    st.subheader('Data is avilable but prediction generation failed.')
        # get datas
    stock_data = convert_column_names(stock_data)
    # convert all the columns to floats except for the index column
    stock_data = stock_data.astype(float)

    # create a plotly figure of close price
    fig = px.line(title=f'\'{str.upper(stock_ticker)}\' stock price')
    # add close price to the plotly figure
    fig.add_scatter(x=stock_data.index, y=stock_data['close'], name='close')

    st.plotly_chart(fig, use_container_width=True)

    # add download buttons
    st.download_button('Download raw stock data', stock_data.to_csv(), f'{stock_ticker}_data.csv', 'text/csv')
else:
    st.subheader('No data for this stock exists in the database')
