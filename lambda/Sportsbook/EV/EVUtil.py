import pandas as pd, boto3, re, pytz, numpy as np, math
from datetime import datetime, timedelta
from Sportsbook.EV.OddsUtil import getInverseImpliedOdds, getImpliedOdds, getProfit, getDecimalOdds
from io import StringIO
import logging

def getLatestBetOdds(fileData):
  df = pd.read_csv(fileData, header=0)
  df['Timestamp'] = pd.to_datetime(df['Timestamp'])
  df = df.sort_values(by='Timestamp', ascending=False).groupby('Title').head(1).reset_index(drop=True)
  return df

def getPastHourLatestBetOdds(fileData):
  df = pd.read_csv(fileData, header=0)
  df['Timestamp'] = pd.to_datetime(df['Timestamp'])
  currentTime = datetime.now() - timedelta(hours=4)
  pastHourTime = currentTime - timedelta(hours=1)
  lastTimestamp = df['Timestamp'].iloc[-1]
  print(lastTimestamp, currentTime, pastHourTime)
  df = df[(df['Timestamp'] >= pastHourTime) & (df['Timestamp'] <= currentTime)]
  df = df.sort_values(by='Timestamp', ascending=False).groupby('Title').head(1).reset_index(drop=True)
  return df

def getFileData(bucketName, file):
  s3_client = boto3.client('s3')
  response = s3_client.get_object(Bucket=bucketName, Key=file)
  csv_content = response['Body'].read().decode('utf-8')
  csv_file = StringIO(csv_content)
  # print(csv_file.read())
  return csv_file
  
def getEVBets(bucketName, pinnacleS3File, commercialBookFile):
  logger = logging.getLogger()
  logger.setLevel(logging.INFO)
  pinnacle = getPastHourLatestBetOdds(getFileData(bucketName, pinnacleS3File))
  commercialBook = getPastHourLatestBetOdds(getFileData(bucketName, commercialBookFile))
  commercialBook['Participant'] = commercialBook['Participant'].astype(str)
  commercialBook['Title'] = commercialBook['Title'].astype(str)
  misMatchedTitles = pinnacle[~pinnacle['Title'].isin(commercialBook['Title'])]['Title']
  logger.info("Pinnacle bets: %d", len(pinnacle))
  logger.info("%s bets: %d %s", commercialBookFile, len(commercialBook), commercialBook['Title'].unique())
  logger.info("Total matched bets: %d", len(pinnacle.merge(commercialBook, on='Title')))
  logger.info("Total mismatched bets: %d", len(misMatchedTitles))
  # logger.info("Pinnacle mismatched bet titles: %s", misMatchedTitles.tolist())
  logger.info("%s missing bet titles: %s",commercialBookFile, [title for title in misMatchedTitles.tolist() if "Team Total" not in title])

  df = pinnacle.merge(commercialBook, on='Title')
  df = df[['Timestamp_x', 'Sport_x', 'Category_x', 'Matchup_x', 'Participant_x', 'Type_x',
          'Title', 'Line_x', 'Over Odds_x', 'Under Odds_x', 'Line_y', 'Over Odds_y', 'Under Odds_y']]
  df.columns = df.columns.str.replace('_x', '')
  
  df['PinVigOverOdds'] = df['Over Odds'].apply(getImpliedOdds)
  df['PinVigUnderOdds'] = df['Under Odds'].apply(getImpliedOdds)
  df['PinNoVigOverOdds'] = df['PinVigOverOdds'] / (df['PinVigOverOdds']+df['PinVigUnderOdds'])
  df['PinNoVigUnderOdds'] = df['PinVigUnderOdds'] / (df['PinVigOverOdds']+df['PinVigUnderOdds'])
  df['FVOverLine'] = df['PinNoVigOverOdds'].apply(getInverseImpliedOdds)
  df['FVUnderLine'] = df['PinNoVigUnderOdds'].apply(getInverseImpliedOdds)
  df = df[df['Over Odds_y'].apply(lambda x: not isinstance(x, str) or (isinstance(x, str) and not x.startswith('[') and not x.endswith(']')))]
  df['DKDecimalOver'] = df['Over Odds_y'].apply(getProfit)
  df['DKDecimalUnder'] = df['Under Odds_y'].apply(getProfit)
  df['Line_y'] = df['Line_y'].astype(float)
  df['Line'] = df['Line'].astype(float)
  df['Diff'] = df['Line_y'] - df['Line']
  print(len(df))
  df['EV_Over'] = df.apply(lambda x: (x['DKDecimalOver']*x['PinNoVigOverOdds'])-x['PinNoVigUnderOdds'], axis=1)
  df['EV_Under'] = df.apply(lambda x: (x['DKDecimalUnder']*x['PinNoVigUnderOdds'])-x['PinNoVigOverOdds'], axis=1)
  df['Kelley'] = df.apply(lambda x: (max(x['EV_Over']/x['DKDecimalOver'],x['EV_Under']/x['DKDecimalUnder'])), axis=1)
  df['BetAmount'] = (df['Kelley']/.04)*10
  df['MarketWidth'] =  df.apply(lambda x: abs(abs(x['Over Odds'])-abs(x['Under Odds'])) if x['Over Odds']>0 or x['Under Odds'] > 0 else  abs(abs(x['Over Odds'])+abs(x['Under Odds']))-200, axis=1)
  df = df.sort_values(by='BetAmount',ascending=False)
  return df
  
