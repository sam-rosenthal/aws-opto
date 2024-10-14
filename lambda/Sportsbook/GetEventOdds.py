import time, random, json, requests
import Sportsbook.DKScrapingUtil as util

# def helper():
#   sports = ["NFL","NHL","NBA"]
#   random.shuffle(sports)
#   data = []
#   for sport in sports:
#   # for sport in ["NBA"]:
#     print(sport)
#     events = util.getEvents(sport)
#     games = list(events.keys())[:15]
#     random.shuffle(games)
#     for game in games:
#       print(game)
#       # print(game.getEventId())
#       time.sleep(random.randrange(0,3))
#       data.append(util.getOdds(sport, events[game]['StartDate'], events[game]['EventId'], game)['Timestamp'])
#     time.sleep(random.randrange(5,10))
  
#   return data
  

def handler(event, context):
  print('request: {}'.format(json.dumps(event)))
  data = json.loads(event['body'])
  eventId = data['eventId']
  oddsData = util.getOdds(eventId)
  # data = helper()
  return {
    'statusCode': 200,
    'headers': {
        'Content-Type': 'text/plain',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'OPTIONS,POST'
    },
    'body': json.dumps(oddsData)
  }
