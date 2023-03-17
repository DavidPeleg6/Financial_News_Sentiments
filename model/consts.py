"""
Constants used throughout the other files.
"""

# aws keys
aws_access_key_id = 'AKIATMSMR3RSAVNMG6PT'
aws_secret_access_key = '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'

# online data sources
price_data_source = "https://www.alphavantage.co/query"
financial_sheets_functions = ['OVERVIEW', 'INCOME_STATEMENT', 'BALANCE_SHEET', 'CASH_FLOW', 'EARNINGS']
# TODO: right now only 'EARNINGS' is actually used for anything, maybe use the other stuff too?

# df column names
stock_col_names = ['open', 'high', 'low', 'close', 'adjusted_close',# TODO: check where it's used,maybe move it there
                    'volume', 'dividend_amount', 'split_coefficient']
useless_col_names = ['split_coefficient', 'dividend_amount']# TODO: check where it's used,maybe move it there
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
    'model': 'model_data'
    }
all_news_sentiments_filename = "__all__"
model_data_filename = 'info'

# feature engineering constants
moving_averages = [30, 50, 100, 200]
moving_highs = [4*7, 10*7, 52*7]
moving_lows = [4*7, 10*7, 52*7]
moving_averages_names = [f"{i}_day_MA" for i in moving_averages]
moving_highs_names = [f"{i/7}_week_high" for i in moving_averages]
moving_lows_names = [f"{i/7}_week_low" for i in moving_averages]

# model
default_XGboost_params = {'n_estimators': 1000, 'early_stopping_rounds': 200,
                          'eval_metric': 'rmse', 'learning_rate': 0.1, 'max_depth': 10,
                          'subsample': 0.8, 'colsample_bytree': 0.8, 'random_state': 42}
optuna_optimization_trials = 100
