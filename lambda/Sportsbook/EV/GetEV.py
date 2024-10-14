import pandas as pd, json, boto3, os
from datetime import datetime
from Sportsbook.EV.EVUtil import getEVBets

def handler(event, context):
  bucket_name = os.environ['BUCKET_NAME']
  print(bucket_name)
  print('request: {}'.format(json.dumps(event)))
  data = json.loads(event['body'])
  date = data["date"]
  site = data["site"]
  pinnacleS3File = f'{date}/PinnacleOddsData.csv'
  commercialBookS3File = f'{date}/{site}OddsData.csv'
  print(pinnacleS3File, commercialBookS3File)
  try:
    evBets = getEVBets(bucket_name, pinnacleS3File, commercialBookS3File).to_csv(index=False)
    # print(evBets)
    return {
      'statusCode': 200,
      'headers': {
          'Content-Type': 'text/plain',
          'Access-Control-Allow-Headers': 'Content-Type',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'OPTIONS,POST'
      },
      'body': json.dumps(evBets)
    }
  except Exception as e:
    print(e)
    return {
      'statusCode': 400,
      'headers': {
          'Content-Type': 'text/plain',
          'Access-Control-Allow-Headers': 'Content-Type',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'OPTIONS,POST'
      },
      'body': "Failed to get ev bets"
    } 
