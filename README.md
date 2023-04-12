# Financial_News_Sentiments
Extracts financial sentiments about stocks from the news sources and uses the data to create simple predictions of the stock market.

TLDR; How to make a gazillion dollars off the stock market with https://recommend-my-stocks.streamlit.app/.

And now for the slightly less clickbaity version - a neat little project Avihai Didi and I worked on to address our personal gripes as amateur traders.

Starting with my biggest complaint, finding investment leads. 
With the whirlpool of media outlets covering the financial markets, I need to spend 1-4 hours a week reading news in order to follow my current portfolio, not to mention the research behind finding a new stock to purchase.
Therefor, the first feature of the tool collects over 1000 articles daily and extracts all the stocks mentioned in each one, along with the article's sentiment towards each company.
While the tech giants are obviously the most trending compnies, the feature also unveils stocks that a noob trader such as myself wouldnt think to look at (because who has time to read about every company in the S&P500).

The next step is a feature to display the company's financial data. 
While stock prices, moving averages, highs, and lows are important indicators to consider, more experienced traders may also focus on additional features such as income statements, quarterly earnings, and balance sheets. As such, the tool will provide these features for a more comprehensive analysis.

Now for more buzzwords - AI. 
Every major platform I encountered used a cryptic grading system, often a simple "this is the combined recommendation of our analysts", which is usually hidden behind a paywall.
And since there are machine learning approaches for time series prediction, the required feature should let me:
1. Choose a model for stock prediction (could vary from random forests and ARIMA to LSTMs and Transformers)
2. Get the performance of the model - not only in niche terms such as RMSE or R^2, but in terms of actual profit I could make by using the model

And the final requirement - I want a product, not a github repo gathering dust.
So the entire project is hosted in aws and while not all the features mentioned above are supported, the app is available in a streamlit app through the following URL: https://recommend-my-stocks.streamlit.app/

And if you have any notes, or (hopefully) a will to contribute to the project, feel free to reach out to me!


![Project](https://user-images.githubusercontent.com/26568166/231538354-e6c84d30-f48c-457a-8673-3469d01735b3.png)
