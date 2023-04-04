"""
Modify existing data which was obtained using the functions in online_data or offline_data (add_...)
Also, combine dataframes (join_...)
"""
import pandas as pd
import numpy as np

import consts

def add_moving_averages(df: pd.DataFrame, target: str = 'adjusted_close',
        spans : list = consts.moving_averages,
        span_names : list = consts.moving_averages_names,
        in_place = False) -> pd.DataFrame:
    """
    adds columns of moving averages of the column 'target' to the dataframe
    spans is a list of what intervals it should average over, span_names will be the names of the columns
    if in_place = True the modifications are done to df directly, rather than to a copy
    """
    if len(spans) != len(span_names):
        print("Error: spans and span_names have different lengths")
        return df
    if in_place:
        tar_df = df
    else:
        tar_df = df.copy()
    for span, name in zip(spans, span_names):
        tar_df[name] = tar_df[target].rolling(span).mean()
    return tar_df

def add_moving_peaks(df: pd.DataFrame, target: str = 'adjusted_close',
        high_spans : list = consts.moving_highs,
        high_span_names : list = consts.moving_highs_names,
        low_spans : list = consts.moving_lows,
        low_span_names : list = consts.moving_lows_names,
        in_place = False) -> pd.DataFrame:
    """
    a combination of add_moving_highs and add_moving_lows
    adds the new columns in an order that matches what dudu did in aws
    """
    if len(high_spans) != len(high_span_names):
        print("Error: high spans and span_names have different lengths")
        return df
    if len(low_spans) != len(low_span_names):
        print("Error: low spans and span_names have different lengths")
        return df
    if len(low_spans) != len(high_spans):
        print("Error: low and high spans have different lengths")
        return df
    if in_place:
        tar_df = df
    else:
        tar_df = df.copy()
    # dumbass index based loop, yay
    for i in range(len(high_spans)):
        tar_df[high_span_names[i]] = tar_df[target].rolling(high_spans[i]).max()
        tar_df[low_span_names[i]] = tar_df[target].rolling(low_spans[i]).min()
    return tar_df

def add_moving_highs(df: pd.DataFrame, target: str = 'adjusted_close',
        spans : list = consts.moving_highs,
        span_names : list = consts.moving_highs_names,
        in_place = False) -> pd.DataFrame:
    """
    adds columns of moving highs of the column 'target' to the dataframe
    spans is a list of what intervals it should average over, span_names will be the names of the columns
    if in_place = True the modifications are done to df directly, rather than to a copy
    """
    if len(spans) != len(span_names):
        print("Error: spans and span_names have different lengths")
        return df
    if in_place:
        tar_df = df
    else:
        tar_df = df.copy()
    for span, name in zip(spans, span_names):
        tar_df[name] = tar_df[target].rolling(span).max()
    return tar_df

def add_moving_lows(df: pd.DataFrame, target: str = 'adjusted_close',
        spans : list = consts.moving_lows,
        span_names : list = consts.moving_lows_names,
        in_place = False) -> pd.DataFrame:
    """
    adds columns of moving lows of the column 'target' to the dataframe
    spans is a list of what intervals it should average over, span_names will be the names of the columns
    if in_place = True the modifications are done to df directly, rather than to a copy
    """
    if len(spans) != len(span_names):
        print("Error: spans and span_names have different lengths")
        return df
    if in_place:
        tar_df = df
    else:
        tar_df = df.copy()
    for span, name in zip(spans, span_names):
        tar_df[name] = tar_df[target].rolling(span).min()
    return tar_df

def join_earnings_df(price_df: pd.DataFrame, earnings_df: pd.DataFrame, in_place = False) -> pd.DataFrame:
    # joins earnings_df to price_df by the date. If in_place = True the modifications are done to df directly
    if in_place:
        gattai_df = price_df
    else:
        gattai_df = price_df.copy()
    # attempt 1, really dumb but vectorized approch
    for index, row in earnings_df.iterrows():
        for col in earnings_df.columns[1:]:
            gattai_df.loc[row['fiscalDateEnding'] < gattai_df.index, f"{consts.earnings_prefix}_{col}"] = row[col]
            # TODO: make this code better, this is not efficent
    # some rows don't get earnings data (coz there ain't any for them) so we get rid of them
    gattai_df = gattai_df.dropna()
    return gattai_df

def join_sentiment_df(price_df: pd.DataFrame, sentiment_df: pd.DataFrame, 
                      FE = True, in_place = False) -> pd.DataFrame:
    """
    joins sentiment_df to price_df by the date. If in_place = True the modifications are done to df directly
    if FE = True weekly and monthly average sentiment data is added
    sentiment_df should contain only the sentiments for the stock described by price_df
    """
    if in_place:
        gattai_df = price_df
    else:
        gattai_df = price_df.copy()
    # TODO: delete the next line once you actually have enough sentiment data
    return gattai_df
    # group the dataframe by day, average sentiment scores weighted by relevance
    avg = lambda x: np.average(x['sentiment'], weights=x['relevance'])
    sentiment_df = pd.DataFrame(sentiment_df.groupby(pd.Grouper(key='time', freq='D')).apply(avg),
                                 columns=['sentiment']).sort_index(ascending=False)
    if FE:
        # add the weekly sentiment scores
        days_in_week = 7
        sentiment_df['weekly_sentiment'] = sentiment_df['sentiment'].sort_index().rolling(days_in_week).mean().sort_index(ascending=False)
        # add the monthly sentiment scores
        days_in_month = 30
        sentiment_df['monthly_sentiment'] = sentiment_df['sentiment'].sort_index().rolling(days_in_month).mean().sort_index(ascending=False)

    # attachto the main df
    gattai_df = gattai_df.join(sentiment_df.add_prefix(f"{consts.sentiments_prefix}"), how='left')
    # for every nan value, replace it with the value of the previous day
    gattai_df.fillna(method='ffill', inplace=True)
    # drop whatever nans are left after that
    gattai_df = gattai_df.dropna()
    return gattai_df
