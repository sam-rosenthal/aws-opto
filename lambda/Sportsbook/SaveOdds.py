import os, boto3, pytz, json, Sportsbook.DKScrapingUtil as util, random, time
from datetime import datetime
def handler(event, context):
  bucket_name = os.environ['BUCKET_NAME']
  print(bucket_name)
  s3_client = boto3.client('s3')
  print('request: {}'.format(json.dumps(event)))
  
  date = event["Date"]
  game = event["Event"]
  eventId = event["EventId"]  
  sport = event["Sport"]  
  file = f"{date}/{sport}/Draftkings/{game}.json"
  print(date, file, eventId)
  odds = util.getOdds(eventId)   
  try:
    # Check if the object exists
    response = s3_client.get_object(Bucket=bucket_name, Key=file)
    json_content = json.loads(response['Body'].read().decode('utf-8'))
    print("File exists",file)
    json_content.append(odds)
    s3_client.put_object(Bucket=bucket_name, Key=file, Body=json.dumps(json_content), ContentType='text/json')
  except Exception as e:
    # print(e)      
    print("File doesn't exist, creating file",game)
    s3_client.put_object(Bucket=bucket_name, Key=file, Body=json.dumps([odds]), ContentType='text/json')



  # print(events)
  # eventKeys = list(events.keys())
  # random.shuffle(eventKeys)
  # for event in eventKeys:
  #   print(event)
  #   eventId = events[event]['EventId']
  #   date = events[event]['StartDate'].strptime("%Y-%m-%d %H:%M:%S").strftime("%Y/%m/%d")
  #   file = f"{date}/{event}.json"
  #   odds = util.getOdds(eventId)   
  #   try:
  #     # Check if the object exists
  #     response = s3_client.get_object(Bucket=bucket_name, Key=file)
  #     json_content = json.loads(response['Body'].read().decode('utf-8'))
  #     print("File exists",file)
  #     json_content.append(odds)
  #     s3_client.put_object(Bucket=bucket_name, Key=file, Body=json.dumps(json_content), ContentType='text/json')
  #   except Exception as e:
  #     print(e)      
  #     print("File doesn't exist, creating file",event)
  #     s3_client.put_object(Bucket=bucket_name, Key=file, Body=json.dumps([odds]), ContentType='text/json')
              
  #   time.sleep(random.randrange(0,3))

