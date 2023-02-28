# TODO: this should also act as a cache

import pandas as pd
import numpy as np

_valid_predgoals = ['Daily', 'Weekly', 'Monthly']
# gets as input a string detailing prediction targer, must be in the set _valid_predgoals
# returns a pandas dataframe structured as follows:
# company name, ticker, model predictions, past accuracy for this stock
# returns a number if an error occured:
# 0: input error (predgoal is invalid)
# 1: model could not generate prediction
# 2: other error (currently unused)
def getRecommendedStocks(predgoal = 'Weekly'):
    if predgoal not in _valid_predgoals:
        return 0
    # TODO: check if prediction is cached, and return that if so
    
    # TODO: actually aquire data from the model, right now it just returns this constant thing
    # (I took this from https://www.nasdaq.com/, it's just the top 5 I sawthere)
    # this if statement should actually do different stuff based on predgoal
    if predgoal == _valid_predgoals[0]:
        return pd.DataFrame({'Company name': ['Daily', 'Prediction', 'Test'], 
                      'Ticker': ['TSLA', 'NVDA', 'AAPL'], 
                      'Prediction': [np.random.random(1)[0], np.random.random(1)[0], np.random.random(1)[0]],
                      'Sentiment': [-1, 0, 5],
                      'Accuracy': [50, 20, -20]})
    if predgoal == _valid_predgoals[1]:
        return pd.DataFrame({'Company name': ['Weekly', 'Prediction', 'Test'], 
                      'Ticker': ['TSLA', 'NVDA', 'AAPL'], 
                      'Prediction': [np.random.random(1)[0], np.random.random(1)[0], np.random.random(1)[0]],
                      'Sentiment': [-1, 0, 5],
                      'Accuracy': [50, 20, -20]})
    return pd.DataFrame({'Company name': ['Monthly', 'Prediction', 'Test'], 
                      'Ticker': ['TSLA', 'NVDA', 'AAPL'], 
                      'Prediction': [np.random.random(1)[0], np.random.random(1)[0], np.random.random(1)[0]],
                      'Sentiment': [-1, 0, 5],
                      'Accuracy': [50, 20, -20]})

# returns a pandas dataframe listing the accuracy of the model in the past for each type of prediction
# the input is how many days back from right now you want it to show
def getPastAccuracy(time_back = 100):
    # TODO: actually do this, right now it just returns a randomly generated list
    SIGMA = 5
    MU = 0
    days = range(-time_back, 0)
    daily_accuracy = MU + SIGMA * np.random.randn(time_back)
    weekly_accuracy = MU + SIGMA * np.random.randn(time_back)
    monthly_accuracy = MU + SIGMA * np.random.randn(time_back)
    return pd.DataFrame({'Day': days,
                         'Daily': daily_accuracy, 
                         'Weekly': weekly_accuracy, 
                         'Monthly': monthly_accuracy})