def rename(title):
  renameDict = {
    "ETSU": "East Tenn State",
    "Green Bay": "Wisc Green Bay",
    "Kansas City": "UMKC",
    "UNC Greensboro": "NC Greensboro",
    "Saint Marys": "Saint Marys CA",   
    "Southeast Missouri State": "SE Missouri State",
    "Saint Thomas MN": "St. Thomas",
    "Milwaukee": "Wisc Milwaukee",
    "SIUE": "SIU Edwardsville",
    "Purdue Fort Wayne": "IPFW",
    "Omaha": "Nebraska Omaha",
    "Detroit Mercy": "Detroit",
    "Charlotte": "Charlotte U",
    "Kennesaw State": "Kennesaw St",
    "UNC Asheville": "NC Asheville",
    "UMBC": "MD Baltimore County",
    "Bethune-Cookman": "Bethune Cookman",
    "UCF": "Central Florida",
    "SFA": "Stephen F. Austin",
    "Saint Josephs": "St. Joseph's",
    "Miami FL": "Miami Florida",
    "McNeese": "McNeese State",    
    "Cal Poly": "Cal Poly SLO",
    "UNCW": "NC Wilmington",
    "Middle Tennessee":"Middle Tennessee State",
    "Southern Mississippi": "Southern Miss",
    "UT Martin": "Tennessee Martin",
    "Louisiana-Lafayette": "UL - Lafayette",
    "FIU": "Florida International",
    "Saint Bonaventure":"St. Bonaventure",
    "Saint Johns": "St. John's",
    "UConn": "Connecticut",
    "Miami OH": "Miami Ohio",
    "DePaul": "Depaul",
    "UTSA": "Texas San Antonio",
    "Texas A&M-Commerce": "Texas A&M Commerce"
  }
  for oldStr, newStr in renameDict.items():
    title = re.sub(oldStr, newStr, title)

  return title

  
