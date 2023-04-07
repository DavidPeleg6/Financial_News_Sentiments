import streamlit as st
import pandas as pd 
import os
import plotly.express as px
from sklearn.metrics import mean_absolute_error
from dataLoader import getPastStockPrices, convert_column_names, getStockEarnings

st.set_page_config(layout="wide")

time_step_options = ('Daily', 'Weekly', 'Monthly')
time_deltas = {'Daily': 1, 'Weekly': 7, 'Monthly': 30}
if 'stock_refresh' not in st.session_state:
    st.session_state.stock_refresh = 0

# try loading DB_ACCESS_KEY from csv file - useful when you run the app locally
try:
    DB_ACCESS_KEY = pd.read_csv('streamlit_interface/db_key_pass.csv')
    os.environ['ID'] = DB_ACCESS_KEY['ID'][0]
    os.environ['PASS'] = DB_ACCESS_KEY['PASS'][0]
    os.environ['URL'] = DB_ACCESS_KEY['URL'][0]
except FileNotFoundError:
    pass

refresh_stocks = st.button('Refresh')
if refresh_stocks:
    st.session_state.stock_refresh += 1

# ------------------------------------- Stock Data -------------------------------------
st.header('Stock price')
stock_ticker = st.text_input(label = 'Type ticker symbol below', value = 'AAPL')
stock_data = getPastStockPrices(st.session_state.stock_refresh, stock_ticker, alltime=True)
if not stock_data.empty:
    stock_data = convert_column_names(stock_data)
    # convert all the columns to floats except for the index column
    stock_data = stock_data.astype(float)
    # create a dataframe out of the first row of the stock data
    daily_data = pd.DataFrame(stock_data.iloc[0]).T
    # create 3 columns
    col1, col2, col3 = st.columns(3)
    # in column 1, place a table of open, close, adjusted close, high, low, volume, split, and dividend. with 2 points of precision
    col1.subheader('Daily Data')
    col1.table(daily_data[['open', 'close', 'adjusted close', 'high', 'low', 'volume', 'split', 'dividend']].T.style.format('{:.1f}'))
    # in column 2, place the 4 week low, 4 week high, 10 week low, 10 week high, 52 week low and 52 week high
    col2.subheader('Historic highs and lows')
    col2.table(daily_data[['4 week low', '4 week high', '10 week low', '10 week high', '52 week low', '52 week high']].T.style.format('{:.1f}'))
    # in column 3, place the 30 day moving average, 50 day moving average, 100 day moving average and 200 day moving average
    col3.subheader('Moving averages')
    col3.table(daily_data[['30 day moving average', '50 day moving average', '100 day moving average', '200 day moving average']].T.style.format('{:.1f}'))
    # create checkboxes for each column in the stock data, with default being close
    checkboxes = st.multiselect('Select indicators to plot', stock_data.columns, default=['close', '30 day moving average'])
    
    # create a plotly blank figure
    fig = px.line()
    for column in checkboxes:
        # add each column to the plotly figure
        fig.add_scatter(x=stock_data.index, y=stock_data[column], name=column)
    st.plotly_chart(fig, use_container_width=True)

    # add download button
    st.download_button('Download raw stock data', stock_data.to_csv(), f'{stock_ticker}_data.csv', 'text/csv')
else:
    st.subheader('No price data for this stock exists in the database')


# ------------------------------------- Earnings Data -------------------------------------
st.header('Company earnings')
# get the earnings data
earnings_data = getStockEarnings(st.session_state.stock_refresh, stock_ticker)
if not earnings_data.empty:
    # create a bar plot of the earnings per share where the x axis is the fiscalDateEnding and the y axis is the reportedEPS include another column for the estimatedEPS
    fig = px.bar(earnings_data, x='fiscalDateEnding', y=['reportedEPS', 'estimatedEPS'], barmode='group', labels={'fiscalDateEnding': 'Date', 'value': 'Earnings per share', 'variable': 'Labels'})
    st.plotly_chart(fig, use_container_width=True)
    # calculate the mean absolute error of the reported earnings per share and the estimated earnings per share
    st.markdown(f"""
    The average estimation error of the EPS in the past 2 years is {mean_absolute_error(earnings_data.dropna()['reportedEPS'], earnings_data.dropna()['estimatedEPS']):.2f}. 
    And the next report date is: {earnings_data['reportedDate'].dt.date.iloc[0]}
    """)
    st.markdown(f"")
    # now do the same but drop the hours, minutes and seconds
    earnings_data['fiscalDateEnding'] = earnings_data['fiscalDateEnding'].dt.date
    earnings_data['reportedDate'] = earnings_data['reportedDate'].dt.date
    
    # add download button
    st.download_button('Download raw earnings data', earnings_data.to_csv(), f'{stock_ticker}_earnings_data.csv', 'text/csv')
else:
    st.subheader('No earnings data for this stock exists in the database')