import os, boto3, json, pandas as pd
from datetime import datetime
def handler(event, context):
  bucket_name = os.environ['BUCKET_NAME']
  print(bucket_name)
  s3_client = boto3.client('s3')
  print('request: {}'.format(json.dumps(event)))
  date = event["Date"]
  sport = event["Sport"]
  fileDir = f"{date}/{sport}/Pinnacle/"
  try:
    response = s3_client.list_objects(Bucket=bucket_name, Prefix=fileDir)
    fullBetsList = []

    # Print the list of files
    for obj in response.get('Contents', []):
      file = obj['Key']
      print(file)
      if '.json' in file:
        try:
          response = s3_client.get_object(Bucket=bucket_name, Key=file)
          contentList = json.loads(response['Body'].read().decode('utf-8'))
          bets = [pd.DataFrame(content['Data']).assign(Timestamp=content['Timestamp']) for content in contentList]
          betsWithTimestamp = pd.concat(bets, ignore_index=True)
          betsWithTimestamp = betsWithTimestamp[['Timestamp', 'Category', 'Matchup', 'Participant', 'Type', 'Title', 'Line', 'Over Odds', 'Under Odds']]
          fullBetsList += betsWithTimestamp.to_dict('records')
        except Exception as e:
          print(e)
          print(f"Error with {file}")
          continue
    if fullBetsList != []:
      fullBetsDF = pd.DataFrame(fullBetsList)
      fullBetsDF = fullBetsDF.sort_values(by=['Title','Matchup']).reset_index(drop=True)
      csv_data = fullBetsDF.to_csv(index=False)  
      fileName = f"{date}/{sport}-odds.csv"
      s3_client.put_object(Bucket=bucket_name, Key=fileName, Body=csv_data)
  except Exception as e:
    print(e)
    print("Couldn't create odds csv")
