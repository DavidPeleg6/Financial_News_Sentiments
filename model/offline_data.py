"""
Access / save offline data
If offline data is not avilable, by default just obtain the data (using the functions in online_data.py)
"""
import pandas as pd
import os # TODO: maybe only import mkdir?

import consts
import online_data
import feature_engineering

daily_data_extension = "daily_prices"
weekly_data_extension = "weekly_prices"
monthly_data_extension = "monthly_prices"

# TODO: maybe just combine all of the 'save/load_x_price' into two functions
def save_daily_price(df: pd.DataFrame, token: str):
    # save daily stock data
    try:
        df.to_csv(f"{consts.folders['price']}/{token}_{daily_data_extension}.csv", index=True)
    except FileNotFoundError:
        os.mkdir(consts.folders['price'])
        df.to_csv(f"{consts.folders['price']}/{token}_{daily_data_extension}.csv", index=True)

def load_daily_price(token: str, get_online: bool = True) -> pd.DataFrame:
    # load daily stock data, if the data is not avilable offline and get_online = True download it first
    # returns None if it could not obtain data
    try:
        df = pd.read_csv(f"{consts.folders['price']}/{token}_{daily_data_extension}.csv", index_col=0)
    except FileNotFoundError:
        if not get_online:
            print("No offline daily price data avilable for " + token)
            return None
        df = online_data.get_price_data(token)
        if df == None:
            print("Could not obtain online daily price data for " + token)
            return None
        save_daily_price(df, token)
    return df

def save_weekly_price(df: pd.DataFrame, token: str, FEed: bool = True):
    """
    save weekly stock data, if FEed=True it is assumed that the df was modified using
    add_moving_averages, add_moving_highs, and add_moving_lows from feature_engineering.
    if it wasn't FEed should be set to false
    """
    resample_dict = {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last',
     'adjusted_close': 'last', 'volume': 'sum'}
    if FEed:
        for name in consts.moving_averages_names + consts.moving_highs_names + consts.moving_lows_names:
            resample_dict[name] = 'last'
    weekly_df = df.resample('W').agg(resample_dict)
    try:
        weekly_df.to_csv(f"{consts.folders['price']}/{token}_{weekly_data_extension}.csv", index=True)
    except FileNotFoundError:
        os.mkdir(consts.folders['price'])
        weekly_df.to_csv(f"{consts.folders['price']}/{token}_{weekly_data_extension}.csv", index=True)

def load_weekly_price(df: pd.DataFrame, token: str, get_online: bool = True, FE: bool = True) -> pd.DataFrame:
    """
    load weekly stock data, if the data is not avilable offline and get_online = True download it first
    if FE is set to true it will also apply feature engineering to the data before saving it
    returns None if it could not obtain data
    """
    try:
        df = pd.read_csv(f"{consts.folders['price']}/{token}_{weekly_data_extension}.csv", index_col=0)
    except FileNotFoundError:
        if not get_online:
            print("No offline weekly price data avilable for " + token)
            return None
        df = online_data.get_price_data(token)
        if df == None:
            print("Could not obtain online weekly price data for " + token)
            return None
        if FE:
            feature_engineering.add_moving_averages(df)
            feature_engineering.add_moving_highs(df)
            feature_engineering.add_moving_lows(df)
            save_weekly_price(df, token, FEed = True)
        else:
            save_weekly_price(df, token, FEed = False)
    return df

def save_monthly_price(df: pd.DataFrame, token: str, FEed: bool = True):
    """
    save monthly stock data, if FEed=True it is assumed that the df was modified using
    add_moving_averages, add_moving_highs, and add_moving_lows from feature_engineering.
    if it wasn't FEed should be set to false
    """
    resample_dict = {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last',
     'adjusted_close': 'last', 'volume': 'sum'}
    if FEed:
        for name in consts.moving_averages_names + consts.moving_highs_names + consts.moving_lows_names:
            resample_dict[name] = 'last'
    monthly_df = df.resample('M').agg(resample_dict)
    monthly_df.to_csv(f"{consts.folders['price']}/{token}_{monthly_data_extension}.csv", index=True)
    try:
        monthly_df.to_csv(f"{consts.folders['price']}/{token}_{weekly_data_extension}.csv", index=True)
    except FileNotFoundError:
        os.mkdir(consts.folders['price'])
        monthly_df.to_csv(f"{consts.folders['price']}/{token}_{weekly_data_extension}.csv", index=True)

