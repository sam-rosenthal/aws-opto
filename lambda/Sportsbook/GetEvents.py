import json
import Sportsbook.DKScrapingUtil as util

def handler(event, context):
  print('request: {}'.format(json.dumps(event)))
  data = json.loads(event['body'])
  sport = data["sport"]
  events = util.getEvents(sport)
  # events = list(util.getEvents(sport).keys())

  return {
    'statusCode': 200,
    'headers': {
        'Content-Type': 'text/plain',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'OPTIONS,POST'
    },
    'body': json.dumps(events)
  }
