import streamlit as st
import pandas as pd
import os
import plotly.express as px
from pages.Stock_Data import getPastStockPrices, convert_column_names
from typing import Dict
import datetime
import requests
from sqlalchemy import create_engine, text
import numpy as np

_default_stonk = 'MSFT'
_pred_days = 60 # days back from today to try and predict
time_step_options = ('Daily', 'Weekly', 'Monthly')
time_deltas = {'Daily': 1, 'Weekly': 7, 'Monthly': 30}

if 'recomm_refresh' not in st.session_state:
    st.session_state.recomm_refresh = 0

st.set_page_config(layout="wide")

refresh_stocks = st.button('Refresh', key='reccom_refresh')
if refresh_stocks:
    st.session_state.recomm_refresh += 1

# try loading DB_ACCESS_KEY from csv file - useful when you run the app locally
try:
    DB_ACCESS_KEY = pd.read_csv('streamlit_interface/db_key_pass.csv')
    os.environ['ID'] = DB_ACCESS_KEY['ID'][0]
    os.environ['PASS'] = DB_ACCESS_KEY['PASS'][0]
    os.environ['URL'] = DB_ACCESS_KEY['URL'][0]
except FileNotFoundError:
    pass


@st.cache_data(ttl=60*60*24)
def get_prediction(token: str,
                   start: datetime.date = datetime.datetime.now().date() - datetime.timedelta(days=_pred_days), 
                      end: datetime.date = datetime.datetime.now().date()) -> pd.DataFrame:
    # get stock predictions from aws by invoking the lambda function called 'model_get_predictions'
    # returns an empty dataframe if it fails
    url = os.environ['model_get_predictions_url'] # TODO: set this as an env var
    start_s = start.strftime('%Y-%m-%d')
    end_s = end.strftime('%Y-%m-%d')
    data = {
        'token': token,
        'start': start_s,
        'end': end_s
    }
    # Send POST request to API Gateway endpoint
    response = requests.post(url, json=data)
    if response.status_code == 200:
        # Parse JSON response and convert to Pandas DataFrame
        df = pd.read_json(response.content)
        # Return the DataFrame
        return df
    else:
        # Print error message and return None
        print('Error:', response.content)
        return pd.DataFrame()


st.title('Financial Stock Recommendation System')

st.write('This is a stock recommendation system that uses a combination of machine learning and news sentiment analysis to recommend stocks to buy.')
# st.write('The recommendation system is still under development, so the results are not guaranteed to be accurate. in the meantime, you can use the navigation bar on the left to explore the other features of the app.')

stock_ticker = st.text_input(label = 'Type ticker symbol below', value = _default_stonk)
# stock_data = getPastStockPrices(st.session_state.recomm_refresh, stock_ticker)
# if not stock_data.empty:
#     # get datas
#     stock_data = convert_column_names(stock_data)
#     predictions = get_prediction(stock_ticker)
#     # convert all the columns to floats except for the index column
#     stock_data = stock_data.astype(float)
#     predictions = predictions.astype(float)

#     # create a plotly figure of close price
#     fig = px.line(title=f'\'{str.upper(stock_ticker)}\' stock price')
#     # add close price to the plotly figure
#     fig.add_scatter(x=stock_data.index, y=stock_data['close'], name='close')
#     # add predictions to the plotly figure
#     fig.add_scatter(x=stock_data.index, y=predictions['prediction'], name='prediction')

#     st.plotly_chart(fig, use_container_width=True)

#     # add download buttons
#     st.download_button('Download raw stock data', stock_data.to_csv(), f'{stock_ticker}_data.csv', 'text/csv')
#     st.download_button('Download raw prediction data', predictions.to_csv(), f'{stock_ticker}_data.csv', 'text/csv')

# else:
#     st.subheader('No data for this stock exists in the database')


# ------------------------------------ EPS based recommendation ------------------------------------
@st.cache_data(ttl=60*60*24*30)
def getStockEarnings(refresh_counter) -> pd.DataFrame:
    """
    returns two dataframes, one for the best earning in the past quarter and one for the best predicted earning
    """
    # get data from the past month unless specified to take the entire dataframe
    earnings_query = f"""SELECT * FROM Earnings;"""
    future_earnings_query = f"""SELECT * FROM FutureEarnings"""

    # Query the database and load results into a pandas dataframe
    engine = create_engine(f"mysql+pymysql://{os.environ['ID']}:{os.environ['PASS']}@{os.environ['URL']}/stock_data")
    with engine.connect() as connection:
        earnings = pd.read_sql_query(sql=text(earnings_query), con=connection, parse_dates=['fiscalDateEnding', 'reportedDate']).sort_values(by='fiscalDateEnding', ascending=False)
        future_earnings = pd.read_sql_query(sql=text(future_earnings_query), con=connection, parse_dates=['fiscalDateEnding', 'reportDate']).drop(columns=['currency']).rename(columns={'reportDate': 'reportedDate', 'estimate': 'estimatedEPS'})
    
    combined_earnings = pd.concat([earnings, future_earnings], axis=0, ignore_index=True)
    sorted_earnings = combined_earnings.groupby('stock').apply(lambda x: x.sort_values(by='fiscalDateEnding')).reset_index(drop=True)
    return sorted_earnings


st.header("EPS based recommendation")

number_of_stocks = st.slider(
    label = 'eps_stocks',
    min_value = 5,
    max_value = 40,
    value = 20,
    step = 1, label_visibility='hidden')

earnings = getStockEarnings(st.session_state.recomm_refresh)
# get only stocks that have more than 2 quarters of earnings data
stocks_with_earnings = earnings.dropna().groupby('stock').filter(lambda x: len(x) > 2)
# get the stocks that have better eps than their last quarter
best_earnings = stocks_with_earnings.groupby('stock').apply(lambda x: x.iloc[0]['reportedEPS'] > x.iloc[1]['reportedEPS'])
# get a subset of the dataframe that only contains the stocks that have better eps than their last quarter
best_earnings = stocks_with_earnings[stocks_with_earnings['stock'].isin(best_earnings[best_earnings].index)]
# for each stock get the latest diff in eps and create column for the diff in percent calculated by the previous reportedEPS.
best_earnings['diff'] = best_earnings.groupby('stock')['reportedEPS'].diff()
best_earnings['diff_percent'] = best_earnings['diff'] / best_earnings.shift(1)['reportedEPS']
# get only the latest diff in eps for each stock
best_earnings = best_earnings.dropna().groupby('stock').apply(lambda x: x.iloc[-1]).sort_values(by='diff_percent', ascending=False)
# drop inf values
best_earnings = best_earnings.replace([np.inf, -np.inf], np.nan).dropna()

# plot a bar chart of the percent diff in eps using plotly. the y axis ticks should be in percent, and without points after the decimal
fig = px.bar(best_earnings.head(number_of_stocks), x='stock', y='diff_percent', title='Best EPS growth in the past quarter', labels={'stock': 'Stock', 'diff_percent': 'EPS growth'})
fig.update_yaxes(tickformat=".0%")
st.plotly_chart(fig, use_container_width=True)

st.markdown('please note that the stock price is affected mostly by the predicted eps, you can go to the company earnings section of [stock data](Stock_Data#company-earnings) to see the predicted eps for the next quarter.')
