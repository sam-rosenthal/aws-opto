import pandas as pd
from datetime import datetime
import requests, re, json
import Util.RGScraper as rg

def handler(event, context):
  print('request: {}'.format(json.dumps(event)))
  data = json.loads(event['body'])
  date = data["date"].replace("-","/")
  sport = data["sport"]
  site = data["site"]
  slate = data["slate"]
  slates = rg.getSlates(date, sport, site)  
  s = rg.getSlate(date,sport, site, slate)
  games = s['Games']
  slatePath = s['SlatePath']
  slateCSV = rg.getSlatePlayerData(games, slatePath)
  
  return {
    'statusCode': 200,
    'headers': {
        'Content-Type': 'text/plain',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'OPTIONS,POST'
    },
    'body': json.dumps(slateCSV)
  }