def renameEspnCBB(row):
  oldStr = row['Participant']
  if '@' not in oldStr:
    newStr = ' '.join(oldStr.split()[:-1])
    newTitle = row['Title'].replace(oldStr, newStr)
  else:
    s = oldStr.split('@')
    oldStr1 = s[0]
    oldStr2 = s[1]
    newStr1 = ' '.join(oldStr1.split()[:-1])
    newStr2 = ' '.join(oldStr2.split()[:-1])
    newTitle = row['Title'].replace(oldStr1, newStr1)
    newTitle = newTitle.replace(oldStr2, newStr2)
  renameArray = ["Golden", "Sun", "Fighting", "Screaming", "Tar", "Mercy", "Purple", "Nittany", 
                "Black", "Red", "Blue", "Big", "Thundering","Mountain","Delta","Blue","Demon",
                "Horned", "Green", "'"]
  for oldStr in renameArray:
    newTitle = newTitle.replace(oldStr, "")
  newTitle = newTitle.replace('  ', ' ')
  newTitle = newTitle.replace(' @', '@').replace('@ ', '@') 
  return newTitle

def getBestBets(bucketName, date):
  pinnacleS3File = f'{date}/PinnacleOddsData.csv'
  draftkingsS3File = f'{date}/DraftkingsOddsData.csv'
  espnS3File = f'{date}/EspnOddsData.csv'
  fanduelS3File = f'{date}/FanduelOddsData.csv'
  print(pinnacleS3File, draftkingsS3File, espnS3File, fanduelS3File)
  columns = ['Timestamp', 'Sport', 'Category', 'Matchup', 'Participant', 'Type',
        'Title', 'Line', 'Over Odds', 'Under Odds', 'Line_y', 'Over Odds_y',
        'Under Odds_y', 'Diff', 'EV_Over', 'EV_Under', 'Kelley', 'BetAmount',
        'MarketWidth']
  dkBestBets = getEVBets(bucketName, pinnacleS3File, draftkingsS3File)
  dkBestBets = dkBestBets[columns]
  
  espnBestBets = getEVBets(bucketName, pinnacleS3File, espnS3File)
  espnBestBets = espnBestBets[columns]
  
  fdBestBets = getEVBets(bucketName, pinnacleS3File, fanduelS3File)
  fdBestBets = fdBestBets[columns]

  bestBets = dkBestBets.merge(espnBestBets, on=['Timestamp', 'Sport', 'Category', 'Matchup', 'Participant', 'Type','Title','Line', 'Over Odds', 'Under Odds','MarketWidth'], how="outer")
  bestBets = bestBets.merge(fdBestBets, on=['Timestamp', 'Sport', 'Category', 'Matchup', 'Participant', 'Type','Title','Line', 'Over Odds', 'Under Odds','MarketWidth'], how="outer")
  print(len(bestBets), len(dkBestBets), len(espnBestBets), len(fdBestBets))
  bestBets = bestBets.sort_values(by=['Kelley_x'], ascending=False)
  return bestBets

