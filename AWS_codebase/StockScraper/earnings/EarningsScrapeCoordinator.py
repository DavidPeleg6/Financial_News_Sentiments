import pandas as pd
import json
import boto3
import os
import pymysql

client = boto3.client('lambda', region_name='us-east-2')


def lambda_handler(event, context):
    # get data regarding all stocks in the Prices table
    query = """
            SELECT DISTINCT Stock
            FROM Prices;
            """
    # Query the database and load results into a pandas dataframe
    dataframe = pd.read_sql_query(query, connection)
    connection.close()
    sorted_tickers = [t for t in dataframe['stock'].to_list() if 'crypto' not in t.lower() and 'forex' not in t.lower()][:MAX_STOCKS]
        
    for i in range(0, len(sorted_tickers), 5):
        response = client.invoke(
            FunctionName='Collect5stocks',
            # InvocationType='RequestResponse',
            InvocationType='Event',
            Payload=json.dumps({'body': sorted_tickers[i:i+5]})
        )

    return {'statusCode': 200, 'body': 'Success!'}