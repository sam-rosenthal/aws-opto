import os, boto3, json, Sportsbook.DKScrapingUtil as util, pandas as pd
from datetime import datetime
def handler(event, context):
  bucket_name = os.environ['BUCKET_NAME']
  print(bucket_name)
  s3_client = boto3.client('s3')
  print('request: {}'.format(json.dumps(event)))
  date = event["Date"]
  sport = event["Sport"]
  fileDir = f"{date}/{sport}/Draftkings/"
  try:
    response = s3_client.list_objects(Bucket=bucket_name, Prefix=fileDir)
    flatList = []
    for obj in response.get('Contents', []):
      file = obj['Key']
      print(file)
      if '.json' in file:
        try:
          response = s3_client.get_object(Bucket=bucket_name, Key=file)
          fileData = json.loads(response['Body'].read().decode('utf-8'))
          betsList = util.getPropsList(sport, fileData)
          flatList += betsList
        except Exception as e:
          print(e)
          print(f"Error with {file}")
          continue
    if flatList != []:
      df = pd.DataFrame(flatList)
      df_sorted = df.sort_values(by=['Matchup','Title']).reset_index(drop=True)
      csv_data = df_sorted.to_csv(index=False)  
      fileName = f"{date}/{sport}-odds.csv"
      s3_client.put_object(Bucket=bucket_name, Key=fileName, Body=csv_data)
  except Exception as e:
    print(e)
    print("Couldn't create odds csv")
