import streamlit as st

dudu_linkedin = "https://www.linkedin.com/in/david-peleg-8b1b13162/"
dudu_github = "https://github.com/DavidPeleg6"
avihai_linkedin = "https://www.linkedin.com/in/avihai-didi-ba47a6224/"
avihai_github = "https://github.com/AvihaiDidi"

st.header('Stock analasys and recomendation platform')
st.subheader('Developed by David Peleg and Avihai Didi, 2023')

st.write(f"David Peleg [github]({dudu_github}), [linkedin]({dudu_linkedin})")
st.write(f"Avihai Didi [github]({avihai_github}), [linkedin]({avihai_linkedin})")

st.write("Frontend was made using streamlit")
st.write("Backend is hosted on AWS using a combination of dynamoDB, RDS, and lambda function")
# TODO: when done with everything else check that this statement is still correct
