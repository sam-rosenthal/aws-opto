import os, boto3, json, time
def handler(event, context):
  pinnacleLambda = os.environ['PINNACLE']
  fanduelLambda = os.environ['FANDUEL']
  draftkingsLambda = os.environ['DRAFTKINGS']
  espnLambda = os.environ['ESPN']
  print('Pinnacle Lambda:',pinnacleLambda)
  print('Fanduel Lambda:',fanduelLambda)
  print('Draftkings Lambda:',draftkingsLambda)
  print('Espn Lambda:',espnLambda)
  print('request: {}'.format(json.dumps(event)))
  data = json.loads(json.dumps(event))
  sportsbooks = data["Sportsbooks"]
  sports = data["Sports"]
  for sport in sports:
    for sportsbook in sportsbooks:
      lambdaName = getLambdaName(sportsbook)
      payload = {"Sport": sport}
      print(sport, sportsbook)
      invokeSaveOddslambda(lambdaName, payload)
      time.sleep(5)
    

def getLambdaName(sportsbook):
  if sportsbook == "Draftkings":
    return os.environ['DRAFTKINGS']
  elif sportsbook == "Fanduel":
    return os.environ['FANDUEL']
  elif sportsbook == "Pinnacle":
    return os.environ['PINNACLE']
  elif sportsbook == "Espn":
    return os.environ['ESPN']
  else:
    return None
  
def invokeSaveOddslambda(functionName, payload):
  client = boto3.client('lambda')
  response = client.invoke(
    FunctionName=functionName,
    InvocationType='Event',  # Use 'Event' for asynchronous invocation
    Payload=json.dumps(payload)
  )
  # Optionally, you can handle the response if needed
  print(response)
