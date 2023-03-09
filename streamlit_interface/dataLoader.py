# this version just loads constant data, it's only for use as an example

import pandas as pd
import numpy as np

datapth = 'temp_data/'

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
        return pd.read_csv(datapth + 'daily_recommendations.csv')
    if predgoal == _valid_predgoals[1]:
        return pd.read_csv(datapth + 'weekly_recommendations.csv')
    return pd.read_csv(datapth + 'monthly_recommendations.csv')

# returns a pandas dataframe listing the accuracy of the model in the past for each type of prediction
# the input is how many days back from right now you want it to show
def getPastAccuracy(time_back = 100):
    # TODO: actually do this, right now it just returns a randomly generated list
    return pd.read_csv(datapth + 'past_accuracy.csv')