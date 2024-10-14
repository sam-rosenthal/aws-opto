import os, io, boto3, pytz, json, Sportsbook.Draftkings.DraftkingsUtil as util, pandas as pd
from datetime import datetime
def handler(event, context):
  bucket_name = os.environ['BUCKET_NAME']
  print(bucket_name)
  s3_client = boto3.client('s3')
  print('request: {}'.format(json.dumps(event)))
  sport = event['Sport']  
  oddsData = util.DraftkingsScraper(sport).getOdds()
  updatedFiles = {}
  for matchup, matchupInfo in oddsData['Data'].items():
    try:
      betDataList = []
      date = datetime.strptime(matchupInfo['StartTime'],'%Y/%m/%d %H:%M:%S').strftime('%Y/%m/%d')
      print(date,matchup,len(matchupInfo['Bets']))
      file = f'{date}/DraftkingsOddsData.csv'
      for bet in matchupInfo['Bets']:
        d = {
          "Timestamp": oddsData['Timestamp'],
          "Sport": sport,
          **bet
        }
        betDataList.append(d)
      
      if file not in updatedFiles:
        try:
          # Check if the object exists
          response = s3_client.get_object(Bucket=bucket_name, Key=file)
          print('File exists, getting file',file, "and adding betting data")
          updatedFiles[file] = pd.read_csv(response['Body'])
        except Exception as e:
          print('File doesn\'t exist, creating file',file)
          updatedFiles[file] = pd.DataFrame()
      
      new_records = pd.DataFrame(betDataList)
      updatedFiles[file] = pd.concat([updatedFiles[file], new_records], ignore_index=True)
    except Exception as e:
      print('Error processing matchup',matchup,e)
      continue
    
  for file in updatedFiles:
    print('Writing file',file)
    csv_buffer = io.StringIO()
    updatedFiles[file].to_csv(csv_buffer, index=False)
    s3_client.put_object(Body=csv_buffer.getvalue().encode('utf-8'), Bucket=bucket_name, Key=file)
