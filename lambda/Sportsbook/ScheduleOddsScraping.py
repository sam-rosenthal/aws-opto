import os, boto3, json, Sportsbook.DKScrapingUtil as util, random, time
from datetime import datetime
def handler(event, context):
  lambdaName = os.environ['LAMBDA_NAME']
  print('Lambda name:',lambdaName)
  print('request: {}'.format(json.dumps(event)))
  # data = json.loads(event)
  # sport = data["sport"]
  sports = ["NBA","NFL","NHL"]
  random.shuffle(sports)
  for sport in sports:
    events = util.getEvents(sport)
    print(events)
    eventKeys = list(events.keys())
    if sport in ["NBA","NHL"]:
      eventKeys = eventKeys[:15]
    else:
      eventKeys = eventKeys[:16]
    random.shuffle(eventKeys)
    for event in eventKeys:
      eventId = events[event]['EventId']
      date = datetime.strptime(events[event]['StartDate'],"%Y-%m-%d %H:%M:%S").strftime("%Y/%m/%d")
      payload = {"Event": event, "EventId": eventId, "Date": date, "Sport": sport}
      invokeSaveOdsslambda(lambdaName, payload)
      time.sleep(random.randrange(0,3))
    time.sleep(random.randrange(0,3))
  

def invokeSaveOdsslambda(functionName, payload):
    client = boto3.client('lambda')
    response = client.invoke(
        FunctionName=functionName,
        InvocationType='Event',  # Use 'Event' for asynchronous invocation
        Payload=json.dumps(payload)
    )
    # Optionally, you can handle the response if needed
    print(response)
