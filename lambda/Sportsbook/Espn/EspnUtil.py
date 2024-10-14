import requests, pandas as pd, pytz, re
from time import sleep
from random import uniform
from datetime import datetime
class EspnScraper():
  def __init__(self, sport):
    self.sport = sport
    self.session = requests.Session()
    self.getApiKey()
    self.getSportsMenuPage()
    self.setEventCanonicalUrls()
  
  def sleep(self):
    sleep(uniform(.8,1.2))
    
  def getApiKey(self):
    url = "https://sportsbook-espnbet.us-va.thescore.bet/graphql/persisted_queries/81a57a572513981de2856a51aa9ac209bb336e9f0e1ca03baf50ac8c67d3461e"
    payload = {"operationName":"Startup","variables":{"connectToken":"54alllll8mi1vhn2fl1dfn11l15ez4ip"},"extensions":{"persistedQuery":{"version":1,"sha256Hash":"81a57a572513981de2856a51aa9ac209bb336e9f0e1ca03baf50ac8c67d3461e"}}}
    headers = {
        'User-Agent': 'Chrome/119.0.0.0',
        'Content-Type': 'application/json',
        'X-App': 'espnbet',
        'X-App-Version': '23.10.2',
        'X-Platform': 'web',
    }
    r = self.session.post(url, json=payload, headers=headers)
    try:
      apiKey = r.json()['data']['startup']['anonymousToken']
      self.apiKey = 'Bearer ' + apiKey
      self.headers =  { 'X-Anonymous-Authorization': self.apiKey }
    except Exception as e:
      print("Failed to get api key", r.text, e)
      raise e

  def getSportsMenuPage(self):
    # Sports menu page
    url = "https://sportsbook-espnbet.us-va.thescore.bet/graphql/persisted_queries/752954896859987aa191300e5787262db0e3e741e6a5f8450d2524a643c19d97"
    payload = {"operationName":"SportsMenu","variables":{},"extensions":{"persistedQuery":{"version":1,"sha256Hash":"752954896859987aa191300e5787262db0e3e741e6a5f8450d2524a643c19d97"}}}
    r = self.session.post(url, json=payload, headers=self.headers)
    try:
      self.data = r.json()['data']['sportsMenu']['menuItems']
    except Exception as e:
      print("Failed to get sports menu page", r.text, e)
      raise e
    categories = [d['label'] for d in self.data]
    self.sportsCanonicalUrlMap = {}
    for d in self.data:
      self.getCanonicalUrlForSport(d)
      
  def getCanonicalUrlForSport(self, d):
    if d['type'] == 'LEAF':
      if d['deepLink'] is not None:
        self.sportsCanonicalUrlMap[d['label']] = d['deepLink']['canonicalUrl']
    else:
      for child in d['sportsMenuItemChildren']:
        self.getCanonicalUrlForSport(child)
        
  def getSportsCanonicalUrlMap(self):
    return self.sportsCanonicalUrlMap

  def getSportsSectionId(self, sport):
    canonicalURL = self.sportsCanonicalUrlMap[sport]
    pages = self.getSportsPages(canonicalURL)['data']['page']['pageChildren']
    sectionLabelIdMap = {section['label']:section['id'] for section in pages}
    return sectionLabelIdMap['Lines']
      
  # Sports  page
  # pass in canonicalURL
  def getSportsPages(self, canonicalURL):
    url = "https://sportsbook-espnbet.us-va.thescore.bet/graphql/persisted_queries/27b9e7556046da19c0df40b5900c3597dae1a2c56811cdcd68246bf757a3d9d1"
    payload = {
      "operationName":"Marketplace",
      "variables": {
        "includeSectionvaField":True, 
        "includevaChild":False, 
        "canonicalUrl": canonicalURL, 
        "oddsFormat":"AMERICAN","pageType":"PAGE","includeRichEvent":True, 
        "includeMediaUrl":False,"selectedFilterId":""
        },
      "extensions":{
        "persistedQuery": {
          "version":1,"sha256Hash":"27b9e7556046da19c0df40b5900c3597dae1a2c56811cdcd68246bf757a3d9d1"
          }}}
    r = self.session.post(url, json=payload, headers=self.headers)
    try:
      return r.json()
    except Exception as e:
      print("Failed to get sports pages", r.text, e)
      raise e

  # Sports  page
  # pass in canonicalURL
  def getLines(self, id):
    url = "https://sportsbook-espnbet.us-va.thescore.bet/graphql/persisted_queries/d172672ef362f8e34d7a952602bc198ba393f99fc4a48d17e34b0289b096d05e"
    payload = {
      "operationName":"Node",
      "variables": { 
        "includeSectionvaField":False,
        "id": id,
        "oddsFormat":"AMERICAN","selectedFilterId":"",
        "includeRichEvent":True,
        "includeMediaUrl":True},
      "extensions":{ 
        "persistedQuery":{ 
          "version":1,"sha256Hash":"d172672ef362f8e34d7a952602bc198ba393f99fc4a48d17e34b0289b096d05e"}
        }}
    r = self.session.post(url, json=payload, headers=self.headers).json()

  def setEventCanonicalUrls(self):
    if self.sport == "UFC":
      self.eventCanonicalUrls = []
      for section in [x for x in self.sportsCanonicalUrlMap.keys() if 'UFC' in x]:
        print(section)
        sportSectionId = self.getSportsSectionId(section)
        self.eventCanonicalUrls += self.getEventCanonicalUrls(sportSectionId)
    else:
      if self.sport in ["ATP", "WTA"]:
        self.eventCanonicalUrls = []
        for section in [x for x in self.sportsCanonicalUrlMap.keys() if 'Specials' not in x and (
          self.sport in x or (
            self.sport == 'ATP' and (x == "Men's French Open"  or x == "Men's Wimbledon")) or (
            self.sport == 'WTA' and ((x == "Women's French Open") or (
              x == "Women's Wimbledon") or (
                "itf-women" in self.sportsCanonicalUrlMap[x])))
        )]:
          print(section)
          sportSectionId = self.getSportsSectionId(section)
          self.eventCanonicalUrls += self.getEventCanonicalUrls(sportSectionId)
        # sportSectionId = self.getSportsSectionId("Men's Australian Open")
      else:
        sportSectionId = self.getSportsSectionId(self.sport)
        self.eventCanonicalUrls = self.getEventCanonicalUrls(sportSectionId)

  def getEventCanonicalUrls(self, sportSectionId):
    lines = self.getLines(sportSectionId)
    eventCanonicalUrls = set()
    # MarketplaceShelf
    try:
      for child in lines['data']['node']['sectionChildren'][1]['marketplaceShelfChildren']: 
        eventCanonicalUrls.add(child['deepLink']['canonicalUrl'])
    except Exception as e:
      print(e, "Getting canonical urls trying with 0th index")
      for child in lines['data']['node']['sectionChildren'][0]['marketplaceShelfChildren']: 
        eventCanonicalUrls.add(child['deepLink']['canonicalUrl'])
    return list(eventCanonicalUrls)
  
  
  # Sports  page
  # pass in canonicalURL
  def getLines(self, id):
    url = "https://sportsbook-espnbet.us-va.thescore.bet/graphql/persisted_queries/d172672ef362f8e34d7a952602bc198ba393f99fc4a48d17e34b0289b096d05e"
    payload = {
      "operationName":"Node",
      "variables": {
        "includeSectionvaField":False,
        "id": id,
        "oddsFormat":"AMERICAN","selectedFilterId":"",
        "includeRichEvent":True,
        "includeMediaUrl":True
        },
      "extensions": {
        "persistedQuery": {
          "version":1,"sha256Hash":"d172672ef362f8e34d7a952602bc198ba393f99fc4a48d17e34b0289b096d05e"}
        }}
    r = self.session.post(url, json=payload, headers=self.headers)
    try:
      return r.json()
    except Exception as e:
      print("Failed to get Lines", r.text, e)
      raise e


  def getSelectionInfo(self, selection):
    # print(selection.keys())
    if selection['status'] == 'OPEN':
      return {
        "Participant": selection['name']['cleanName'] if selection['participant'] is None else selection['participant']['fullName'],
        "Odds": selection['odds']['formattedOdds'],
        "Points": selection['points']['decimalPoints'] if selection['points'] is not None else 0,
      }

  def getBets(self, marketInfo):
    return {
        "Name": marketInfo['name'],
        "Selections": [self.getSelectionInfo(s) for s in marketInfo['selections']]
    }
  
  def getMatchupName(self, sportsPage):
    try:
      awayTeam = sportsPage['data']['page']['pageHeaders'][0]['fallbackEvent']['awayParticipant']['fullName'] 
      homeTeam = sportsPage['data']['page']['pageHeaders'][0]['fallbackEvent']['homeParticipant']['fullName']
      if self.sport in ['UFC','ATP','WTA']:
        teams = [awayTeam, homeTeam]
        teams.sort()
        return teams[0] + '@' + teams[1]
      else:
        return awayTeam + '@' + homeTeam
    except Exception as e:
      print(e, sportsPage)
      return None
    
  def setTimestamp(self):
    timestamp = datetime.now().astimezone(pytz.timezone('America/New_York')).strftime('%Y/%m/%d %H:%M:%S')
    return timestamp
  
  def getOdds(self):
    self.scrapeOdds()
    timestamp = self.setTimestamp()
    return {"Timestamp": timestamp, "Data": self.matchups}
  
  def scrapeOdds(self):
    self.matchups = {}
    for event in self.eventCanonicalUrls:
      sportsPage = self.getSportsPages(event)
      matchupName = self.getMatchupName(sportsPage)
      print(matchupName)
      labelIdMap = {section['label']: section['id'] for section in sportsPage['data']['page']['pageChildren']}
      # categories = ['Lines', 'Game Props', 'Player Props']
      categories = self.getBetCategories()
      # print(labelIdMap.keys(), categories)
      tmp = []
      for betCategory in categories:
        if betCategory in labelIdMap:
          lines = self.getLines(labelIdMap[betCategory])['data']['node']
          sectionChildren = lines['sectionChildren']        
          for sectionChild in sectionChildren:
            type = sectionChild['labelText']
            if not self.skipTypes(betCategory, type):
              for drawerChild in sectionChild['drawerChildren']:
                for marketplaceChild in drawerChild['marketplaceShelfChildren']:
                  startTime = datetime.strptime(marketplaceChild['fallbackEvent']['startTime'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=pytz.UTC).astimezone(pytz.timezone("America/New_York"))
                  # print(startTime)
                  if startTime > datetime.now(pytz.timezone("America/New_York")):
                    if matchupName not in self.matchups:
                      self.matchups[matchupName] = {
                        "StartTime": startTime.strftime("%Y/%m/%d %H:%M:%S"),
                        "Bets": []
                      }
                    if 'market' in marketplaceChild:
                      bets = [self.getBets(marketplaceChild['market'])]
                    else:
                      bets = [self.getBets(market) for market in marketplaceChild['markets']]
                    
                    tmp.extend(self.formatBets(bets, matchupName, betCategory, type))
      if matchupName in self.matchups:
        self.matchups[matchupName]["Bets"].extend(tmp)

    return self.matchups
    
  def getBetCategories(self):
    betCategoryMap = {
      "NFL": ['Lines', 'Player Props','TD Scorers'],
      "WTA": ['Lines','Game Props'],
      "ATP": ['Lines','Game Props'],
      "MLB": ['Lines','Player Props', 'Game Props'],
    }
    if self.sport in betCategoryMap:
      return betCategoryMap[self.sport]
    else:
      return ['Lines','Player Props']

  def extractParticipantName(self, type, title):
    type_words = type.split()
    title_words = title.split()
    title_words = [word for word in title_words if word not in type_words]
    return ' '.join(title_words)
  
  def handleRenaming(self, betCategory, type, title, matchupName):
    if type == "Total Points" or type == "Total Goals" or type == "Total Runs":
      type, title = "Game Total", "Game Total"
    elif self.sport in ["WTA","ATP"]:
      renameDict = {
        "Match Winner": ("Matchup","MoneyLine"),
        "Total Games": ("Matchup", "Total (Games)"),
        "Total Sets": ("Matchup", "Total (Sets)"),
        "Games Handicap": ("Matchup", "Spread (Games)"),
        "Match Handicap (Sets)": ("Matchup", "Spread (Sets)"),
        "Set Winner": ("1st Set", "1st Set MoneyLine"),
        "Set Total Games": ("1st Set", "1st Set Total (Games)"),
        "Set Handicap": ("1st Set", "1st Set Spread (Games)"),
        "Player 1 Total Games": ("Matchup", "Team Total (Games)"),
        "Player 2 Total Games": ("Matchup", "Team Total (Games)"),
      }
      participant = ""
      for k,v in renameDict.items():
        if type == k or type == v[1]:
          player1 = matchupName.split('@')[0]
          player2 = matchupName.split('@')[1]
          if type == title or type =='Set Total Games':
            participant = matchupName
          else:
            if player1 in title:
              participant = player1
            elif player2 in title:
              participant = player2
            
          betCategory = v[0]
          type = v[1]
          title = participant + " " + type
          break

      return betCategory, type, participant, title

    else:
      renameDict = {
        "Match Spread": "Spread",
        "Game Spread": "Spread",
        "Run Line": "Spread",
        "Rounds": "Game Total",
        "Moneyline": "MoneyLine",
        "Points, Rebounds And Assists": "Pts+Rebs+Asts",
        "Total ": "",
        "Bases": "Total Bases",
        "To Record A Double Double":"Double+Double",
        "To Record A Triple Double":"Triple+Double",
        "To Score A Touchdown": "Anytime TD",
        "To Score A Goal": "Anytime Goalsscorer",
        "Passing Attempts": "Pass Attempts",
        "Passing Completions": "Completions",
        "Passing TDs": "TD Passes",
        "Threes Made": "3 Point FG", 
        "3-Pointers Made": "3 Point FG",
        "Nicolas Claxton": "Nic Claxton",
        "Cameron Thomas": "Cam Thomas",
        "Trey Murphy III": "Trey Murphy",
        " Jr ": " Jr. ",
        "Mitch Marner": "Mitchell Marner",
        "Thomas Novak": "Tommy Novak",
        "Strikeouts": "Total Strikeouts",
        'Earned Runs Allowed': 'Earned Runs',
        'Outs Recorded': 'Pitching Outs',
        'Home Runs Hit': 'Home Runs',
      }
      for oldStr, newStr in renameDict.items():
        type = type.replace(oldStr, newStr)
        title = title.replace(oldStr, newStr)
      
    if type == title:
      participant = matchupName
      title = matchupName +" "+type
    else:
      participant = self.extractParticipantName(type, title)
      
    participant = self.fixNames(participant)
    title = self.fixNames(title)
    return betCategory, type, participant, title
  
  
  
  def formatBets(self, betOfferings, matchupName, betCategory, type):
    parsedOfferings = self.parseBetOfferings(betOfferings)
    result = []
    for title, values in parsedOfferings.items():
      betCategory, type, participant, title = self.handleRenaming(betCategory, type, title, matchupName)
      b = {
        "Matchup": matchupName,
        "Category": betCategory,
        "Type": type,
        'Participant': participant, 
        'Title': title,
        **values
      }
      result.append(b)
    return result
  
  def parseBetOfferings(self, betOfferings):
    # print(betOfferings)
    betNames = set()
    output = {}
    for bet in betOfferings:
      name = bet['Name']
      if name not in betNames:
        betNames.add(name)
      else:
        # Don't care about alt line
        continue  
      for selection in bet['Selections']:
        if selection is not None:
          try:
            participant = selection['Participant']
            if participant != "Over" and participant != "Under" and participant != "Yes" and participant != "No":
              title = participant + " " + name
              if 'Moneyline' in title or 'Match Winner' in title:
                line = -0.5
              else:
                line = next(sel['Points'] for sel in bet['Selections'] if sel['Participant'] == participant)
              odds = selection['Odds']
              nextNext = self.getNextNext(bet['Selections'], participant)
              if " Total Games" in name and nextNext and participant == nextNext['Participant']:
                oppOdds = nextNext['Odds']
                title = participant + " Total Games" 
                if title not in output:
                  output[title] = {
                    "Line": line if line != 0 else .5,
                    "Over Odds": float(odds.replace('Even','+100')),
                    "Under Odds": float(oppOdds.replace('Even','+100'))
                  }
                  break
              else:
                oppOdds = next(sel['Odds'] for sel in bet['Selections'] if sel['Participant'] != participant)
                if title not in output:
                  output[title] = {
                    "Line": line if line != 0 else .5
                  }
                output[title]["Over Odds"] = float(odds.replace('Even','+100'))
                output[title]["Under Odds"] = float(oppOdds.replace('Even','+100'))
              # print(bet)
            else:
              title = name
              line = next(sel['Points'] for sel in bet['Selections'] if sel['Participant'] == participant)
              odds = selection['Odds']
              if title not in output:
                output[title] = {
                  "Line": line if line != 0 else .5
                }
              participant = participant.replace("Yes","Over").replace("No","Under")
              output[title][participant+" Odds"] = float(odds.replace('Even','+100'))
          except Exception as e:
            print("Error parsing bet",e,selection,bet)
            continue
    return output
  
  def getNextNext(self, selections, participant):
    count = 0
    for sel in selections:
      if sel['Participant'] == participant:
        count += 1
      if count == 2:
        return sel
    return None
  
  def skipTypes(self, category, betType):
    skip = ['1st Set Correct Score Group', '1st Set Correct Score', 'To Win', 'Exact Number of Sets - Best of 5',
            'to Win a Set','Any Set to be Won to Nil', 'Correct Score - Best of 5 Sets']
    for t in skip:
      if t in betType:
        return True
    
    if self.sport == 'MLB' and category == 'Game Props':
      for t in ['Exact', 'Result', 'Number', '?', 'Banded',
                'Race','Margin', 'Thrown', 'Recorded',
                'Odd/Even', 'Highest', '3-Way', 'Team To ']:
        if t in betType:
          return True
    
    return False
  
  def fixNames(self, name):
    replacements = {
      'Vince Williams': 'Vince Williams Jr.',
      'T. Young': 'Trae Young',
      'Trey Murphy': 'Trey Murphy III',
      'D. Avdija': 'Deni Avdija',
      'N. Claxton': 'Nic Claxton',
      'J. Brunson': 'Jalen Brunson',
      'K. Kuzma': 'Kyle Kuzma',
      'J. Harden': 'James Harden',
      'L. Doncic': 'Luka Doncic',
      'T. Harris': 'Tobias Harris',
      'P.J. Washington': 'PJ Washington',
      'N. Vucevic': 'Nikola Vucevic',
      'P. Banchero': 'Paolo Banchero',
      'P. Reed': 'Paul Reed',  
      'Derrick Jones': 'Derrick Jones Jr.',
      'A. Drummond': 'Andre Drummond',
      'A. Sengun': 'Alperen Sengun',
      'Kelly Oubre': 'Kelly Oubre Jr.',
      'S. Barnes': 'Scottie Barnes',
      'J. Poeltl': 'Jakob Poeltl',
      'J. Nurkic': 'Jusuf Nurkic',
      'J. Allen': 'Jarrett Allen',
      'J. Giddey': 'Josh Giddey',
      'C. Holmgren': 'Chet Holmgren',
      'E. Mobley': 'Evan Mobley',
      'C. Cunningham': 'Cade Cunningham',
      'M. Turner': 'Myles Turner',
      'J. Duren': 'Jalen Duren',
      'V. Wembanyama': 'Victor Wembanyama',
      'W. Carter Jr.': 'Wendell Carter Jr.',
      'J. Valanciunas': 'Jonas Valanciunas',
      'J. Johnson': 'Jalen Johnson',
      'N. Richards': 'Nick Richards',
      'J. Walker': 'Jabari Walker',
      'D. Ayton': 'Deandre Ayton',
      'J. Smith Jr.': 'Jabari Smith Jr.',
      'I. Zubac': 'Ivica Zubac',
      'S. Gilgeous-Alexander': 'Shai Gilgeous-Alexander',
      'T. Haliburton': 'Tyrese Haliburton',
      'M. Bagley III': 'Marvin Bagley III',
      'D. Sabonis': 'Domantas Sabonis',
      'B. Portis': 'Bobby Portis',
      'D. Gafford': 'Daniel Gafford',
      'J. Tatum': 'Jayson Tatum',
      'A. Gordon': 'Aaron Gordon',
      'L. James': 'LeBron James',
      'P. Siakam': 'Pascal Siakam',
      'P. Achiuwa': 'Precious Achiuwa',
      'K. Porzingis': 'Kristaps Porzingis',
      'D. Mitchell': 'Donovan Mitchell',
      'A. Davis': 'Anthony Davis',
      'S. Aldama': 'Santi Aldama',
      'J. Green': 'Jalen Green',
      'J. Konchar': 'John Konchar',
      'O. Okongwu': 'Onyeka Okongwu',
      'B. Adebayo': 'Bam Adebayo',
      'J. Hart': 'Josh Hart',
      'R. Gobert': 'Rudy Gobert',
      'G. Antetokounmpo': 'Giannis Antetokounmpo',
      'D. White': 'Coby White',
      'D. Murray': 'Dejounte Murray',
      'J. Murray': 'Jamal Murray',
      'W. Kessler': 'Walker Kessler',
      'T. Maxey': 'Tyrese Maxey',
      'I. Hartenstein': 'Isaiah Hartenstein',
      'N. Jokic': 'Nikola Jokic',
      'K. Love': 'Kevin Love',
      'M. Porter Jr.': 'Michael Porter Jr.',
      'L. Markkanen': 'Lauri Markkanen',
      'K. Dunn': 'Kris Dunn',
      'J. Collins': 'John Collins',
      'D. Green': 'Draymond Green',
      'K. Olynyk': 'Kyle Olynyk',
      'C. Sexton': 'Collin Sexton',
      'D. Lillard': 'Damian Lillard',
      'Z. Williamson': 'Zion Williamson',
      'J. Landale': 'Jock Landale',
      'J. Sochan': 'Jeremy Sochan',
      'F. VanVleet': 'Fred VanVleet',
      'D. Schroder': 'Dennis Schroder',
      'D. Russell': "D'Angelo Russell",
      'C. Capela': 'Clint Capela',
      'J. Wiseman': 'James Wiseman',
      'UT Arlington Mavericks': 'UT Arlington',
      'Seattle Redhawks': 'Seattle U',
      'Green Bay Phoenix': 'Wisc Green Bay',
      'Youngstown State Penguins': 'Youngstown State',
      'Princeton Tigers': 'Princeton',
      'Boise State Broncos': 'Boise State',
      'Utah Utes': 'Utah',
      'Tarleton St Texans': 'Tarleton St',
      'Southeast Missouri State Redhawks': 'SE Missouri State',
      'Oregon Ducks': 'Oregon',
      'Oregon State Beavers': 'Oregon State',
      'Wisconsin Badgers': 'Wisconsin',
      'Le Moyne Dolphins': 'Le Moyne',
      'Cal St Northridge': 'Cal State Northridge',
      'Boston College Eagles': 'Boston College',
      'Portland State Vikings': 'Portland State',
      'Idaho State Bengals': 'Idaho State',
      'Alabama A&M Bulldogs': 'Alabama A&M',
      'Belmont Bruins': 'Belmont',
      'South Florida Bulls': 'South Florida',
      'Ball State Cardinals': 'Ball State',
      'Connecticut Huskies': 'Connecticut',
      'Georgetown Hoyas': 'Georgetown',
      'Iowa State Cyclones': 'Iowa State',
      "Mount St. Mary's Mountaineers": "Mt. St. Mary's",
      'Abilene Christian Wildcats': 'Abilene Christian',
      'Eastern Kentucky Colonels': 'Eastern Kentucky',
      'Austin Peay Governors': 'Austin Peay',
      'Siena Saints': 'Siena',
      'Santa Clara Broncos': 'Santa Clara',
      'Chicago State Cougars': 'Chicago State',
      'Colgate Raiders': 'Colgate',
      'Clemson Tigers': 'Clemson',
      'Jacksonville State Gamecocks': 'Jacksonville State',
      'Kentucky Wildcats': 'Kentucky',
      'Morehead State Eagles': 'Morehead State',
      'Northern Kentucky Norse': 'Northern Kentucky',
      'Auburn Tigers': 'Auburn',
      'San Francisco Dons': 'San Francisco',
      'Tennessee State Tigers': 'Tennessee State',
      'Northern Arizona Lumberjacks': 'Northern Arizona',
      'Kennesaw State Owls': 'Kennesaw St',
      'Incarnate Word Cardinals': 'Incarnate Word',
      'Houston Christian Huskies': 'Houston Christian',
      'Bradley Braves': 'Bradley',
      'Robert Morris Colonials': 'Robert Morris',
      'Western Michigan Broncos': 'Western Michigan',
      'Arkansas Pine Bluff Golden Lions': 'Arkansas Pine Bluff',
      'Valparaiso Beacons': 'Valparaiso',
      'South Alabama Jaguars': 'South Alabama',
      'Cal Poly Mustangs': 'Cal Poly SLO',
      'Long Beach State Beach': 'Long Beach State',
      'Appalachian State Mountaineers': 'Appalachian State',
      'Illinois State Redbirds': 'Illinois State',
      'Utah Valley Wolverines': 'Utah Valley',
      'Northern Illinois Huskies': 'Northern Illinois',
      'Kansas State Wildcats': 'Kansas State',
      'Fairleigh Dickinson Knights': 'Fairleigh Dickinson',
      'North Alabama Lions': 'North Alabama',
      'New Hampshire Wildcats': 'New Hampshire',
      'Oklahoma State Cowboys': 'Oklahoma State',
      'Long Island Sharks': 'Long Island',
      'Hofstra Pride': 'Hofstra',
      'Murray State Racers': 'Murray State',
      'Missouri Tigers': 'Missouri',
      'Seattle U Kraken': 'Seattle Kraken',
      'Rice Owls': 'Rice',
      "Saint Mary's Gaels": 'Saint Marys CA',
      'Air Force Falcons': 'Air Force',
      'Brown Bears': 'Brown',
      'SIU Edwardsville Cougars': 'SIU Edwardsville',
      'Middle Tennessee Blue Raiders': 'Middle Tennessee State',
      'Lindenwood Lions': 'Lindenwood',
      'Prairie View A&M Panthers': 'Prairie View A&M',
      'Bethune-Cookman Wildcats': 'Bethune Cookman',
      'Detroit Mercy Titans': 'Detroit',
      'South Carolina State Bulldogs': 'South Carolina State',
      'Jackson State Tigers': 'Jackson State',
      'Manhattan Jaspers': 'Manhattan',
      'Chattanooga Mocs': 'Chattanooga',
      'Arizona State Sun Devils': 'Arizona State',
      'Washington State Cougars': 'Washington State',
      'Missouri State Bears': 'Missouri State',
      'North Florida Ospreys': 'North Florida',
      "Saint Joseph's Hawks": "St. Joseph's",
      'Portland Pilots': 'Portland',
      'UNC Greensboro': 'NC Greensboro',
      'Providence Friars': 'Providence',
      'Stetson Hatters': 'Stetson',
      'Binghamton Bearcats': 'Binghamton',
      'Sacred Heart Pioneers': 'Sacred Heart',
      'Buffalo Bulls': 'Buffalo',
      'Georgia Southern Eagles': 'Georgia Southern',
      'Northwestern State Demons': 'Northwestern State',
      'Montana Grizzlies': 'Montana',
      'Northern Colorado Bears': 'Northern Colorado',
      'CSU Bakersfield Roadrunners': 'Cal State Bakersfield',
      'UT Martin Skyhawks': 'Tennessee Martin',
      'Loyola Chicago Ramblers': 'Loyola Chicago',
      'George Washington Colonials': 'George Washington',
      'Northeastern Huskies': 'Northeastern',
      'Jacksonville Dolphins': 'Jacksonville',
      'UC Santa Barbara Gauchos': 'UC Santa Barbara',
      'East Carolina Pirates': 'East Carolina',
      'North Carolina A&T Aggies': 'North Carolina A&T',
      'Fresno State Bulldogs': 'Fresno State',
      'Georgia State Panthers': 'Georgia State',
      'Iona Gaels': 'Iona',
      'Texas A&M-Corpus Christi': 'Texas A&M Corpus',
      'Southern Illinois Salukis': 'Southern Illinois',
      'Western Carolina Catamounts': 'Western Carolina',
      'Quinnipiac Bobcats': 'Quinnipiac',
      'Bucknell Bison': 'Bucknell',
      'Washington Huskies': 'Washington',
      'Eastern Michigan Eagles': 'Eastern Michigan',
      'Mississippi State Bulldogs': 'Mississippi State',
      'North Dakota State Bison': 'North Dakota State',
      'Monmouth Hawks': 'Monmouth',
      'Pacific Tigers': 'Pacific',
      'Arkansas State Red Wolves': 'Arkansas State',
      'Texas A&M–Commerce Lions': 'Tex A&M Commerce',
      'Stony Brook Seawolves': 'Stony Brook',
      'UNC Asheville': 'NC Asheville',
      'Syracuse Orange': 'Syracuse',
      'Pepperdine Waves': 'Pepperdine',
      'Wright State Raiders': 'Wright State',
      'Pennsylvania Quakers': 'Pennsylvania',
      'Western Illinois Leathernecks': 'Western Illinois',
      'Merrimack Warriors': 'Merrimack',
      'California Baptist Lancers': 'California Baptist',
      'Cincinnati Bearcats': 'Cincinnati',
      'Southeastern Louisiana Lions': 'SE Louisiana',
      'New Mexico State Aggies': 'New Mexico State',
      'Cal State Fullerton Titans': 'Cal State Fullerton',
      'San Diego Toreros': 'San Diego',
      'Montana State Bobcats': 'Montana State',
      'Houston Cougars': 'Houston',
      'Lipscomb Bisons': 'Lipscomb',
      'South Carolina Gamecocks': 'South Carolina',
      'Sacramento State Hornets': 'Sacramento State',
      'Texas Southern Tigers': 'Texas Southern',
      'Fairfield Stags': 'Fairfield',
      'Louisville Cardinals': 'Louisville',
      'Eastern Illinois Panthers': 'Eastern Illinois',
      'Central Arkansas Bears': 'Central Arkansas',
      'McNeese State Cowboys': 'McNeese State',
      'Florida Gators': 'Florida',
      'Milwaukee Panthers': 'Wisc Milwaukee',
      'Bellarmine Knights': 'Bellarmine',
      'Nicholls State Colonels': 'Nicholls State',
      'Loyola Marymount Lions': 'Loyola Marymount',
      'Stanford Cardinal': 'Stanford',
      'Drexel Dragons': 'Drexel',
      'Alabama State Hornets': 'Alabama State',
      'Western Kentucky Hilltoppers': 'Western Kentucky',
      'Columbia Lions': 'Columbia',
      'Indiana State Sycamores': 'Indiana State',
      'Oklahoma Sooners': 'Oklahoma',
      'Stonehill Skyhawks': 'Stonehill',
      'Stephen F. Austin Lumberjacks': 'Stephen F. Austin',
      'New Orleans Privateers': 'New Orleans',
      'Michigan State Spartans': 'Michigan State',
      "St. John's Red Storm": "St. John's",
      'Weber State Wildcats': 'Weber State',
      'Toledo Rockets': 'Toledo',
      'Idaho Vandals': 'Idaho',
      'Eastern Washington Eagles': 'Eastern Washington',
      'Boston U Terriers': 'Boston U',
      'North Carolina Tar Heels': 'North Carolina',
      'St. Bonaventure Bonnies': 'St. Bonaventure',
      'Lafayette Leopards': 'Lafayette',
      'Duquesne Dukes': 'Duquesne',
      'Baylor Bears': 'Baylor',
      'Ohio State Buckeyes': 'Ohio State',
      'UTEP Miners': 'UTEP',
      'New Mexico Lobos': 'New Mexico',
      'Florida A&M Rattlers': 'Florida A&M',
      'Saint Louis Billikens': 'Saint Louis',
      'Holy Cross Crusaders': 'Holy Cross',
      'Florida Gulf Coast Eagles': 'Florida Gulf Coast',
      'UCLA Bruins': 'UCLA',
      'Texas State Bobcats': 'Texas State',
      'Mercer Bears': 'Mercer',
      'Rider Broncs': 'Rider',
      'St. Francis (PA) Red Flash': 'St. Francis PA',
      'Harvard Crimson': 'Harvard',
      'High Point Panthers': 'High Point',
      'Grand Canyon Antelopes': 'Grand Canyon',
      'Texas A&M Aggies': 'Texas A&M',
      'Creighton Bluejays': 'Creighton',
      'Cornell Big Red': 'Cornell',
      'Alcorn State Braves': 'Alcorn State',
      'South Dakota State Jackrabbits': 'South Dakota State',
      'Providence@Butler Bulldogs': 'Butler',
      'Mississippi Valley State Delta Devils': 'Mississippi Valley State',
      'Marist Red Foxes': 'Marist',
      'Georgia Tech Yellow Jackets': 'Georgia Tech',
      'Loyola (MD) Greyhounds': 'Loyola Maryland',
      'Utah Tech Trailblazers': 'Utah Tech',
      'Drake Bulldogs': 'Drake',
      'Miami Hurricanes': 'Miami Florida',
      'Boise State@Utah State Aggies': 'Utah State',
      'Michael Matheson': 'Mike Matheson',
      'Tennessee Volunteers': 'Tennessee',
      'College of Charleston Cougars': 'College Of Charleston',
      'Miami (OH) Redhawks': 'Miami Ohio',
      'Grambling State Tigers': 'Grambling',
      'Southern Utah Thunderbirds': 'Southern Utah',
      'Southern Indiana Screaming Eagles': 'Southern Indiana',
      'BYU Cougars': 'BYU',
      'Xavier Musketeers': 'Xavier',
      "Saint Peter's Peacocks": "St. Peter's",
      'Central Connecticut State': 'Central Connecticut',
      'Marquette Golden Eagles': 'Marquette',
      'Vanderbilt Commodores': 'Vanderbilt',
      'Kansas Jayhawks': 'Kansas',
      'Maine Black Bears': 'Maine',
      'Nebraska-Omaha Mavericks': 'Nebraska Omaha',
      'Illinois Fighting Illini': 'Illinois',
      'USC Trojans': 'USC',
      'Alexander Wennberg': 'Alex Wennberg',
      'Bryant Bulldogs': 'Bryant',
      'California Golden Bears': 'California',
      'Evansville Purple Aces': 'Evansville',
      'Dartmouth Big Green': 'Dartmouth',
      'Ohio Bobcats': 'Ohio',
      'Gonzaga Bulldogs': 'Gonzaga',
      'Tennessee Tech Golden Eagles': 'Tennessee Tech',
      'Yale Bulldogs': 'Yale',
      'Southern Miss Golden Eagles': 'Southern Miss',
      'Duke Blue Devils': 'Duke',
      'Maryland Terrapins': 'Maryland',
      'Lamar Cardinals': 'Lamar',
      'UNC Greensboro Spartans': 'NC Greensboro',
      'Colorado State Rams': 'Colorado State',
      'Seattle U Kraken Kraken': 'Seattle Kraken',
      "Gardner-Webb Runnin' Bulldogs": 'Gardner Webb',
      'Wyoming Cowboys': 'Wyoming',
      'Utah State Aggies': 'Utah State',
      'Towson Tigers': 'Towson',
      'Northern Iowa Panthers': 'Northern Iowa',
      'Fordham Rams': 'Fordham',
      'Cleveland State Vikings': 'Cleveland State',
      'Arkansas-Pine Bluff Golden Lions': 'Arkansas Pine Bluff',
      'UNC Asheville Bulldogs': 'NC Asheville',
      'San Diego State Aztecs': 'San Diego State',
      'Seton Hall Pirates': 'Seton Hall',
      'Dayton Flyers': 'Dayton',
      'Davidson Wildcats': 'Davidson',
      'Presbyterian Blue Hose': 'Presbyterian',
      'San Jose State Spartans': 'San Jose State',
      'North Texas Mean Green': 'North Texas',
      'UTSA Roadrunners': 'Texas San Antonio',
      'Sam Houston State Bearkats': 'Sam Houston State',
      'Tarleton State Texans': 'Tarleton St',
      'Louisiana Tech Bulldogs': 'Louisiana Tech',
      'UNC Wilmington Seahawks': 'NC Wilmington',
      'South Dakota Coyotes': 'South Dakota',
      'UC Davis Aggies': 'UC Davis',
      'Wichita State Shockers': 'Wichita State',
      'Coastal Carolina Chanticleers': 'Coastal Carolina',
      'Florida Atlantic Owls': 'Florida Atlantic',
      'UC San Diego Tritons': 'UC San Diego',
      'Charlotte 49ers': 'Charlotte U',
      'Little Rock Trojans': 'Arkansas Little Rock',
      'Temple Owls': 'Temple',
      'UC Riverside Highlanders': 'Cal Riverside',
      'Memphis Tigers': 'Memphis',
      'Marshall Thundering Herd': 'Marshall',
      'UT Rio Grande Valley Vaqueros': 'UT Rio Grande Valley',
      'Colorado Buffaloes': 'Colorado',
      'Troy Trojans': 'Troy',
      'UM Kansas City Roos': 'UMKC',
      'Northwestern Wildcats': 'Northwestern',
      'Oral Roberts Golden Eagles': 'Oral Roberts',
      'FIU Golden Panthers': 'Florida International',
      'Louisiana-Monroe Warhawks': 'UL - Monroe',
      'North Dakota Fighting Hawks': 'North Dakota',
      'SMU Mustangs': 'SMU',
      'Elon Phoenix': 'Elon',
      'Rutgers Scarlet Knights': 'Rutgers',
      'Minnesota Golden Gophers': 'Minnesota',
      'Hawaii Rainbow Warriors': 'Hawaii',
      'Tulane Green Wave': 'Tulane',
      'Purdue Boilermakers': 'Purdue',
      'Albany Great Danes': 'Albany NY',
      'Texas Tech Red Raiders': 'Texas Tech',
      'Maryland Baltimore': 'MD Baltimore County',
      'Delaware Blue Hens': 'Delaware',
      'Vermont Catamounts': 'Vermont',
      'LIU Sharks': 'Long Island',
      'Denver Pioneers': 'Denver',
      'Wagner Seahawks': 'Wagner',
      'NJIT Highlanders': 'NJIT',
      'Campbell Fighting Camels': 'Campbell',
      'Villanova Wildcats': 'Villanova',
      'Niagara Purple Eagles': 'Niagara',
      'Canisius Golden Griffins': 'Canisius',
      'Queens University Royals': 'Queens',
      'Michigan Wolverines': 'Michigan',
      'Texas Longhorns': 'Texas',
      'Pittsburgh Panthers': 'Pittsburgh',
      'NC Greensboro Spartans': 'NC Greensboro',
      'Kent State Golden Flashes': 'Kent State',
      'Alabama Crimson Tide': 'Alabama',
      'West Virginia Mountaineers': 'West Virginia',
      'UC Irvine Anteaters': 'Cal Irvine',
      'Florida State Seminoles': 'Florida State',
      'Georgia Bulldogs': 'Georgia',
      'Bowling Green Falcons': 'Bowling Green',
      'N.C. State Wolfpack': 'NC State',
      'Central Michigan Chippewas': 'Central Michigan',
      'St. Thomas (MN) Tommies': 'St. Thomas',
      'Massachusetts Minutemen': 'Massachusetts',
      'Samford Bulldogs': 'Samford',
      'Arkansas Razorbacks': 'Arkansas',
      'LSU Tigers': 'LSU',
      'Iowa Hawkeyes': 'Iowa',
      'Akron Zips': 'Akron',
      'East Tennessee State Buccaneers': 'East Tenn State',
      'Butler Bulldogs': 'Butler',
      'Arizona Wildcats': 'Arizona',
      'TCU Horned Frogs': 'TCU',
      'Nebraska Cornhuskers': 'Nebraska',
      'Howard Bison': 'Howard',
      'Delaware State Hornets': 'Delaware State',
      'Coppin State Eagles': 'Coppin State',
      'NC Asheville Bulldogs': 'NC Asheville',
      'North Carolina Central Eagles': 'North Carolina Central',
      'Morgan State Bears': 'Morgan State',
      'Wofford Terriers': 'Wofford',
      'Penn State Nittany Lions': 'Penn State',
      'Maryland-Eastern Shore Hawks': 'MD Eastern Shore',
      'La Salle Explorers': 'La Salle',
      'Navy Midshipmen': 'Navy',
      'UCF Knights': 'Central Florida',
      'UNLV Runnin Rebels': 'UNLV',
      'Nevada Wolf Pack': 'Nevada',
      'Southern University Jaguars': 'Southern',
      'Massachusetts-Lowell River Hawks': 'UMass Lowell',
      'Purdue Fort Wayne Mastodons': 'IPFW',
      'DePaul Blue Demons': 'DePaul',
      'Indiana Hoosiers': 'Indiana',
      'Furman Paladins': 'Furman',
      'UAB Blazers': 'UAB',
      'Rhode Island Rams': 'Rhode Island',
      'UIC Flames': 'Illinois Chicago',
      'Jesús Sánchez': 'Jesus Sanchez',
      'Cristian Garin': 'Christian Garin',
      'Yandy Díaz': 'Yandy Diaz',
      'José Berríos': 'Jose Berrios',
      'Elias Díaz': 'Elias Diaz',
      'Javier Báez': 'Javier Baez',
      'René Pinto': 'Rene Pinto',
      'Pablo López': 'Pablo Lopez',
      'Julio Rodríguez': 'Julio Rodriguez',
      'Harold Ramírez': 'Harold Ramirez',
      'Eloy Jiménez': 'Eloy Jimenez',
      'Eugenio Suárez': 'Eugenio Suarez',
      'Jeremy Peña': 'Jeremy Pena',
      'Yoán Moncada': 'Yoan Moncada',
      'Adolis García': 'Adolis Garcia',
      'Carlos Rodón': 'Carlos Rodon',
      'Jose Caballero': 'José Caballero',
      'Ronald Acuña Jr.': 'Ronald Acuna Jr.',
      'Giovanni Mpetshi Perricard': 'Giovanni Perricard',
      'Tomas Barrios Vera': 'Marcelo Tomas Barrios-Vera',
      'José Quintana': 'Jose Quintana',
      'Ramón Laureano': 'Ramon Laureano',
      'Avisaíl García': 'Avisail Garcia',
      'José Abreu': 'Jose Abreu',
      'Andrés Giménez': 'Andres Gimenez',
      'K. Durant': 'Kevin Durant',
      'Troy Brown': 'Troy Brown Jr.',
      'Krejcikova/Siegemund': 'B Krejcikova / L Siegemund',
      'Matos/Meligeni Rodrigues Alves': 'Felipe Meligeni Rodrigues Alves',
      'Felix Auger-Aliassime': 'Felix Auger Aliassime',
      'Hsu Yu-hsiou': 'Yu Hsiou Hsu',
      'Ramón Urías': 'Ramon Urias',
      'Mike Sian': 'Michael Sian',
      'Camila Osorio': 'Maria Camila Osorio Serrano',
      'Korda/Thompson': 'S Korda / J Thompson',
      'Felipe Alves': 'Felipe Meligeni Rodrigues Alves',
      'Tomás Nido': 'Tomas Nido',
      'Hsieh/Mertens': 'S-W. Hsieh / E Mertens',
      'Pedro Boscardin Dias': 'Pedro Dias',
      'J. Embiid': 'Joel Embiid',
      'Bolelli/Vavassori': 'Bolelli S / Vavassori A',
      'Murray/Venus': 'J Murray / M Venus',
      'Mauricio Dubón': 'Mauricio Dubon',
      'Behar/Pavlasek': 'A Behar / A Pavlasek',
      'Lammons/Withrow': 'N Lammons / J Withrow',
      'Granollers/Zeballos': 'Granollers M / Zeballos H',
      'K. Middleton': 'Khris Middleton',
      'Doumbia/Reboul': 'S Doumbia / F Reboul',
      'Omar Narváez': 'Omar Narvaez',
      'Nys/Zielinski': 'H Nys / J Zielinski',
      'Botic Van de Zandschulp': 'Botic Van De Zandschulp',
      'JiSung Nam': 'Ji-Sung Nam (Sets)',
      'Joel Josef Schwarzler': 'Joel Schwaerzler',
      'Simeon Woods-Richardson': 'Simeon Woods Richardson',
      'Jaqueline Adina Cristian': 'Jaqueline Cristian',
      'Alex de Minaur': 'Alex De Minaur',
      'José Azocar': 'Jose Azocar',
      'Christian Vázquez': 'Christian Vazquez',
      'Luis Urías': 'Luis Urias',
      'Ranger Suárez': 'Ranger Suarez',
      'Jesus Luzardo': 'Jesús Luzardo',
      'Andy Ibanez': 'Andy Ibáñez',
      'Tung-Lin Wu': 'Tung-Lin WU',
      'James Kent Trotter': 'James Trotter',
      'Anna-Karolina Schmiedlova': 'Anna Schmiedlova',
      'Seong Chan Hong': 'Seong-chan Hong',
      'Mackenzie McDonald': 'Mackenzie Mcdonald',
      'Jeffrey John Wolf': 'JJ Wolf',
      'Nicolas Moreno de Alboran': 'Nicolas Moreno De Alboran',
      'Daniel Evans': 'Dan Evans',
      'Leylah Fernandez': 'Leylah Annie Fernandez',
      'Andy Ibáñez': 'Andy Ibanez',
      'Cristopher Sánchez': 'Cristopher Sanchez',
      'Wang/Zheng': 'Wang X / Zheng S',
      'Erik Arutiunian': 'Eric Arutiunian',
      'Gille/Vliegen': 'Gille S / Vliegen J',
      'Errani/Paolini': 'Errani S / Paolini J',
      'Koolhof/Mektic': 'Koolhof W / Mektic N',
      'A. Edwards': 'Anthony Edwards',
      'Dolehide CA/Krawczyk': 'Dolehide C / Krawczyk D',
      'Bublik/Shelton': 'Bublik A / Shelton B',
      'Arevalo/Pavic': 'Arevalo M / Pavic M',
      'P. Washington': 'PJ Washington',
      'Randy Vasquez': 'Randy Vásquez',
      'Anca Alexia Todoni': 'Anca Todoni',
      'Reynaldo López': 'Reynaldo Lopez',
      'Miriam Bianca Bulgaru': 'Miriam Bulgaru',
      'Oscar Colas': 'Oscar Colás',
      'Matheus Pucinelli de Almeida': 'Matheus Pucinelli De Almeida',
      'Anastasiya Konstantinovna Soboleva': 'Anastasiya Soboleva',
      'J.P. Martinez': 'J.P. Martínez',
      'Yexin Ma': 'Ye-Xin Ma',
      'Ariana Geerlings Martinez': 'Ariana Geerlings',
      'Khumoyun Sultanov': 'Khumoun Sultanov',
      'Isis Louise van Den Broek': 'Isis Louise Van Den Broek',
      'Joan Nadal Vives': 'Joan Nadal',
      'Samantha Murray Sharan': 'Samantha Murray',
      'Angela Fita Boluda': 'Angela Fita',
      'Bianca Andreescu': 'Bianca Vanessa Andreescu',
      'Nuria Parrizas Diaz': 'Nuria Parrizas-Diaz',
      'Greet Minnen': 'Greetje Minnen',
      'Mateo Barreiros Reyes': 'Mateo Alejandro Barreiros Reyes',
      'Santiago Rodriguez Taverna': 'Santiago FA Rodriguez Taverna',
      'Tim van Rijthoven': 'Tim Van Rijthoven',
      'Henry Searle': 'Hynek Barton',
      'Joao Lucas Reis Da Silva': 'Joao Lucas Silva',
      'Jesper de Jong': 'Jesper De Jong',
      'Jesús Luzardo': 'Jesus Luzardo',
      'José Suarez': 'Jose Suarez',
      'D. Lively II Double+Double': 'Dereck Lively II',}
    for oldStr, newStr in replacements.items():
      if "Milwaukee Bucks" not in oldStr and "Seattle Kraken" not in oldStr:
        name = re.sub(oldStr, newStr, name)
    if self.sport in ['WTA','ATP']:
      name = name.replace(' de ', ' De ')
    return name