import pandas as pd
import json
import boto3
import os
from sqlalchemy import create_engine, text

client = boto3.client('lambda', region_name='us-east-2')


def lambda_handler(event, context):
    # get data regarding all stocks in the Prices table
    query = text("""SELECT DISTINCT Stock FROM Prices;""")
    # Query the database and load results into a pandas dataframe
    engine = create_engine(f"mysql+pymysql://{os.environ['ID']}:{os.environ['PASS']}@{os.environ['URL']}/stock_data", echo=False)
    with engine.connect() as connection:
        dataframe = pd.read_sql_query(sql=query, con=connection)
        
    sorted_tickers = sorted(dataframe['Stock'].tolist())
    
    for i in range(0, len(sorted_tickers), 5):
        response = client.invoke(
            FunctionName='Collect5earnings',
            # InvocationType='RequestResponse',
            InvocationType='Event',
            Payload=json.dumps({'body': sorted_tickers[i:i+5]})
        )