import streamlit as st
import pandas as pd # REMOVE THIS LATER, YOU'RE NOT SUPPOSED TO DIRECTLY USE THAT HERE
import numpy as np # REMOVE THIS LATER, YOU'RE NOT SUPPOSED TO DIRECTLY USE THAT HERE

import dataLoader

st.title('Avihai-Dudu project WIP stream UI')

option = st.selectbox(
    label = 'Prediction target',
    options = ('Daily', 'Weekly', 'Monthly'),
    index = 1)
st.dataframe(data = dataLoader.getRecommendedStocks(predgoal = option))

st.write('The prediction is just a random number, everything else is constant')

st.header('Past accuracy (random numbers):')

st.line_chart(data = dataLoader.getPastAccuracy(), x = 'Day', y = ['Daily', 'Weekly', 'Monthly'], use_container_width = True)

st.write('Image test:')
from PIL import Image
image = Image.open('image.png')
st.image(image, caption='DOOMGUY STRONG')
st.write('Images works')

st.header('I forgot what this was supposed to be but I remember we were supposed to do something with this type of graph:')

st.write("we should have probably kept a copy of that image you drew when we discussed what to do, I forgot most of it by now .-. (doesn't really matter, this stuff is ez to do anyways)")

chart_data = pd.DataFrame(
    np.random.randn(5, 3),
    columns=["a", "b", "c"])
st.bar_chart(chart_data)

st.write("There's fancier UI design options than just sticking everything in a big column but fuck it, we can expirement with that stuff when we know what we want.")

st.button('Reload page')