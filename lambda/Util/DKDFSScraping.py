import sys, requests, re, csv, json, pandas as pd
from datetime import datetime
from io import StringIO 
def getContestStructureCSV(contestId):
  contestDetails = requests.get('https://api.draftkings.com/contests/v1/contests/'+str(contestId)+'?format=json').json()['contestDetail']
  payouts = contestDetails['payoutSummary']
  contestSize = contestDetails['entries']
  entryFee = contestDetails['entryFee']
  output = StringIO()
  writer = csv.writer(output) 
  writer.writerow(['Place', 'Payout', 'Field Size', 'Entry Fee'])
  place = str(payouts[0]['minPosition']) + "-" + str(payouts[0]['maxPosition']) if payouts[0]['minPosition'] != payouts[0]['maxPosition'] else payouts[0]['minPosition']
  payout = "$" + str(payouts[0]['payoutDescriptions'][0]['value'])
  writer.writerow([place, payout, contestSize, entryFee])

  # Iterate over the payouts and write each row
  for d in payouts[1:]:
    place = str(d['minPosition']) + "-" + str(d['maxPosition']) if d['minPosition'] != d['maxPosition'] else d['minPosition']
    payout = "$" + str(d['payoutDescriptions'][0]['value'])
    writer.writerow([place, payout])
  
  return output.getvalue() 
      