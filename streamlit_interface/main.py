import streamlit as st
import pandas as pd # REMOVE THIS LATER, YOU'RE NOT SUPPOSED TO DIRECTLY USE THAT HERE
import numpy as np # REMOVE THIS LATER, YOU'RE NOT SUPPOSED TO DIRECTLY USE THAT HERE

from dataLoader import getRecommendedStocks, getPastAccuracy, getSentimentData, time_step_options


st.title('Financial Stock Recommendation System')

st.header('Sentiment Analysis of News Articles')
st.write('Most Buzzing Stocks')
timeframe = st.selectbox(
    label = 'Time Frame',
    options = time_step_options,
    index = 1)
number_of_stocks = st.slider(
    label = 'Number of Stocks',
    min_value = 5,
    max_value = 40,
    value = 20,
    step = 1)

sentiment_data = getSentimentData(time_step=timeframe)
# create a histogram where the x axis is the stock name and the y axis is the frequency, make the chart sorted by frequency
st.bar_chart(data = sentiment_data['Stock'].value_counts().head(number_of_stocks), use_container_width = True)
# make streamlit bar chart sort by frequency
# https://discuss.streamlit.io/t/sort-bar-chart-by-value/1001/2

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

st.button('Reload page')