def getPlusEvBets(bucketName, date):
  bestBets = getBestBets(bucketName, date)
  bestBets = bestBets.rename(
    columns={
      'Line':'Line(Pinnacle)',
      'Over Odds':'Over Odds(Pinnacle)',
      'Under Odds':'Under Odds(Pinnacle)',
      'Line_y_x':'Line(Draftkings)',
      'Over Odds_y_x':'Over Odds(Draftkings)',
      'Under Odds_y_x':'Under Odds(Draftkings)',
      'Diff_x':'Diff(Draftkings)',
      'EV_Over_x':'EV_Over(Draftkings)',
      'EV_Under_x': 'EV_Under(Draftkings)',
      'Kelley_x': 'Kelly(Draftkings)',
      'BetAmount_x': 'BetAmount(Draftkings)',
      'Line_y_y':'Line(ESPN)',
      'Over Odds_y_y':'Over Odds(ESPN)',
      'Under Odds_y_y':'Under Odds(ESPN)',
      'Diff_y':'Diff(ESPN)',
      'EV_Over_y':'EV_Over(ESPN)',
      'EV_Under_y':'EV_Under(ESPN)',
      'Kelley_y':'Kelly(ESPN)',
      'BetAmount_y':'BetAmount(ESPN)',
      'Line_y':'Line(Fanduel)',
      'Over Odds_y':'Over Odds(Fanduel)',
      'Under Odds_y':'Under Odds(Fanduel)',
      'Diff':'Diff(Fanduel)',
      'EV_Over':'EV_Over(Fanduel)',
      'EV_Under':'EV_Under(Fanduel)',
      'Kelley':'Kelly(Fanduel)',
      'BetAmount':'BetAmount(Fanduel)'})
  plusEvBets = []
  max_length = max(len(sportsbook) for sportsbook in ['Draftkings', 'ESPN', 'Fanduel', 'Pinnacle'])

  for _, row in bestBets.iterrows():
    bets = []
    extraSpace = f"{' ' * (1+max_length - len('Pinnacle'))}"
    otherBookInfo = f"Pinnacle:{extraSpace}{row[f'Line(Pinnacle)']} | {row['Over Odds(Pinnacle)']} | {row['Under Odds(Pinnacle)']}"
    for sportsbook in ['Draftkings', 'ESPN', 'Fanduel']:
      extraSpace = f"{' ' * (1+max_length - len(sportsbook))}"
      otherBookInfo += f"\n{sportsbook}:{extraSpace}{row[f'Line({sportsbook})']} | {row[f'Over Odds({sportsbook})']} | {row[f'Under Odds({sportsbook})']}".replace(".0","")
      if row[f'Diff({sportsbook})'] == 0:
        sportsbookOdds = {
          "Sportsbook": sportsbook,
          "Line": row[f'Line({sportsbook})'],
          "Over Odds": row[f'Over Odds({sportsbook})'],
          "Under Odds": row[f'Under Odds({sportsbook})'],
          "EV_Over": 0 if math.isnan(row[f'EV_Over({sportsbook})']) else row[f'EV_Over({sportsbook})'],
          "EV_Under": 0 if math.isnan(row[f'EV_Under({sportsbook})']) else row[f'EV_Under({sportsbook})'],
          "Kelly": row[f'Kelly({sportsbook})'],
          "Bet Amount": row[f'BetAmount({sportsbook})']
          }

        bets.append(sportsbookOdds)
    if len(bets) == 0:
      continue
    bestOverOdds = max(bets, key=lambda x: x['EV_Over'])
    bestUnderOdds = max(bets, key=lambda x: x['EV_Under'])
    
    if round(max(bestOverOdds['EV_Over'], bestUnderOdds['EV_Under']),2) > 0:
      bestBet = {
        'Participant': row['Participant'],
        'Type': row['Type'],
      }
      if bestOverOdds['EV_Over'] > bestUnderOdds['EV_Under']:
        bestBet['Bet'] = f"Over {bestOverOdds['Line']}"
        bestBet['Book'] = bestOverOdds['Sportsbook']
        bestBet['Odds'] = bestOverOdds['Over Odds']
        bestBet['EV'] = round(bestOverOdds['EV_Over'],3)
        bestBet['Kelly'] = round(bestOverOdds['Kelly'],3)
      else:
        bestBet['Bet'] = f"Under {bestUnderOdds['Line']}"
        bestBet['Book'] = bestUnderOdds['Sportsbook']
        bestBet['Odds'] = bestUnderOdds['Under Odds']
        bestBet['EV'] = round(bestUnderOdds['EV_Under'],3)
        bestBet['Kelly'] = round(bestUnderOdds['Kelly'],3)
        
      bestBet['Bet Amount'] = (bestBet['Kelly']/.04)*10
      bestBet['Market Width'] = row['MarketWidth']
      
      bestBet['otherBookInfo'] = otherBookInfo
      bestBet['Sport'] = row['Sport']
      bestBet['Category'] = row['Category']
      bestBet['Matchup'] = row['Matchup']
      bestBet['Timestamp'] = row['Timestamp']   
      
      plusEvBets.append(bestBet)

  return pd.DataFrame(plusEvBets).sort_values(by='Kelly', ascending=False)