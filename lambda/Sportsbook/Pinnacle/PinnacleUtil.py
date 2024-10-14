from datetime import timezone, datetime
import random, requests, pytz, time, logging

class PinnacleScraper():
  def __init__(self, sport="NFL"):
    self.sport = sport
    self.logger = logging.getLogger()
    self.logger.setLevel(logging.INFO)
    self.session = requests.Session()
    self.apiKey = self.getApiKeyWithRetry()
    self.setAvailableBets()
    self.setMatchups()
    
  def scrapeOdds(self):
    if self.sport in ["WTA","ATP"]:
      self.getTennisData()
    else:
      self.getPlayerPropBets()
      self.getMatchupBets()
    
  def getOdds(self):
    self.scrapeOdds()
    timestamp = self.setTimestamp()
    return {"Timestamp": timestamp, "Data": self.matchups}

  def getApiKey(self):
    url = 'https://www.pinnacle.com/config/app.json'
    response = self.session.get(url)
    try:
      configData = response.json()
      return configData['api']['haywire']['apiKey']
    except Exception as e:
      self.logger.info(f"Failed to get api key. Exception: {e}. Response text: {response.text}")
      raise e
  
  def getApiKeyWithRetry(self):
    return self.getApiKey()
    
  def getUserAgent(self):
    agents = [
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
      "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
      "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15"
    ]
    return random.choice(agents)
    

  def getApiData(self, url):
    headers = { 
               'x-api-key': self.apiKey,
               "User-Agent": self.getUserAgent(),
               "Accept": "application/json",
               "Accept-Language": "en-US,en;q=0.9",
               "Content-Type": "application/json",
               "Referer": "https://www.pinnacle.com/"
               }
    self.requestOptions = { 'headers': headers }
    response = self.session.get(url, **self.requestOptions)
    try:
      return response.json()
    except Exception as e:
      self.logger.info(f"Failed to get api data. Exception: {e}. Response text: {response.text}")
      raise e
  
  def getApiDataWithRetry(self, url):
    return self.getApiData(url)
    # try:
    #   return self.getApiData(url)
    # except Exception as e:
    #   print("Retrying getApiData")
    #   time.sleep(5)
    #   return self.getApiData(url)
  
  def setAvailableBets(self):
    self.sportIds = {
      "NFL": "889",
      "NCAAF": "880",
      "NCAAM": "493",
      "NHL": "1456",
      "NBA": "487",
      "UFC": "1624",
      "WNCAA": "583",
      "MLB": "246",
    }
    self.availableBets = []
    if self.sport not in ["ATP","WTA"]:
      leagueIds = [self.sportIds[self.sport]]
    else:
      leagueIds = self.getLeagueIds()
    
    for leagueId in leagueIds:
      url = f'https://guest.api.arcadia.pinnacle.com/0.1/leagues/+{leagueId}/matchups?brandId=0'
      data = self.getApiDataWithRetry(url)
      currTime = datetime.now().astimezone(pytz.timezone('America/New_York'))
      self.availableBets.extend([d for d in data if self.getStartTime(d['startTime']) > currTime])
      
    
  def setMatchups(self):
    self.matchups = {}
    leagueName = self.sport if "NCAA" not in self.sport or self.sport == "WNCAA" else "NCAA"
    for bet in self.availableBets:
      matchupName = self.getMatchupName(bet)
      if matchupName is None:
        continue
      if matchupName not in self.matchups:
        self.matchups[matchupName] = {}
        self.matchups[matchupName]['Bets'] = []
        if bet['parent'] is not None:
          # self.matchups[matchupName]['id'] = bet['parent']['id']
          self.matchups[matchupName]['StartTime'] = self.formatStartTime(bet['parent']['startTime'])
      
      if bet['type'] == 'special' or (self.sport not in ["ATP","WTA"] and (bet['league']['name'] != leagueName or bet['units'] != 'Regular')):
        continue
      
      if len(bet['participants']) > 0 and "Goal" in bet['participants'][0]['name']:
        continue
      
      self.matchups[matchupName]['StartTime'] = self.formatStartTime(bet['startTime'])
      self.matchups[matchupName]['id'] = bet['id']

      homeTeam = next((team['name'] for team in bet['participants'] if team['alignment'] == 'home'), None)
      awayTeam = next((team['name'] for team in bet['participants'] if team['alignment'] == 'away'), None)

      self.matchups[matchupName]['home'] = homeTeam.replace(" (Games)","") if homeTeam is not None else None
      self.matchups[matchupName]['away'] = awayTeam.replace(" (Games)","") if awayTeam is not None else None
        
  def getMatchupName(self, bet):
    participants = bet['parent']['participants'] if bet['parent'] is not None else bet['participants']
    homeTeam = next((team['name'] for team in participants if team['alignment'] == 'home'), None)
    awayTeam = next((team['name'] for team in participants if team['alignment'] == 'away'), None)
    if homeTeam is not None and awayTeam is not None:
      if self.sport in ["UFC", "WTA", "ATP"]:
        teams = [awayTeam, homeTeam]
        teams.sort()
        return f"{teams[0]}@{teams[1]}"
      else:
        return f"{awayTeam}@{homeTeam}"
    elif awayTeam is None and homeTeam is not None: 
      # print(bet)
      return homeTeam
    elif awayTeam is not None and homeTeam is None:
      # print(bet)
      return awayTeam
    else:
      # print(bet)
      return       

  def setTimestamp(self):
    timestamp = datetime.now().astimezone(pytz.timezone('America/New_York')).strftime('%Y/%m/%d %H:%M:%S')
    return timestamp

  def getStartTime(self, startTime):
    try:
      return datetime.strptime(startTime, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.UTC).astimezone(pytz.timezone('America/New_York'))
    except:
      return datetime.strptime(startTime, "%Y-%m-%dT%H:%M:%S%z").replace(tzinfo=pytz.UTC).astimezone(pytz.timezone('America/New_York'))
  
  def formatStartTime(self, startTime):
    return self.getStartTime(startTime).strftime('%Y/%m/%d %H:%M:%S')
  
  def getDate(self, startTime):
    return datetime.strptime(startTime,'%Y/%m/%d %H:%M:%S').strftime('%Y/%m/%d')
    
  def getPlayerPropBets(self):
    data = []
    playerProps = self.filterAvailableBetsForPlayerProps()
    for playerProp in playerProps:
      propData = self.getApiDataWithRetry(f"https://guest.api.arcadia.pinnacle.com/0.1/matchups/{playerProp['id']}/markets/straight")
      if len(propData) < 1:
        continue
      propData = propData[0]
      playerName, propDesc = self.parsePlayerPropDescription(playerProp['special']['description'])
      try:
        points, priceA, priceB = self.extractPropData(propData)
      except Exception as e:
        self.logger.info(f"Skipping bet: {playerName}, {propDesc}. Exception: {e}. PropData: {propData}")
        continue
      
      matchup = self.getMatchupName(playerProp)
      betInfo = {'Category': 'Prop', 'Matchup': matchup,
                 'Participant': playerName, 'Type': propDesc, 
                 'Title': f'{playerName} {propDesc}', 'Line': points, 
                 'Over Odds': priceA, 'Under Odds': priceB}
      self.matchups[matchup]['Bets'].append(betInfo)
      data.append(betInfo)
    timeStamp = self.setTimestamp()
    # return {"Timestamp": timeStamp, "Data": data}

  def filterAvailableBetsForPlayerProps(self):
    return [matchup for matchup in self.availableBets
            if 'special' in matchup.keys() and matchup['special'] is not None
            and matchup['special']['category'] == "Player Props"
            and matchup['units'] not in ["Last Touchdown", "1st Touchdown", "LongestPassComplete", "LongestReception", "KickingPoints"]]
  
  def extractPropData(self, propData):
    points = propData['prices'][0]['points']
    prices = sorted(propData['prices'], key=lambda x: x['participantId'])
    priceA = prices[0]['price']
    priceB = prices[1]['price']
    return points, priceA, priceB

  def parsePlayerPropDescription(self, description):
    description = description.replace("(must start)","")
    parts = description.split(' (')
    playerName = parts[0]
    propDesc = parts[1].replace(')', '')
    propDesc = propDesc.replace("Saves(must start","Saves")
    return playerName, propDesc
  
  def getMatchupBets(self):
    self.betData = {}
    for matchupName, matchupInfo in self.matchups.items():
      self.logger.info(f"{matchupName} {matchupInfo}")
      if 'id' in matchupInfo:
        matchupId = matchupInfo['id']
        self.processMatchupId(matchupId, matchupName)
    return self.matchups

  def processMatchupId(self, matchupId, matchupName):
    bettingData = self.getApiDataWithRetry(f"https://guest.api.arcadia.pinnacle.com/0.1/matchups/{matchupId}/markets/related/straight")
    # print(len(bettingData))
    self.resetProcessedFlags()
    for line in bettingData:
      # print(line)
      self.updateBettingData(line, matchupId, matchupName, "home")
      self.updateBettingData(line, matchupId, matchupName, "away")
      if self.hasProcessed['Game Total'] and all(self.hasProcessed['home'].values()) and all(self.hasProcessed['away'].values()):
        self.resetProcessedFlags()
        return
  
  def updateBettingData(self, line, matchupId, matchupName, teamType):
    teamName = self.matchups[matchupName][teamType]
    oppTeamType = "away" if teamType == "home" else "home"
    if line['key'] == "s;0;m" and self.isMatchupMainBet(line, matchupId):
      moneyline = next(price['price'] for price in line['prices'] if price['designation'] == teamType)
      oppTeamMoneyline = next(price['price'] for price in line['prices'] if price['designation'] == oppTeamType)
      betInfo = {'Category': 'Matchup', 'Matchup': matchupName, 
                 'Participant': teamName, 'Type':'MoneyLine', 
                 'Title': f'{teamName} MoneyLine', 'Line': -.5,
                 'Over Odds': moneyline, 'Under Odds': oppTeamMoneyline}
      self.matchups[matchupName]['Bets'].append(betInfo)
      self.hasProcessed[teamType]['MoneyLine'] = True

    if "s;0;s;" in line['key'] and self.isMatchupMainBet(line, matchupId):
      spread = next(price['points'] for price in line['prices'] if price['designation'] == teamType)
      teamSpreadOdds = next(price['price'] for price in line['prices'] if price['designation'] == teamType)
      oppTeamSpreadOdds = next(price['price'] for price in line['prices'] if price['designation'] == oppTeamType)
      betInfo = {'Category': 'Matchup', 'Matchup': matchupName, 
                 'Participant': teamName, 'Type': 'Spread', 
                 'Title': f'{teamName} Spread', 'Line': spread,
                 'Over Odds': teamSpreadOdds, 'Under Odds': oppTeamSpreadOdds}
      self.matchups[matchupName]['Bets'].append(betInfo)
      self.hasProcessed[teamType]['Spread'] = True

    if "s;0;ou;" in line['key'] and self.isMatchupMainBet(line, matchupId) and not self.hasProcessed['Game Total']:
      overUnder = line['prices'][0]['points']
      overPrice = next(price['price'] for price in line['prices'] if price['designation'] == 'over')
      underPrice = next(price['price'] for price in line['prices'] if price['designation'] == 'under')
      betInfo = {'Category': 'Matchup', 'Matchup': matchupName, 
                 'Participant': matchupName, 'Type': 'Game Total',
                 'Title': f'{matchupName} Game Total', 'Line': overUnder, 
                 'Over Odds': overPrice, 'Under Odds': underPrice}
      self.matchups[matchupName]['Bets'].append(betInfo)
      self.hasProcessed['Game Total'] = True

    if "s;0;tt;" in line['key'] and line['side'] == teamType and self.isMatchupMainBet(line, matchupId):
      teamTotal = line['prices'][0]['points']
      teamOverPrice = next(price['price'] for price in line['prices'] if price['designation'] == 'over')
      teamUnderPrice = next(price['price'] for price in line['prices'] if price['designation'] == 'under')
      betInfo = {'Category': 'Matchup', 'Matchup': matchupName, 
                 'Participant': teamName, 'Type': 'Team Total',
                 'Title': f'{teamName} Team Total', 'Line': teamTotal, 
                 'Over Odds': teamOverPrice, 'Under Odds': teamUnderPrice}
      self.matchups[matchupName]['Bets'].append(betInfo)
      self.hasProcessed[teamType]['Team Total'] = True

  def isMatchupMainBet(self, line, matchupId):
    return ('isAlternate' in line.keys() and not line['isAlternate']) and line['matchupId'] == matchupId
    # return {"Moneyline": moneyline, "Spread": spread, "Over/Under": overUnder, "OverPrice": overPrice, 
    #         "UnderPrice": underPrice, "Team Over/Under": teamTotal, "Team OverPrice": teamOverPrice, 
    #         "Team UnderPrice": teamUnderPrice, "Team Total": teamTotal}

  def resetProcessedFlags(self):
    self.hasProcessed = {'Game Total': False}
    self.hasProcessed['home'] = {'MoneyLine': False, 'Spread': False, 'Team Total': False}
    self.hasProcessed['away'] = {'MoneyLine': False, 'Spread': False, 'Team Total': False}

  def getTennisData(self):
    for playerProp in self.availableBets:
      propData = self.getApiDataWithRetry(f"https://guest.api.arcadia.pinnacle.com/0.1/matchups/{playerProp['id']}/markets/straight")
      if len(propData) < 1:
        continue
      matchup = self.getMatchupName(playerProp)
      for pd in propData:
       self.updateBettingDataForTennis(pd, matchup, playerProp['units'])
 
  def updateBettingDataForTennis(self, line, matchupName, units):
    if 'isAlternate' in line and not line['isAlternate']:
      parts = line['key'].split(';')
      set_number = int(parts[1])
      bet_type = parts[2]
      betInfo = {}
      
      if bet_type == 's':
        for teamType in ['home', 'away']:
          teamName = self.matchups[matchupName][teamType]
          oppTeamType = "away" if teamType == "home" else "home"
          
          spread = next(price['points'] for price in line['prices'] if price['designation'] == teamType)
          teamSpreadOdds = next(price['price'] for price in line['prices'] if price['designation'] == teamType)
          oppTeamSpreadOdds = next(price['price'] for price in line['prices'] if price['designation'] == oppTeamType)
          betInfo = {
            'Category': 'Matchup' if set_number == 0 else f'{set_number}st Set', 
            'Matchup': matchupName, 
            'Participant': teamName, 
            'Type': f'Spread ({units})', 
            'Title': f'{teamName} Spread ({units})' if set_number == 0 else f'{teamName} {set_number}st Set Spread ({units})',
            'Line': spread, 
            'Over Odds': teamSpreadOdds, 
            'Under Odds': oppTeamSpreadOdds
          }
          self.matchups[matchupName]['Bets'].append(betInfo)
      elif bet_type == 'ou':
        over_under_value = float(parts[3])
        # overUnder = line['prices'][0]['points']
        overPrice = next(price['price'] for price in line['prices'] if price['designation'] == 'over')
        underPrice = next(price['price'] for price in line['prices'] if price['designation'] == 'under')
        betInfo = {
          'Category': 'Matchup' if set_number == 0 else f'{set_number}st Set', 
          'Matchup': matchupName, 
          'Participant': matchupName,
          'Type': f'Total ({units})',
          'Title': f'{matchupName} Total ({units})' if set_number == 0 else f'{matchupName} {set_number}st Set Total ({units})', 
          'Line': over_under_value, 
          'Over Odds': overPrice, 'Under Odds': underPrice
        }
        self.matchups[matchupName]['Bets'].append(betInfo)
      elif bet_type == 'tt':
        teamType = parts[4]
        teamName = self.matchups[matchupName][teamType]
        oppTeamType = "away" if teamType == "home" else "home"
          
        teamTotal = float(parts[3])
        teamOverPrice = next(price['price'] for price in line['prices'] if price['designation'] == 'over')
        teamUnderPrice = next(price['price'] for price in line['prices'] if price['designation'] == 'under')
        betInfo = {
          'Category':'Matchup' if set_number == 0 else f'{set_number}st Set', 
          'Matchup': matchupName, 
          'Participant': teamName, 
          'Type': f'Team Total ({units})',
          'Title': f'{teamName} Team Total ({units})', 
          'Line': teamTotal, 
          'Over Odds': teamOverPrice, 
          'Under Odds': teamUnderPrice
        }
        self.matchups[matchupName]['Bets'].append(betInfo)
      elif bet_type == 'm':
        for teamType in ['home', 'away']:
          teamName = self.matchups[matchupName][teamType]
          oppTeamType = "away" if teamType == "home" else "home"
          
          moneyline = next(price['price'] for price in line['prices'] if price['designation'] == teamType)
          oppTeamMoneyline = next(price['price'] for price in line['prices'] if price['designation'] == oppTeamType)
          betInfo = {
            'Category':'Matchup' if set_number == 0 else f'{set_number}st Set', 
            'Matchup': matchupName, 
            'Participant': teamName, 
            'Type':'MoneyLine',
            'Title': f'{teamName} MoneyLine' if set_number == 0 else f'{teamName} {set_number}st Set MoneyLine', 
            'Line': -.5,
            'Over Odds': moneyline, 
            'Under Odds': oppTeamMoneyline
          }
          self.matchups[matchupName]['Bets'].append(betInfo)
  
  def getSportIds(self):
    url = "https://guest.api.arcadia.pinnacle.com/0.1/sports?brandId=0"
    response = self.getApiData(url)
    return {entry['name']: entry['id'] for entry in response}
    
  def getLeagues(self):
    if self.sport in ["WTA", "ATP"]:
      sportId = self.getSportIds()["Tennis"]
    else:
      sportId = self.getSportIds()[self.sport]
    url = f"https://guest.api.arcadia.pinnacle.com/0.1/sports/{sportId}/leagues?all=false&brandId=0"
    response = self.getApiData(url)
    league_mapping = {entry['name']: entry['id'] for entry in response}
    return league_mapping

  def getAussieOpenIds(self):
    return [str(value) for key, value in self.getLeagues().items() if f"{self.sport} Australian Open - " in key]
  
  def getLeagueIds(self):
    return [str(value) for key, value in self.getLeagues().items() if self.sport in key]