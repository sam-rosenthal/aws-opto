def getInverseImpliedOdds(odds):
  if odds == 0 or odds==1:
    return 1000000
  if odds<.5:
    return (1/odds)*100 -100
  else:
    return (100*odds)/(odds-1)

def getProfit(odds):
  odds = float(odds)
  if odds >= 100:
    return odds/100
  else:
    return 100/(-1*odds)
  
def getDecimalOdds(americanOdds):
  americanOdds = float(americanOdds)
  if americanOdds >= 0:
    return 1 + (americanOdds/100)
  else:
    return (americanOdds/100) + 1
  
def getImpliedOdds(odds):
  odds = str(odds)
  odds = odds.replace("−","-")
  odds = odds.replace("âˆ’","-")
  odds = float(odds)
  if odds > 0:
    return 100 / (odds + 100)
  else:
    return odds * -1 / ((odds * -1) + 100)