import pandas as pd
import json
import boto3
import os
from sqlalchemy import create_engine, text

# The maximum number of stocks to scrape
MAX_STOCKS = 1000

client = boto3.client('lambda', region_name='us-east-2')


def lambda_handler(event, context):
    # get data from the past month unless specified to take the entire dataframe
    query = """
            SELECT stock, COUNT(*) AS frequency 
            FROM Sentiments 
            WHERE time_published >= DATE_SUB(NOW(), INTERVAL 1 MONTH)
            GROUP BY stock 
            ORDER BY frequency DESC;
            """
    # Query the database and load results into a pandas dataframe
    engine = create_engine(f"mysql+pymysql://{os.environ['ID']}:{os.environ['PASS']}@{os.environ['URL']}/stock_data", echo=False)
    with engine.connect() as connection:
        dataframe = pd.read_sql_query(sql=text(query), con=connection)
    
    sorted_tickers = [t for t in dataframe['stock'].to_list() if 'crypto' not in t.lower() and 'forex' not in t.lower()][:MAX_STOCKS]
       
    for i in range(0, len(sorted_tickers), 5):
        response = client.invoke(
            FunctionName='Collect5stocks',
            # InvocationType='RequestResponse',
            InvocationType='Event',
            Payload=json.dumps({'body': sorted_tickers[i:i+5]})
        )

    return {'statusCode': 200, 'body': 'Success!'}