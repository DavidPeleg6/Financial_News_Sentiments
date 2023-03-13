import streamlit as st
import pandas as pd # REMOVE THIS LATER, YOU'RE NOT SUPPOSED TO DIRECTLY USE THAT HERE
import numpy as np # REMOVE THIS LATER, YOU'RE NOT SUPPOSED TO DIRECTLY USE THAT HERE

from dataLoader import getRecommendedStocks, getPastAccuracy, getSentimentData, time_step_options


st.title('Financial Stock Recommendation System')

st.header('Sentiment Analysis of News Articles')
option = st.selectbox(
    label = 'Top 10 Most Buzzing Stocks',
    options = time_step_options,
    index = 1)

sentiment_data = getSentimentData(time_step=option)
# create a histogram where the x axis is the stock name and the y axis is the frequency, take only the 10 most frequent stocks
st.bar_chart(data = sentiment_data['Stock'].value_counts().head(10), use_container_width = True)

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