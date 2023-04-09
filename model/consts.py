"""
Constants used throughout the other files.
"""

# aws keys


# aws consts
# Set this to 'true' if this code is running in a lambda function on aws
aws = False
bucket_name = "financialnewssentimentsmodel"
prediction_table_name = "StockPredictions"
aws_key_filename = 'aws_keys.txt'
if not aws:
    with open(aws_key_filename, 'r') as f:
        aws_access_key_id = f.readline().strip()
        aws_secret_access_key = f.readline().strip()

# online data sources
price_data_source = "https://www.alphavantage.co/query"
financial_sheets_functions = ['OVERVIEW', 'INCOME_STATEMENT', 'BALANCE_SHEET', 'CASH_FLOW', 'EARNINGS']
# TODO: right now only 'EARNINGS' is actually used for anything, maybe use the other stuff too?
model_table_names = {
    'xgbV1': 'ModelsXGB',
    'xgbV2': 'ModelsXGBV2'
}

# df column names
stock_col_names = ['open', 'high', 'low', 'close', 'adjusted_close',
                    'volume', 'dividend_amount', 'split_coefficient']
sentiment_col_names_dic = {
                    'ticker_sentiment_score': 'sentiment',
                    'relevance_score': 'relevance',
                    'Date': 'time',
                    'source': 'site',
                    'Stock': 'token'
                    }
earnings_prefix = 'earnings'
sentiments_prefix = 'sentiments'

# folder & file names
folders = {
    'price' : 'price_data',
    'report': 'report_data',
    'sentiments': 'sentiment_data',
    # gattai means combine in weeb, as in it's what big robots do to become bigger robots
    'gattai': 'gattai_data',
    'model': 'model_data',
    'modelV2': 'model_v2_data',
    'FEprice': 'FE_price_data'
    }
all_news_sentiments_filename = "__all__"
model_data_filename = 'info'

# feature engineering constants
moving_averages = [30, 50, 100, 200]
moving_highs = [4*7, 10*7, 52*7]
moving_lows = [4*7, 10*7, 52*7]
moving_averages_names = [f"{i}_day_MA" for i in moving_averages]
moving_highs_names = [f"{int(i/7)}_week_high" for i in moving_highs]
moving_lows_names = [f"{int(i/7)}_week_low" for i in moving_lows]

# model
default_XGboost_params = {'n_estimators': 1000, 'early_stopping_rounds': 200,
                          'eval_metric': 'rmse', 'learning_rate': 0.1, 'max_depth': 10,
                          'subsample': 0.8, 'colsample_bytree': 0.8, 'random_state': 42}
optuna_optimization_trials = 100
test_months = 2
days_ahead = 1
