import json
import boto3
import traceback
from external_api_comm import get_stockprice, convert_dict_to_df

getMethod = 'GET'
postMethod = 'POST'
healthPath = '/health'
scrapePath = '/scrape/prices'

dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
table = dynamodb.Table('StockPrices')


def lambda_handler(event, context):
    try:
        httpMethod = event['httpMethod']
        path = event['path']
        # first scenario, health check
        if httpMethod == getMethod and path == healthPath:
            response = respond(None, 'successful')
        # second scenario, scrape stocks
        elif httpMethod == postMethod and path == scrapePath:
            failed_stocks = write_stocks(json.loads(event['body']))
            response = respond(None, 'successful') if not failed_stocks else respond(ValueError(f'Failed to scrape {failed_stocks}')) 
        else:
            response = respond(ValueError(f'Unsupported method/path: {httpMethod}/{path}'))
        return response
    except Exception as e:
        return respond(traceback.format_exc())
    

def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': str(err) if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        },
    }


def write_stocks(stock_list):
    stocks_to_watch = [str.upper(stock) for stock in stock_list]
    failed_stocks = []
    # iterate over all stocks and log into database
    for stock in stocks_to_watch:
        # get stockprice from alpha vantage
        json_stock_data = get_stockprice(stock)
        if json_stock_data is None or 'Time Series (Daily)' not in json_stock_data: 
            failed_stocks.append(stock)
            continue
        # convert stock data into a dataframe and add indicators and take only 2 years back
        stocks_df = convert_dict_to_df(stock, json_stock_data['Time Series (Daily)'])
        with table.batch_writer() as batch:
            # iterate over all the rows in the dataframe
            for index, row in stocks_df.iterrows():
                # convert the index to a string
                date = str(index)
                # create a dictionary of the row data and convert all the values to strings
                row_dict = {key: str(value) for key, value in row.to_dict().items()}
                # add the date to the dictionary
                row_dict['Date'] = date
                # change the stock name to ticker
                row_dict['Stock'] = row_dict.pop('stock')
                # write the data to dynamodb
                batch.put_item(Item=row_dict)
    return failed_stocks

