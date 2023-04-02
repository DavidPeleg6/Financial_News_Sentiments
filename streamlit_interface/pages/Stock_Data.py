import streamlit as st
import pandas as pd 
import os
import plotly.express as px
from sqlalchemy import create_engine, text

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

# st.session_state.OFFLINE = False

@st.cache_data(ttl=60*60*24)
def getPastStockPrices(refresh_counter, stock: str = 'MSFT', alltime = False) -> pd.DataFrame:
    """
    returns a pandas dataframe structured as follows:
    company name, ticker, sentiment score, sentiment magnitude, sentiment score change, sentiment magnitude change
    """
    # if st.session_state.OFFLINE:
    #     stock_prices = pd.read_csv("streamlit_interface/temp_data/stock_df.csv", index_col="Date")
    #     # get stock prices of a stock in the Stock column
    #     stock_prices = stock_prices[stock_prices['Stock'] == str.upper(stock)].drop(columns=['Stock'], errors='ignore')
    
    # get data from the past month unless specified to take the entire dataframe
    query = f"""SELECT * FROM Prices WHERE Stock = '{str.upper(stock)}';""" if alltime else f"""
            SELECT * FROM Prices Where Stock = '{str.upper(stock)}' and Date >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH);"""
    
    # Query the database and load results into a pandas dataframe
    engine = create_engine(f"mysql+pymysql://{os.environ['ID']}:{os.environ['PASS']}@{os.environ['URL']}/stock_data")
    with engine.connect() as connection:
        stock_prices = pd.read_sql_query(sql=text(query), con=connection, parse_dates=['Date']).drop(columns=['Stock']).set_index('Date').sort_index(ascending=False)
    return stock_prices


def convert_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts the column names of a dataframe to more readable names. 
    """
    # replace all spaces with underscores
    df.columns = df.columns.str.replace('_', ' ')
    df.columns = df.columns.str.replace('MA', 'moving average')
    # convert all column names to lowercase
    df.columns = df.columns.str.lower()
    # sort columns by string length
    df = df.reindex(sorted(df.columns, key=len), axis=1)
    df.columns = df.columns.str.replace('adj', 'adjusted')
    return df


refresh_stocks = st.button('Refresh')
if refresh_stocks:
    st.session_state.stock_refresh += 1
st.header('Basic Stock Data')

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
    checkboxes = st.multiselect('Select indicators to plot', stock_data.columns, default=['close'])
    # create a plotly blank figure
    fig = px.line()
    for column in checkboxes:
        # add each column to the plotly figure
        fig.add_scatter(x=stock_data.index, y=stock_data[column], name=column)

    st.plotly_chart(fig, use_container_width=True)

    # TODO add the earnings stock data histograms pulled from the database
    # add download button
    st.download_button('Download raw stock data', stock_data.to_csv(), f'{stock_ticker}_data.csv', 'text/csv')

else:
    st.subheader('No data for this stock exists in the database')