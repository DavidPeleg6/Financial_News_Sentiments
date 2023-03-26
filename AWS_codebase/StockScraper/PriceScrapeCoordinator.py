import pandas as pd
import boto3
import json
# import time
# from tqdm import tqdm

# The maximum number of stocks to scrape
MAX_STOCKS = 1000

# define a boto resource in the ohio region
dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
table = dynamodb.Table('StockSentiment')
client = boto3.client('lambda', region_name='us-east-2')


def lambda_handler(event, context):
    # keep scanning until we have all the data in the table
    response = table.scan()
    data = response['Items']
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])
    # convert the data to a pandas dataframe
    sentiment_ticker_list = pd.DataFrame(data)
    # convert Date column to datetime
    sentiment_ticker_list['Date'] = pd.to_datetime(sentiment_ticker_list['Date'])
    # make the index the Date column
    sentiment_ticker_list = sentiment_ticker_list.set_index('Date').sort_index(ascending=False)
    # get a list of tickers sorted by frequency, and append googl since theres a bug with alpha vantage
    sorted_tickers = sentiment_ticker_list['Stock'].value_counts().index.tolist() + ['GOOGL']
    # remove any stocks that contain crypto or forex and take the first MAX_STOCKS
    sorted_tickers = [t for t in sorted_tickers if 'crypto' not in t.lower() and 'forex' not in t.lower()][:MAX_STOCKS]
    
    for i in range(0, len(sorted_tickers), 5):
        response = client.invoke(
            FunctionName='Collect5stocks',
            # InvocationType='RequestResponse',
            InvocationType='Event',
            Payload=json.dumps({'body': sorted_tickers[i:i+5]})
        )


# start = time.time()
# lambda_handler(None, None)
# print(f'Runtime of the program is {time.time() - start}')