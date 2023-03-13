import streamlit as st
import pandas as pd # REMOVE THIS LATER, YOU'RE NOT SUPPOSED TO DIRECTLY USE THAT HERE
import numpy as np # REMOVE THIS LATER, YOU'RE NOT SUPPOSED TO DIRECTLY USE THAT HERE
import os

# from news_sentiment_page import display_page
from dataLoader import getPastStockPrices, time_step_options

stock_df = getPastStockPrices()
st.dataframe(stock_df)
# get 