def load_monthly_price(df: pd.DataFrame, token: str, get_online: bool = True, FE: bool = True) -> pd.DataFrame:
    """
    load monthly stock data, if the data is not avilable offline and get_online = True download it first
    if FE is set to true it will also apply feature engineering to the data before saving it
    returns None if it could not obtain data
    """
    try:
        df = pd.read_csv(f"{consts.folders['price']}/{token}_{monthly_data_extension}.csv", index_col=0)
    except FileNotFoundError:
        if not get_online:
            print("No offline monthly price data avilable for " + token)
            return None
        df = online_data.get_price_data(token)
        if df == None:
            print("Could not obtain online monthly price data for " + token)
            return None
        if FE:
            feature_engineering.add_moving_averages(df)
            feature_engineering.add_moving_highs(df)
            feature_engineering.add_moving_lows(df)
            save_monthly_price(df, token, FEed = True)
        else:
            save_monthly_price(df, token, FEed = False)
    return df

def save_earnings_report(df: pd.DataFrame, token: str):
    # save the earnings report of the stock 'token'
    try:
        df.to_csv(f"{consts.folders['report']}/{token}.csv", index=False)
    except FileNotFoundError:
        os.mkdir(consts.folders['report'])
        df.to_csv(f"{consts.folders['report']}/{token}.csv", index=False)

def load_earnings_report(token: str, get_online: bool = True) -> pd.DataFrame:
    """
    returns the earnings report of the stock 'token'
    if the data is not avilable offline and get_online = True download it first
    returns None if it could not obtain data
    """
    try:
        df = pd.read_csv(f"{consts.folders['report']}/{token}.csv")
    except FileNotFoundError:
        if not get_online:
            print("No offline earnings data avilable for " + token)
            return None
        df = online_data.get_earnings_report(token)
        if df == None:
            print("Could not obtain online earnings data for " + token)
            return None
        save_earnings_report(df, token)
    return df

def save_news_sentiments(df: pd.DataFrame, token: str):
    # save the news sentiments for the token 'token', if token is None it's assumed that the data is for ALL tokens
    if token == None:
        filename = f"{consts.folders['sentiments']}/{consts.all_news_sentiments_filename}.csv"
    else:
        filename = f"{consts.folders['sentiments']}/{token}.csv"
    try:
        df.to_csv(filename, index=False)
    except FileNotFoundError:
        os.mkdir(consts.folders['sentiments'])
        df.to_csv(filename, index=False)


def load_news_sentiments(token: str, get_online: bool = True) -> pd.DataFrame:
    """
    returns the news sentiments of the stock 'token'
    if the data is not avilable offline and get_online = True download it first
    returns None if it could not obtain data
    """
    try:
        if token == None:
            df = pd.read_csv(f"{consts.folders['sentiments']}/{consts.all_news_sentiments_filename}.csv")
        else:
            df = pd.read_csv(f"{consts.folders['sentiments']}/{token}.csv")
    except FileNotFoundError:
        if not get_online:
            print("No offline sentiment data avilable for " + token)
            return None
        df = online_data.get_news_sentiments(token)
        if df == None:
            print("Could not obtain online sentiment data for " + token)
            return None
        save_news_sentiments(df, token)
    return df

def save_gattai(df: pd.DataFrame, token: str):
    # saves the combined dataframe for the stock 'token'
    filename = f"{consts.folders['gattai']}/{token}.csv"
    try:
        df.to_csv(filename, index=False)
    except FileNotFoundError:
        os.mkdir(consts.folders['sentiments'])
        df.to_csv(filename, index=False)

def load_gattai(token: str, get_online: bool = True) -> pd.DataFrame:
    """
    returns the fully combined dataframe for the stock 'token'
    if the data is not avilable offline and get_online = True download and combine it first
    returns None if it could not obtain data
    """
    try:
        df = pd.read_csv(f"{consts.folders['gattai']}/{token}.csv")
    except FileNotFoundError:
        if not get_online:
            print("No offline gattai data avilable for " + token)
            return None
        price_df = load_daily_price(token)
        earnings_df = load_earnings_report(token)
        sentiment_df = load_news_sentiments(token)
        if sentiment_df == None or earnings_df == None or price_df == None:
            print("Could not obtain the data needed to construct a combined df for the stock " + token)
            return None
        df = price_df
        df = feature_engineering.join_earnings_df(df, earnings_df)
        df = feature_engineering.join_sentiment_df(df,sentiment_df)
        save_gattai(df, token)
    return df
