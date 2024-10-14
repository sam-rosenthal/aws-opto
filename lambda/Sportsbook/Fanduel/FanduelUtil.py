import requests, pytz, re, random
from random import uniform
from datetime import datetime
from time import sleep  
class FanduelScraper:
  def __init__(self, sport="NFL"):
    self.sport = sport
    self.session = requests.Session()

    # self.session.get("https://sbapi.va.sportsbook.fanduel.com/api/event-page?_ak=FhMFpcPWXMeyZxOx&eventId=32862320", headers=getHeaders()).text
    self.FD_SPORTS_LIST = ["NFL","NHL","NCAAB","NCAAF","NBA","PGA","UFC"]
    self.FD_EVENT_TYPES={"Basketball":"7522"}
    self.FD_COMPETITION_IDS = {"NBA":"10547864"}
    self.matchups = {}

  def setTimestamp(self):
    timestamp = datetime.now().astimezone(pytz.timezone('America/New_York')).strftime('%Y/%m/%d %H:%M:%S')
    return timestamp
    
  def getOdds(self):
    self.scrapeOdds()
    timestamp = self.setTimestamp()
    return {"Timestamp": timestamp, "Data": self.matchups}
  
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
    
    
  def getHeaders(self):
    
    headers = {
      "accept": "application/json",
      "accept-language": "en-US,en;q=0.9",
      "origin": "https://va.sportsbook.fanduel.com",
      "priority": "u=1, i",
      "referer": "https://va.sportsbook.fanduel.com/",
      "user-agent": self.getUserAgent(),
    }
    return headers

  def sleep(self):
    sleep(uniform(.5,.75))

  def scrapeOdds(self):
    if self.sport == "UFC":
      payload = {
        "page": "SPORT",
        "eventTypeId":"26420387",
        "pbHorizontal": "false",
        "_ak": "FhMFpcPWXMeyZxOx",
        "timezone": "America/New_York"
      }
    elif self.sport in ["Tennis"]:
      payload = {
        "page": "SPORT",
        "eventTypeId":"2",
        "includeEnhancedScan": "true",
        "_ak": "FhMFpcPWXMeyZxOx",
        "timezone": "America/New_York"
      }
    else:
      payload = {
      # "page": "SPORT",
      # "competitionId":"10547864",
      "page": "CUSTOM",
      "customPageId": self.sport.lower() if self.sport not in ['WNCAAB'] else "womens-sports",
      "pbHorizontal": "false",
      "_ak": "FhMFpcPWXMeyZxOx",
      "timezone": "America/New_York",
      "includeEnhancedScan": "true",
    }
    headers = self.getHeaders()
    req = self.session.get("https://sbapi.va.sportsbook.fanduel.com/api/content-managed-page", headers=headers, params=payload)
    self.sleep()
    # print(req.text)
    req = req.json()
    self.getEvents(req['attachments']['events'])
  
  def getExcludedTabs(self):
    excludedTabs = {
      "NBA": ['Half','Team Props','Parlays','Same Game Parlay™','Quick Bets', 'Totals Parlays',
        'Race To', 'Margin', 'Stat Leaders', '2nd Quarter', '3rd Quarter', '4th Quarter', 
        'Buy/Sell Points', '2nd Half', '1st Quarter', 'Scoring','Live SGP'],
      "NFL": ['All','Parlays','Same Game Parlay™','Quick Bets', 'Totals Parlays',
        'Race To', 'Margin', 'Stat Leaders', '2nd Quarter', '3rd Quarter', '4th Quarter', 
        'Buy/Sell Points', '2nd Half', '1st Quarter', 'Game Specials', '1st Half', 'Totals', 'Scoring','Live SGP'],
      "NCAAF": ['Alternates'],
      "NCAAB": ['Quick Bets','Alternates','Margin', 'Half', 'Team Props','Live SGP'],
      "WNCAAB": ['Quick Bets','Alternates','Margin', 'Half', 'Team Props','Live SGP','Alternates'],
      "Tennis": ['Set Markets', 'Player Markets', 'Total Games Props', 'Game Markets','Alternatives',
              'Point By Point','All', 'Quick Bets'],
      "NHL": ['Same Game Parlay™', '2nd Period', '1st Period', '3rd Period','Live SGP'],
      "UFC": [ 'Method of Victory', 'Round Props', 'Time Props', 'Specials', 'Minute Props','Live SGP'],
      "MLB": ['First 5 Innings', 'Innings', 'Hits & Runs', 'Away Team PA', 'Home Team PA', 'Quick Bets'],
    }
    if self.sport in excludedTabs:
      return excludedTabs[self.sport]
    else:
      return excludedTabs["NFL"]

  def getEventTabs(self, eventId):
    payload = {
      "_ak": "FhMFpcPWXMeyZxOx",      
      "eventId": eventId,
      "includeEnhancedScan": "true",
      "useCombinedTouchdownsVirtualMarket": "true",
      "usePulse": "true",
      "useQuickBets": "true",
    }
    headers = self.getHeaders()
    req = self.session.get("https://sbapi.va.sportsbook.fanduel.com/api/event-page", headers=headers, params=payload)
    try:
      req = req.json()
    except:
      print(req.text)
    self.sleep()
    # tabs = [tab for _,tab in req['layout']['tabs'].items()]
    tabs = []
    for _,tab in req['layout']['tabs'].items():
      if 'title' in tab and 'Parlay' not in tab['title'] and tab['title'] not in self.getExcludedTabs():
        tabs.append(tab['title'])
    print(tabs)
    return tabs

  def parseEventTabMarkets(self, eventId, tab):
    payload = {
      "_ak": "FhMFpcPWXMeyZxOx",      
      "eventId": eventId,
      "tab": tab,
      "includeEnhancedScan": "true",
      "useCombinedTouchdownsVirtualMarket": "true",
      "usePulse": "true",
      "useQuickBets": "true",
    }
    headers = self.getHeaders()
    req = self.session.get("https://sbapi.va.sportsbook.fanduel.com/api/event-page", headers=headers, params=payload).json()
    self.sleep()
    markets = self.parseMarkets(req['attachments']['markets'])
    # print(markets)
    return markets

  def getBets(self, eventId):
    tabs = self.getEventTabs(eventId)
    bets = []
    uniqueBets = set()
    for tab in tabs:
      try:
        markets = self.parseEventTabMarkets(eventId, tab.lower().replace(" ","-").replace("/","-"))    
        marketBets = self.getMarketBets(markets)
        if self.sport == "UFC":
          marketBets = [bet for bet in marketBets if bet['Type'] in ['MoneyLine', 'Game Total']]
        for bet in marketBets:
          betTuple = (bet['Type'], bet['Title'], bet['Line'], bet['Over Odds']) 
          if betTuple not in uniqueBets:
            uniqueBets.add(betTuple)
            bets.append(bet)
        # bets.extend(marketBets)
      except Exception as e:
        print(f"Couldn't get market bets for tab {tab}. Exception: {e}")
    return bets
      
  def getEvents(self, events):
    self.eventIdMatchupNameMap = {}
    for id,event in events.items():
      eventId = event['eventId']
      matchupName = event['name'].replace(' @ ', '@').replace(' v ','@')
      if 'Specials' in matchupName or '@' not in matchupName or (
        self.sport in 'Tennis' and '/' in matchupName) or (
        self.sport in ["WNCAAB"] and event['competitionId'] != 11844241
      ):
        print("Skipping", matchupName)
        continue
      if self.sport in ["UFC",'Tennis'] :
        teams = matchupName.split('@')
        teams.sort()
        matchupName = teams[0]+'@'+teams[1]
      self.eventIdMatchupNameMap[eventId] = matchupName
      startTime = datetime.strptime(event['openDate'], '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=pytz.utc).astimezone(pytz.timezone('US/Eastern'))
      if startTime > datetime.now().astimezone(pytz.timezone('US/Eastern')):
        print(matchupName)
        bets = self.getBets(eventId)
        if len(bets) > 0:
          self.matchups[matchupName] = {
            'StartTime': startTime.strftime('%Y/%m/%d %H:%M:%S'),
            'Bets': bets,
          }
        else:
          print("No bets for", matchupName)
      
  def parseMarkets(self, markets):
    marketsDict = {}
    for id,market in markets.items():
      if market['marketStatus'] == 'OPEN':
        try:
          parsed_data = {
            'matchupName': self.eventIdMatchupNameMap[market['eventId']],
            'marketId': market['marketId'],
            'marketName': market['marketName'],
            'marketType': market['marketType'],
            'runners': self.parseRunners(market['runners']),
            'associatedMarkets': market['associatedMarkets'],
            # 'eventTypeId': market['eventTypeId'],
            # 'competitionId': market['competitionId'],
            # 'eventId': market['eventId'],
            # 'marketTime': datetime.strptime(market['marketTime'], '%Y-%m-%dT%H:%M:%S.%fZ'),
            # 'bettingType': market['bettingType'],
            # 'marketStatus': market['marketStatus'],
            # 'marketLevels': market['marketLevels'],
          }
          marketsDict[id] = parsed_data      
        except Exception as e:
          print("Couldn't parse",market['marketName'], "Error:",e)       
    # return parsed_market
    return marketsDict

  def parseRunners(self, runners):
    res = []
    for runner in runners:
      if runner['runnerStatus'] == 'ACTIVE' and 'winRunnerOdds' in runner:
        parsed_data = {
          # 'selectionId': runner['selectionId'],
          'handicap': runner['handicap'],
          'runnerName': runner['runnerName'],
          'winRunnerOdds': runner['winRunnerOdds']['americanDisplayOdds']['americanOdds'],
          # 'previousWinRunnerOdds': [self.parseWinRunnerAmericanOdds(r) for r in runner['previousWinRunnerOdds']],
        }
        res.append(parsed_data)
    return res

  def includeMarket(self, marketName):
    pattern =  re.compile(r'.*\d[+].*')
    if pattern.search(marketName):
      return False
    if 'Any Time Touchdown Scorer' in marketName:
      return True
    ignoreNames = [
      'Alt', ' - 1st Qtr', 'Odd / Even', 'Odd/Even', 'Odd Even','Parlay', 
      'Margin', 'Including Tie', 'Tri-Bet', '3-Way', 'Both', 
      'Score', 'Total Touchdowns', 'Overtime?', 'Scoring',
      ' / Total', 'Exact', 'Race', 'Band', 'Half-Time/Full-Time',
      'Team to have', 'Drive Result', '(3 Way)', '(Flat Line)', 'Most',
      'Method of ', 'Dunks', 'Winning at End of ','Largest',
      'Player Performance Doubles', '2 or more', 'First Basket', 'Game Specials', 'First Player',
      'Player To Record Longest Reception Of The Game', 'Method Of First TD','Method OF First TD',
      '1st Drive', 'Any Time Goal Scorer', '1st Period Goal In First Five Minutes',
      'Set Betting', 'and win match', '2nd Set', 'Set 2', 'Tie Breaks', '6-0 Set in Match', 'Aces',
      'Top ', 'Bottom ', '1st Inning Hits'
      ]
    for name in ignoreNames:
      if name in marketName:
        return False
    return True

  def getBetInfo(self, bet, marketType, marketName, matchupName, line):
    matchupCategories = [
      'HOME_TOTAL_POINTS','AWAY_TOTAL_POINTS',
      'HOME_TEAM_TOTAL_POINTS', 'AWAY_TEAM_TOTAL_POINTS',
      'MATCH_HANDICAP_(2-WAY)','MONEY_LINE','TOTAL_POINTS_(OVER/UNDER)',
      'FIRST_HALF_TOTAL', 'FIRST_HALF_HANDICAP',
      '1ST_HALF_HOME_TEAM_TOTAL_POINTS', '1ST_HALF_AWAY_TEAM_TOTAL_POINTS',
      'HOME_TOTAL_GOALS','AWAY_TOTAL_GOALS', '1ST_PERIOD_TOTAL_GOALS',
      'GOAL_SCORED_IN_FIRST_TEN_MINUTES_(00:00-09:59)',
      '1ST_HALF_HANDICAP', '1ST_HALF_WINNER', '1ST_HALF_TOTAL', '1ST_HALF_SPREAD',
      '1ST_QUARTER_TOTAL_POINTS', '2ND_QUARTER_TOTAL_POINTS',
      '3RD_QUARTER_TOTAL_POINTS', '4TH_QUARTER_TOTAL_POINTS'
    ]
    pattern = re.compile(r'^((PLAYER)|(ANY_TIME)|(TO_RECORD_A))_')
    if marketType in matchupCategories:
      betCategory = "Matchup"
    elif pattern.match(marketType):
      betCategory = "Prop"
    else:
      betCategory = "OTHER"

    if bet['runnerName'] not in ['Over','Under','Yes','No']:
      participant = bet['runnerName']
      for ending in [' Over',' Under', ' -', ' Yes', ' No']:
        if participant.endswith(ending):
          participant = participant[:-len(ending)]
    else:
      if marketName == 'Away Team Total Points':
        participant = matchupName.split('@')[0]
      elif marketName == 'Home Team Total Points':
        participant = matchupName.split('@')[1]
      elif ' - Total Saves' in marketName:
        participant = marketName.split(' - Total Saves')[0]
      else:
        participant = matchupName
        
    type = marketName
    if " - " in marketName:
      type = marketName.split(" - ")[1] 
    elif marketName in ['Total Goals','Total Points','Total Rounds', 'Total Runs']:
      type = 'Game Total'
      betCategory = "Matchup"

    if ' Total Goals' in type:
      prefix = type.split(' Total Goals')[0]
      if prefix in matchupName:
        type = 'Team Total'
        participant = prefix
      elif prefix == participant:
        type = 'Goals'
    
    for total in [' Total Points',' Total Runs']:
      prefix = type.split(total)[0]
      if prefix in matchupName:
        type = 'Team Total'
        participant = prefix
      
    if participant in type:
      type = type.replace(participant, "").strip()
    
    typeRenaming = {
      'Moneyline': 'MoneyLine',
      'Spread Betting': 'Spread',
      'Away Team Total Points': "Team Total",
      'Home Team Total Points': "Team Total",
      'Made Threes': '3 Point FG',
      'Pts + Reb + Ast':'Pts+Rebs+Asts',
      'To Record A Double Double': 'Double+Double',
      'To Record A Triple Double': 'Triple+Double',
      
      'Rushing Yds': 'Rushing Yards',
      'Passing Yds': 'Passing Yards',
      'Receiving Yds': 'Receiving Yards',
      'Any Time Touchdown Scorer': 'Anytime TD',
      'Pass Completions': 'Completions',
      'Total Receptions': 'Receptions',
      'Passing TDs': 'TD Passes',
      'Interception': 'Interceptions',
      
      'Shots on Goal': 'Shots On Goal',
      '60 Min  Shots on Goal': 'Shots On Goal',
      'Puck Line': 'Spread',
      'Total Saves': 'Saves',
      'Total Points': 'Points',
      
      'To Win 1st Set': '1st Set MoneyLine',
      'Game Spread': 'Spread (Games)', 
      'Strikeouts': 'Total Strikeouts',
      'Run Line': 'Spread',
      'First 5 Innings Money Line': 'First 5 Innings MoneyLine',
      'First 5 Innings Run Line': 'First 5 Innings Spread',
      "Outs Recorded": "Pitching Outs",
    }
    
    for k,v in typeRenaming.items():
      if type == k:
        type = v
        break
    
    participant = self.renameParticipant(participant)
    if self.sport == "Tennis":
      pattern = r'([A-Za-z\s]+)\s*\(([-+]?\d+(\.\d+)?)\)$'
      match = re.search(pattern, participant)

      if match:
        participant = match.group(1).strip()
        line = float(match.group(2))
        if 'Set 1 Game Handicap' in type:
          type = "1st Set Spread (Games)"
      # elif ' to win at least one set' in type:
      #   type = 'Spread (Sets)'
      #   line = 1.5
      else:  
        pattern = r'([A-Za-z\s]+)\s*([-+]?\d+(\.\d+)?)$'
        match = re.search(pattern, type)
        if match:
          type = match.group(1).strip()
          line = float(match.group(2))
          if type == 'Total Match Games':
            type = 'Total (Games)'
            participant = matchupName
          elif type == 'Total Sets':
            type = 'Total (Sets)'
            participant = matchupName
            
    title = participant + " " + type
  
    return betCategory, type, participant, title, line

  def getBetInfoDict(self, bet, marketType, marketName, matchupName, participant, title, line, overOdds, underOdds=None):
    betCategory, type, participant, title, line = self.getBetInfo(bet, marketType, marketName, matchupName, line)
    line = .5 if type in ['Anytime TD', 'Triple+Double', 'Double+Double', 'Interceptions'] else line
    info = {
      "Category": betCategory,
      "Matchup": matchupName,
      "Participant": participant,
      "Type": type, 
      "Title": title,
      "Line": line,
      "Over Odds": overOdds,
      "Under Odds": underOdds,
    }
    return info

  def getMarketBets(self, markets):
    maketBets = []
    for b in markets.values():   
      marketName = b['marketName']
      marketType = b['marketType']
      matchupName = b['matchupName'].replace(' @ ','@')
      if self.includeMarket(marketName):
        # print(marketName,marketType,betCategory,matchupName)
        # print(marketName, marketType)
        # print(marketName, b['runners'])
        firstBet = next(sel for sel in b['runners'])
        secondBet = next((sel for sel in b['runners'] if sel['runnerName'] != firstBet['runnerName']),None)
        if secondBet is None:
          line = firstBet['handicap']
          betCategory, type, participant, title, line = self.getBetInfo(firstBet,marketType, marketName, b['matchupName'], line)
          line = .5 if type in ['Anytime TD', 'Triple+Double', 'Double+Double', 'Interceptions'] else line
          maketBets.append({
            "Category": betCategory,
            "Matchup": matchupName,
            "Participant": participant if firstBet['runnerName'] not in matchupName else firstBet['runnerName'],
            "Type": type,
            "Title": title,
            "Line": line,
            "Over Odds": firstBet['winRunnerOdds'],
            })
        else:
          thirdBet = next((sel for sel in b['runners'] if sel['runnerName'] != firstBet['runnerName'] and sel['runnerName'] != secondBet['runnerName']), None)
          if thirdBet is None:
            if (firstBet['handicap'] == secondBet['handicap'] and firstBet['handicap'] != 0) or (
              self.sport == "Tennis" and marketType in ['PLAYER_A_TO_WIN_AT_LEAST_1_SET', 'OVER_UNDER_TOTAL_SETS', 
                             'TOTAL_MATCH_GAMES', 'PLAYER_B_TO_WIN_AT_LEAST_1_SET']):
              line = firstBet['handicap']
              betCategory, type, participant, title, line = self.getBetInfo(firstBet,marketType, marketName, b['matchupName'], line)
              overOdds = firstBet['winRunnerOdds']
              underOdds = secondBet['winRunnerOdds']
              participant = participant if firstBet['runnerName'] not in matchupName else firstBet['runnerName']
              maketBets.append(self.getBetInfoDict(firstBet, marketType, marketName, matchupName, participant, title, line, overOdds, underOdds))
            elif (firstBet['handicap'] == -secondBet['handicap']):
              if firstBet['handicap'] == 0:
                firstBet['handicap'] = secondBet['handicap'] = -.5
              line = firstBet['handicap']
              betCategory, type, participant, title, line = self.getBetInfo(firstBet,marketType, marketName, b['matchupName'], line)
              overOdds = firstBet['winRunnerOdds']
              underOdds = secondBet['winRunnerOdds']
              participant = participant if firstBet['runnerName'] not in matchupName else firstBet['runnerName']
              maketBets.append(self.getBetInfoDict(firstBet, marketType, marketName, matchupName, participant, title, line, overOdds, underOdds))
              line = secondBet['handicap']
              overOdds = secondBet['winRunnerOdds']
              underOdds = firstBet['winRunnerOdds']  
              participant = participant if secondBet['runnerName'] not in matchupName else secondBet['runnerName']
              maketBets.append(self.getBetInfoDict(secondBet, marketType, marketName, matchupName, participant, title, line, overOdds, underOdds))
          else:
            visited = set()
            nextBet = next((sel for sel in b['runners']), None)
            while nextBet is not None:
              line = nextBet['handicap']
              betCategory, type, participant, title, line = self.getBetInfo(nextBet,marketType, marketName, b['matchupName'], line)
              overOdds = nextBet['winRunnerOdds']
              participant = participant if nextBet['runnerName'] not in matchupName else nextBet['runnerName']
              maketBets.append(self.getBetInfoDict(nextBet, marketType, marketName, matchupName, participant, title, line, overOdds))
              visited.add(nextBet['runnerName'])
              nextBet = next((sel for sel in b['runners'] if sel['runnerName'] not in visited), None)
    return maketBets        
  
  def renameParticipant(self, participant):
    renameDict = {'UC Riverside': 'Cal Riverside',
      'Charleston': 'College Of Charleston',
      'Citadel': 'The Citadel',
      'Miss Valley State': 'Mississippi Valley State',
      'UW Milwaukee': 'Wisc Milwaukee',
      'UNC Greensboro': 'NC Greensboro',
      'UC Irvine': 'Cal Irvine',
      'Jabari Smith': 'Jabari Smith Jr.',
      'CSU Northridge': 'Cal State Northridge',
      'Tim Stützle': 'Tim Stutzle',
      'Boston University': 'Boston U',
      'Green Bay': 'Wisc Green Bay',
      'Cal Poly': 'Cal Poly SLO',
      "Saint Joseph's": "St. Joseph's",
      'CSU Fullerton': 'Cal State Fullerton',
      "Mount St. Mary's (MD)": "Mt. St. Mary's",
      'Gardner-Webb': 'Gardner Webb',
      'Saint Peters': "St. Peter's",
      'P.J. Washington': 'PJ Washington',
      'Bruce Brown Jr': 'Bruce Brown',
      'UNC Asheville': 'NC Asheville',
      'Nicholls': 'Nicholls State',
      'East Tennessee State': 'East Tenn State',
      'Middle Tennessee': 'Middle Tennessee State',
      'Kennesaw State': 'Kennesaw St',
      'CSU Bakersfield': 'Cal State Bakersfield',
      'Lafayette College': 'Lafayette',
      'Lonnie Walker': 'Lonnie Walker IV',
      'Utah Valley State': 'Utah Valley',
      'Calvin Petersen Saves': 'Cal Petersen Saves',
      'Grambling State': 'Grambling',
      'Detroit Mercy': 'Detroit',
      'UT Martin': 'Tennessee Martin',
      'Sebastian Aho (CAR)': 'Sebastian Aho CAR',
      'Tarleton State': 'Tarleton St',
      'GG Jackson': 'Gregory Jackson',
      'T.J McConnell': 'T.J. McConnell',
      'Arkansas-Pine Bluff': 'Arkansas Pine Bluff',
      'Bethune-Cookman': 'Bethune Cookman',
      'Marvin Bagley': 'Marvin Bagley III',
      'Southern University': 'Southern',
      'Ole Miss': 'Mississippi',
      'Alexis Lafrenière': 'Alexis Lafreniere',
      'San Jose St': 'San Jose State',
      'UNC Wilmington': 'NC Wilmington',
      'Pacific': 'Pacific Tigers',
      "Saint Mary's": 'Saint Marys CA',
      "Hawai'i": 'Hawaii',
      'UTSA': 'Texas San Antonio',
      'N.J.I.T': 'NJIT',
      'UMBC': 'MD Baltimore County',
      'St. Francis (PA)': 'St. Francis PA',
      'Albany': 'Albany NY',
      'LIU': 'Long Island',
      "Saint Peter's": "St. Peter's",
      "Queen's University": 'Queens',
      'DePaul': 'Depaul',
      'Pacific Tigers': 'Pacific',
      'Louisiana Lafayette': 'UL - Lafayette',
      'McNeese': 'McNeese State',
      'N Carolina Central': 'North Carolina Central',
      'Miami (OH)': 'Miami Ohio',
      'College Of Charleston Southern': 'Charleston Southern',
      'UMass': 'Massachusetts',
      'Maryland-Eastern Shore': 'MD Eastern Shore',
      'Giovanni Mpetshi Perricard': 'Giovanni Perricard',
      'J Riera': 'Julia Riera',
      'O Danilovic': 'Olga Danilovic',
      'Sim Waltert': 'Simona Waltert',
      'Uchijima': 'Moyuka Uchijima',
      'Zeyn Sonmez': 'Zeynep Sonmez',
      'Robi Montgomery': 'Robin Montgomery',
      'F Jones': 'Francesca Jones',
      'Marcelo Tomas Barrios Vera': 'Marcelo Tomas Barrios-Vera',
      'Pierre-hugues Herbert': 'Pierre-Hugues Herbert',
      'Cristian Garin': 'Christian Garin',
      'Je Bouzas Maneiro': 'Jessica Bouzas Maneiro',
      'El Cocciaretto': 'Elisabetta Cocciaretto',
      'Guiomar Maristany Zuleta De Reales': 'Guiomar M Zuleta de Reales',
      'Pe Stearns': 'Peyton Stearns',
      'Albert Ramos Vinolas': 'Albert Ramos-Vinolas',
      'Camila Osorio': 'Maria Camila Osorio Serrano',
      'Yunchaokete Bu': 'Bu Yunchaokete',
      'A. Cornet': 'Alize Cornet',
      'Jes Ponchet': 'Jessika Ponchet',
      'Dereck Lively': 'Dereck Lively II',
      'Emm Navarro': 'Emma Navarro',
      'M Sherif': 'Mayar Sherif',
      'As Krueger': 'Ashlyn Krueger',
      'K Siniakov': 'Katerina Siniakova',
      'Sorribes Tormo': 'Sara Sorribes Tormo',
      'I Swiatek': 'Iga Swiatek',
      'Elmer Moeller': 'Elmer Moller',
      'Di Shnaider': 'Diana Shnaider',
      'P Badosa': 'Paula Badosa',
      'A Kalinina': 'Anhelina Kalinina',
      'M Sakkari': 'Maria Sakkari',
      'O Jabeur': 'Ons Jabeur',
      'Sof Kenin': 'Sofia Kenin',
      'A Kalinskaya': 'Anna Kalinskaya',
      'Jose Urena': 'José Ureña',
      'Ayano Shimizu': 'Yuta Shimizu',
      'A Potapova': 'Anastasia Potapova',
      'A Sabalenka': 'Aryna Sabalenka',
      'D Yastremska': 'Dayana Yastremska',
      'Jan-lennard Struff': 'Jan-Lennard Struff',
      'C Tauson': 'Clara Tauson',
      'B Haddad': 'Beatriz Haddad',
      'D Kasatkina': 'Daria Kasatkina',
      'L Noskova': 'Linda Noskova',
      'Q Zheng': 'Qinwen Zheng',
      'E Rybakina': 'Elena Rybakina',
      'V Gracheva': 'Varvara Gracheva',
      'A L Lingua Lavallen': 'Alejo Lorenzo Lingua Lavallen',
      'C Gauff': 'Coco Gauff',
      'J Cristian ': 'Jaqueline Cristian ',
      'N Osaka': 'Naomi Osaka',
      'Davidovich Fokina A': 'Alejandro Davidovich Fokina',
      'J Paolini': 'Jasmine Paolini',
      'Er Andreeva': 'Erika Andreeva',
      'Daniel Evans': 'Dan Evans',
      'Jeffrey John Wolf': 'JJ Wolf',
      'Abdullah Shelbayh': 'Abedallah Shelbayh',
      'Marc-andrea Huesler': 'Marc-Andrea Huesler',
      'Anna Karolina Schmiedlova': 'Anna Schmiedlova',
      'D Parry': 'Diane Parry',
      'Thai-son Kwiatkowski': 'Thai-Son Kwiatkowski',
      'J Niemeier': 'Jule Niemeier',
      'D Collins': 'Danielle Collins',
      'Mccartney Kessler': 'McCartney Kessler',
      'Felipe Meligeni Rodrigues': 'Felipe Meligeni Rodrigues Alves',
      'E Ruse': 'Elena-Gabriela Ruse',
      'Jesus Luzardo': 'Jesús Luzardo',
      'J Cristian': 'Jaqueline Cristian',
      'El Seidel': 'Ella Seidel',
      'Lu Ciric Bagaric': 'Lucija Ciric Bagaric',
      'Mirr Andreeva': 'Mirra Andreeva',
      'Leol Jeanjean': 'Leolia Jeanjean',
      'Mir Bulgaru': 'Miriam Bulgaru',
      'No Noha Akugue': 'Noma Noha Akugue',
      'X Wang': 'Xiyu Wang',
      'James Kent Trotter': 'James Trotter',
      'T Zidansek': 'Tamara Zidansek',
      'Ma Joint': 'Maya Joint',
      'Randy Vasquez': 'Randy Vásquez',
      'Sar Svetac': 'Sara Svetac',
      'P Martic': 'Petra Martic',
      'Kat Zavatska': 'Katarina Zavatska',
      'A Li': 'Ann Li',
      'M Trevisan': 'Martina Trevisan',
      'Tung-lin Wu': 'Tung-Lin WU',
      'Seongchan Hong': 'Seong-chan Hong',
      'Coleman Wong': 'Chak Lam Coleman Wong',
      'Al Eala': 'Alexandra Eala',
      'P Udvardy': 'Panna Udvardy',
      'Khumoyun Sultanov': 'Khumoun Sultanov',
      'Kat Dunne': 'Katy Dunne',
      'Tay Preston': 'Taylah Preston',
      'Ta Gibson': 'Talia Gibson',
      'A Anisimova': 'Amanda Anisimova',
      'Ano Koevermans': 'Anouk Koevermans',
      'Mccar Kessler': 'McCartney Kessler',
      'Samantha Murray Sharan': 'Samantha Murray',
      'Ari Geerlings': 'Ariana Geerlings',
      'Ja Kolodynska': 'Jana Kolodynska',
      'YeXin Ma': 'Ye-Xin Ma',
      'Michae Krajicek': 'Michaella Krajicek',
      'Re Marino': 'Rebecca Marino',
      'Vit Diatchenko': 'Vitalia Diatchenko',
      'Roddery Munoz': 'Roddery Muñoz',
      'Luca Potenza': 'Lukas Pokorny',
      'Joan Nadal Vives': 'Joan Nadal',
      'Lin Fruhvirtova': 'Linda Fruhvirtova',
      'Sa Murray Sharan': 'Samantha Murray',
      'Am Banks': 'Amarni Banks',
      'A Zverev': 'Alexander Zverev',
      'A Sasnovich': 'Aliaksandra Sasnovich',
      'Ame Rajecki': 'Amelia Rajecki',
      'La Tararudee': 'Lanlana Tararudee',
      'Ang Fita Boluda': 'Angela Fita',
      'Nur Brancaccio': 'Nuria Brancaccio',
      'D Galfi': 'Dalma Galfi',
      'Angela Fita Boluda': 'Angela Fita',
      'Bianca Andreescu': 'Bianca Vanessa Andreescu',
      'Santiago Rodriguez Taverna': 'Santiago FA Rodriguez Taverna',
      'Pedro Boscardin Dias': 'Pedro Dias',
      'Ce Naef': 'Celine Naef',
      'L Samsonova': 'Liudmila Samsonova',
      'Oks Selekhmeteva': 'Oksana Selekhmeteva',
      'Iryn Shymanovich': 'Iryna Shymanovich',
      'Emi Bektas': 'Emina Bektas',
      'Joao Lucas Reis Da Silva': 'Joao Lucas Silva',
      'Francisca Jorge': 'Francesca Jones',
      'Alexandra Vecic': 'Aleksandar Vukic',
      'Dar Semenistaja': 'Darja Semenistaja',
      'I Begu': 'Irina-Camelia Begu',
      'V Kudermetova': 'Veronika Kudermetova',
      'D Augusto Barreto Sanchez': 'Diego Augusto Barreto Sanchez',
      'Santiago Rodriguez': 'Santiago FA Rodriguez Taverna'
    }
    for oldStr, newStr in renameDict.items():
      # for team in ['Milwakee Bucks', 'Seattle Kraken']
      if "Milwaukee Bucks" not in oldStr and "Seattle Kraken" not in oldStr and "Charlotte Hornets" not in oldStr:
        participant = re.sub(oldStr, newStr, participant)
    return participant