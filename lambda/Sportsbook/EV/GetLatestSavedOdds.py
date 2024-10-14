import pandas as pd, json, boto3, os
from datetime import datetime
from Sportsbook.EV.EVUtil import getFileData, getLatestBetOdds

def handler(event, context):
  bucketName = os.environ['BUCKET_NAME']
  print(bucketName)
  print('request: {}'.format(json.dumps(event)))
  data = json.loads(event['body'])
  date = data["date"]
  sportsbook = data["sportsbook"]
  fileName = f'{date}/{sportsbook}OddsData.csv'
  try:
    fileData = getFileData(bucketName, fileName)
    latestSavedOdds = getLatestBetOdds(fileData).to_csv(index=False)
    # print(evBets)
    return {
      'statusCode': 200,
      'headers': {
          'Content-Type': 'text/plain',
          'Access-Control-Allow-Headers': 'Content-Type',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'OPTIONS,POST'
      },
      'body': json.dumps(latestSavedOdds)
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
