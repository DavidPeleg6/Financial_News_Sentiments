import streamlit as st
import pandas as pd # REMOVE THIS LATER, YOU'RE NOT SUPPOSED TO DIRECTLY USE THAT HERE
import numpy as np # REMOVE THIS LATER, YOU'RE NOT SUPPOSED TO DIRECTLY USE THAT HERE

from dataLoader import getRecommendedStocks, getPastAccuracy

st.title('Avihai-Dudu project WIP stream UI')

option = st.selectbox(
    label = 'Prediction target',
    options = ('Daily', 'Weekly', 'Monthly'),
    index = 1)
st.dataframe(data = getRecommendedStocks(predgoal = option))

st.write('The prediction is just a random number, everything else is constant')

st.header('Past accuracy (random numbers):')

st.line_chart(data = getPastAccuracy(), x = 'Day', y = ['Daily', 'Weekly', 'Monthly'], use_container_width = True)

chart_data = pd.DataFrame(
    np.random.randn(5, 3),
    columns=["random", "xd", "data"])
st.bar_chart(chart_data)

st.write("There's fancier UI design options than just sticking everything in a big column but fuck it, we can expirement with that stuff when we know what we want.")

st.button('Reload page')