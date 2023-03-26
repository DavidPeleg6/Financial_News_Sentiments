import boto3
from external_api_comm import get_stockprice, convert_dict_to_df


dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
table = dynamodb.Table('StockPrices')


def lambda_handler(event, context):
    write_stocks(event['body'])


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
