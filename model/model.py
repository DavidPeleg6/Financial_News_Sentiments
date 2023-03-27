"""
Function for creating, saving, and loading predictive models
"""

import pandas as pd
import xgboost as xgb
from enum import Enum
import numpy as np
import optuna
from os import mkdir, path
from sklearn.metrics import mean_squared_error
import datetime

import consts
import offline_data
from online_data import write_to_DDB

class overwrite_modes(Enum):
    NEVER = 1
    BETTER = 2
    ALWAYS = 3

def _printProgressBar(iteration: int, total: int, prefix: str = '', suffix: str = '',
                      decimals: int = 1, length: int = 100, fill: str = '█', printEnd: str = "\r"):
    # displays progress for interation/total, variable names are self explanatory (my documentation's da best)
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% _{iteration}/{total}_ {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()

def _get_RMSE(token: str):
    # returns the RMSE of the model for 'token'. If no model currently exists return -1
    try:
        df = pd.read_csv(f"{consts.folders['model']}/{consts.model_data_filename}.csv")
    except (FileNotFoundError, OSError):
        # make the folder if it doesn't already exist
        if not path.exists(consts.folders['model']):
            mkdir(consts.folders['model'])
        # save the empty info file in the folder
        df = pd.DataFrame(columns=["token", "date", "RMSE", "test_months", "optimize"])
        df.to_csv(f"{consts.folders['model']}/{consts.model_data_filename}.csv", index=False)
        return -1
    # get the row 'token' is stored at
    row = df[df["token"] == token]
    # if it doesn't exist, return -1
    if row.empty:
        return -1
    return row['RMSE'].iat[0]

def _save_model_info(token: str, RMSE: float, test_months: int, optimize: bool):
    # saves the info regarding the model's performance, overwrites existing data
    filename = f"{consts.folders['model']}/{consts.model_data_filename}.csv"
    new_data = pd.DataFrame({
            "token": [token],
            "date": [datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")],
            "RMSE": [RMSE],
            "test_months": [test_months], 
            "optimize": [optimize]
        })
    try:
        df = pd.read_csv(filename)
    except (FileNotFoundError, OSError):
        # make the folder if it doesn't already exist
        if not path.exists(consts.folders['model']):
            mkdir(consts.folders['model'])
        # save the new info file in the folder
        new_data.to_csv(filename, index=False)
    # get the row 'token' is stored at
    row = df[df["token"] == token]
    # if it doesn't exist, just add it
    if row.empty:
        new_data.to_csv(filename, mode='a', header=False, index=False)
    # if it does exist, replace it and overwrite the older file
    elif not new_data.empty:
        df[df["token"] == token] = new_data
        df.to_csv(filename, index=False)


def new_model(token: str, df: pd.DataFrame = pd.DataFrame(), optimize: bool = True, test_months: int = consts.test_months,
              print_acc: bool = False, overwrite_mode: overwrite_modes = overwrite_modes.BETTER) -> xgb.XGBRegressor:
    """
    Parameters:

    token: the stock token the data belongs to
    df: A DataFrame containing gattai data.
        if no df_ is provided, it will attempt to load it from the avilable data (gattai is used)
    optimize: A boolean value that indicates whether or not to optimize the model's hyperparameters. Default is True.
    test_months: An integer value that represents the number of months to use as test data. Default is 3.
    print_acc: A boolean value that indicates whether or not to print the accuracy of the model. Default is False.
    overwrite_mode: An enumeration that represents the overwrite mode for existing models. Default is BETTER.

    Once generated, the model is saved in folders['model'], and it's data is logged in consts.model_data_filename
    'overwrite_mode' determines what should be done if an earlier model already exists, it's options are:
    NEVER   never overwrite, don't save the new model at all
    BETTER  overwrite the older model only if the new one is more accurate
    ALWAYS  overwrite the older model

    If for whatever reason model creation fails, None is returned
    """
    if df.empty:
        df_copy = offline_data.load_gattai(token)
    else:
        df_copy = df.copy()
    if df_copy.empty:
        print("Failed to load data for " + token)
        return None
    # raise the all the columns up by one day so that the model only gets the daily open price and
    # the rest of the data from yesterday
    for col in set(df_copy.columns) - {'close', 'open'}: df_copy[col] = df_copy[col][1:].shift(-1)
    # shift the close column by 1
    df_copy['close'] = df_copy['close'][:-1]
    df_copy = df_copy.dropna(axis=0)

    df_copy.index = pd.to_datetime(df_copy.index)
    df_copy.sort_index(ascending=False, inplace=True)
    # convert all columns to numeric except for the index
    df_copy = df_copy.apply(pd.to_numeric, errors='ignore')
    # drop any column that contains a date time value
    # df_copy = df_copy.drop(columns=[col for col in df_copy.columns if df_copy[col].dtype != 'float64']).dropna()
    df_copy = df_copy.dropna(axis=0)
    # get all times before the test_months months
    train_df_copy = df_copy[df_copy.index <= df_copy.index.max() - pd.DateOffset(months=test_months)]
    test_df_copy =  df_copy[df_copy.index >= df_copy.index.max() - pd.DateOffset(months=test_months)]

    # split to X and y
    tar_col = ['close']
    leak_col = ['adjusted_close']
    X_train, y_train = train_df_copy.drop(columns=tar_col + leak_col), train_df_copy[tar_col]
    X_test, y_test = test_df_copy.drop(columns=tar_col + leak_col), test_df_copy[tar_col]

    if optimize:
        def _objective(trial):
            # objective function used by optuna
            params = {
                'objective': 'reg:squarederror',
                'eval_metric': 'rmse',
                'booster': 'gbtree',
                'n_jobs': -1,
                'verbosity': 0,
                'eta': trial.suggest_float('eta', 1e-5, 1),
                'max_depth': trial.suggest_int('max_depth', 3, 10),
                'subsample': trial.suggest_float('subsample', 0.1, 1),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.1, 1),
                'gamma': trial.suggest_float('gamma', 1e-5, 1),
                'min_child_weight': trial.suggest_float('min_child_weight', 1e-5, 100),
                'reg_alpha': trial.suggest_float('reg_alpha', 1e-5, 100),
                'reg_lambda': trial.suggest_float('reg_lambda', 1e-5, 100)
            }
            
            # Train the model
            model = xgb.XGBRegressor(**params)
            model.fit(X_train, y_train)
            # Evaluate the model on the testation set
            y_pred = model.predict(X_test)
            error = mean_squared_error(y_test, y_pred, squared=False)
            return error
        optuna.logging.set_verbosity(optuna.logging.WARNING)
        study = optuna.create_study(direction='minimize')
        study.optimize(_objective, n_trials=consts.optuna_optimization_trials)
        model = xgb.XGBRegressor(**study.best_params)
    else:
        model = xgb.XGBRegressor(**consts.default_XGboost_params)
    model.fit(X_train, y_train, eval_set=[(X_train, y_train), (X_test, y_test)], verbose=False)
    new_RMSE = np.sqrt(mean_squared_error(y_test, model.predict(X_test)))
    if print_acc:
        print(f'{token}\tmodel RMSE:\t{new_RMSE:.4f}')
    # now that we have the RMSE over the test data, we can retrain the model over ALL data
    # can't do early stopping without a validation set, so nvm
    # X_final, y_final = df_copy.drop(columns=['close']), df_copy['close']
    # model.fit(X_final, y_final, verbose=False)
    filename = f"{consts.folders['model']}/{token}.bin"
    existing_RMSE = _get_RMSE(token)
    should_save = overwrite_mode == overwrite_modes.ALWAYS or existing_RMSE == -1 or new_RMSE < existing_RMSE
    if overwrite_mode != overwrite_modes.NEVER and should_save:
        try:
            model.save_model(filename)
            _save_model_info(token, new_RMSE, test_months, optimize)
        except (FileNotFoundError, OSError):
            mkdir(consts.folders['model'])
            model.save_model(filename)
            _save_model_info(token, new_RMSE, test_months, optimize)
    return model

def generate_models(token_list: list, optimize: bool = True, test_months: int = 3,
                    progress_bar: bool = True, overwrite_mode: overwrite_modes = overwrite_modes.BETTER) -> int:
    """
    Generates a model for each token in 'token_list' and saves them to the models folder
    if progress_bar = True it shows progress using a bar

    it returns the number of succsussfully generated models
    """
    sucsssusfull = 0
    failed_list = []
    iter = 0
    total = len(token_list)
    for token in token_list:
        if progress_bar:
            iter += 1
            _printProgressBar(iteration = iter, total = total, prefix="Generating models.", suffix=token)
        model = new_model(token = token, optimize = optimize,
                          test_months = test_months, overwrite_mode = overwrite_mode)
        if model != None:
            sucsssusfull += 1
        else:
            failed_list.append(token)
    print(f"Succsusfully trained {sucsssusfull}/{total} models.")
    print("Failed to create a model for the following tokens:")
    print(failed_list)

def load_model(token: str) -> xgb.XGBRegressor:
    """
    loads a model for the stock 'token'
    If a model doesn't exist, it will attempt to create one using new_model
    if that fails, None is returned
    """
    loaded_model = xgb.XGBRegressor()
    try:
        loaded_model.load_model(f"{consts.folders['model']}/{token}.bin")
    except (FileNotFoundError, OSError):
        # the folder doesn't exist, make it and make the model
        mkdir(consts.folders['model'])
        loaded_model = new_model(token)
    except xgb.core.XGBoostError:
        # the model doesn't exist, make one
        loaded_model = new_model(token)
    if loaded_model == None:
        print("Model creation failed for " + token)
    return loaded_model

def predict_tomorrow(tokens: list, date: datetime.date) -> pd.DataFrame:
    """
    ___ not used anymore, the implementation on aws is completly different 

    Predicts the closing prices of the stocks in 'tokens' for the day AFTER 'date'.
    Returns the prediction as a dataframe structured as follows:
    token, prediction, model_RMSE
    If prediction fails for a token, the corresponding entry will map be a None

    Note that if any of the requiered data doesn't exist yet (model, stock price data, etc)
    the function will just create it on it's own
    """
    df = pd.DataFrame(columns=['token', 'prediction', 'model_RMSE'])
    for token in tokens:
        model = load_model(token)
        if model is None:
            df = df.append({'token': token,
                            'prediction': None,
                            'model_RMSE': _get_RMSE(token)}, ignore_index=True)
        else:
            data = offline_data.load_gattai(token)
            pred = model.predict(data.loc[data.loc[date]])
            df = df.append({'token': token,
                            'prediction': pred,
                            'model_RMSE': _get_RMSE(token)}, ignore_index=True)
    return df

def write_predictions_to_DDB(tokens: list,
        start: datetime.date = datetime.datetime.now().date() - datetime.timedelta(days=30*consts.test_months), 
                      end: datetime.date = datetime.datetime.now().date(), progress_bar: bool = True):
    """
    ___ not used anywere, we're switching to RDS

    produces predictions for each token in 'tokens' for the dates between 'start' and 'end'
    writes all of those predictions to the table in dynamoDB called 'consts.prediction_table_name'

    DON'T RUN THIS FUNCTION MORE THAN ONCE FOR THE SAME STOCKS AND DATES
    IT DOESN'T CHECK IF THE DATA ALREADY EXISTS
    DOING SO WILL GENERATE DUPLICATE DATA
    """
    succsuss_count = 0
    iter = 0
    total = len(tokens)
    for token in tokens:
        if progress_bar:
            iter += 1
            _printProgressBar(iteration = iter, total = total, prefix=token, suffix="0/?")
        # get model
        model = load_model(token)
        if model == None:
            print("Failed to load model for " + token)
            continue
        # get data
        df = offline_data.load_gattai(token)
        if df.empty:
            df = offline_data.load_daily_price(token)
            if df.empty:
                print("Failed to load data for " + token)
                continue
        # drop the 'close' column
        df = df.drop(columns=['close'])
        # get only the data in the desired range
        time_format = "%Y-%m-%d"
        start_s = start.strftime(time_format)
        end_s = end.strftime(time_format)
        df = df.loc[start_s:end_s]
        pred_df = pd.DataFrame(columns=["Date", "Stock", "Close"])
        pred_df["Date"] = df.index.copy()
        pred_df["Stock"] = token
        # predict
        try:
            pred_df["Close"] = model.predict(df)
        except Exception as e:
            print("Failed to predict for " + token)
            print("Error is:\t" + str(e))
            continue
        # iterate over the rows
        try:
            for index, row in pred_df.iterrows():
                row_dict = row.to_dict()
                convdict = {
                    'Date': {'S': row_dict['Date']},
                    'Stock': {'S': row_dict['Stock']},
                    'Close': {'N': str(row_dict['Close'])}
                }
                # upload to dynamoDB
                if not write_to_DDB(consts.prediction_table_name, convdict):
                    print("Failed to upload for " + token)
                    continue
                if progress_bar:
                    _printProgressBar(iteration = iter, total = total, prefix=token, suffix=f"{index}/{len(pred_df)}")
        except Exception as e:
            print("Unknown error when trying to process " + token)
            print("Error msg:\t" + str(e))
            continue
        succsuss_count += 1
    if progress_bar:
        print(f"Completed predictioning for {succsuss_count}/{total} tokens.")
