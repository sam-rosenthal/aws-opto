import json, requests, json, pytz, time, random, re
from datetime import datetime
from dateutil import parser
from time import sleep  
from random import uniform

class DraftkingsScraper():
  def __init__(self, sport="NFL"):
    self.sport = sport
    self.eventGroups = {
      "MLB": "84240",
      "NFL": "88808",
      "NBA": "42648",
      "NHL": "42133",
      "PGA": "43759",
      "UFC": "9034",
      "CFB": "87637",
      "NCAAB": "92483",
      "WNCAAB": "36647",
      "EPL": "40253",
      "ATP": "91170",
      "WTA": "91174",
    }
    self.session = requests.Session()
    # self.getRequest('https://gaming-us-va.draftkings.com/api/wager/v1/generateAnonymousEnterpriseJWT')

    self.setBetFilters()
    self.setMaxEvents()
    self.setMatchups()

  def getUserAgent(self):
    agents = [
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
      "Mozilla/5.0 (Android 14; Mobile; rv:126.0) Gecko/126.0 Firefox/126.0"
    ]
    return random.choice(agents)
    
  def getRequestHeaders(self):
    headers = { 
      "user-agent": self.getUserAgent(),
      "accept": "*/*",
      "accept-language": "en-US,en;q=0.9",
      "origin": "https://sportsbook.draftkings.com",
      "referer": "https://sportsbook.draftkings.com/",
      "sec-fetch-dest": "empty",
      "sec-fetch-mode": "cors",
      "sec-fetch-site": "same-site",
      "sec-gpc": "1",
    }
    return {"headers": headers}
  
  def getRequest(self, url):
    requestHeaders = self.getRequestHeaders()
    sleep(uniform(0,1))
    print("URL:", url)
    return self.session.get(url, **requestHeaders)
    
  def setMatchups(self):
    self.matchups = {}
    if self.sport not in self.eventGroups.keys():
      return None
    if self.sport == "WTA" or self.sport == "ATP":
      dkEvents = []
      displayGroupInfo = self.getRequest('https://sportsbook.draftkings.com//sites/US-VA-SB/api/v2/displaygroupinfo?format=json')
      tennisTournaments = [d for d in displayGroupInfo.json()['displayGroupInfos'] if d['displayName'] == 'Tennis'][0]
      tourneyIds = []
      for tourney in tennisTournaments['eventGroupInfos']:
        if 'tags' in tourney and ('Doubles' not in tourney['eventGroupName']) and (
          self.sport in tourney['eventGroupName'] or (self.sport == 'ATP' and (
              ('Challenger' in tourney['eventGroupName']) or 
              ('French Open (M)' in tourney['eventGroupName']) or
              ('Wimbledon (M)' in tourney['eventGroupName'])) or
                self.sport == 'WTA' and (
                  'French Open (W)' in tourney['eventGroupName'] or
                  'Wimbledon (W)' in tourney['eventGroupName'] ))):
          tourneyIds.append(tourney['eventGroupId'])
      for id in tourneyIds:
        url = "https://sportsbook-nash-usva.draftkings.com/sites/US-VA-SB/api/v5/eventgroups/"+id+"?format=json"
        dkEvents += self.getRequest(url).json()['eventGroup']['events']
    else:
      url = "https://sportsbook-nash-usva.draftkings.com/sites/US-VA-SB/api/v5/eventgroups/"+self.eventGroups[self.sport]+"?format=json"
      dkEvents = self.getRequest(url).json()['eventGroup']['events']
    if self.sport in self.maxEvents:
      dkEvents = dkEvents[:self.maxEvents[self.sport]]
    for dkEvent in dkEvents:
      if dkEvent['eventStatus']['state'] == "NOT_STARTED":
        if 'teamName1' in dkEvent.keys() and len(dkEvent['teamName1']) > 0:
          if self.sport in ['UFC', 'WTA', 'ATP']:
            teams = [dkEvent['teamName1'], dkEvent['teamName2']]
            teams.sort()
            matchupName = teams[0]+"@"+teams[1]
          else:
            matchupName = dkEvent['teamName1']+"@"+dkEvent['teamName2']
        else:
          matchupName = dkEvent['name']
        startDateTime = parser.parse(dkEvent['startDate']).astimezone(pytz.timezone('US/Eastern'))
        self.matchups[matchupName] = {
          "EventId": str(dkEvent['eventId']),
          "StartTime": startDateTime.strftime("%Y/%m/%d %H:%M:%S"),
          'Bets': []
        }
    
  def getMatchups(self):
    return self.matchups
    
  def setTimestamp(self):
    timestamp = datetime.now().astimezone(pytz.timezone('America/New_York')).strftime('%Y/%m/%d %H:%M:%S')
    return timestamp

  def scrapeOdds(self):
    self.getMatchupBets()
    
  def getOdds(self):
    self.scrapeOdds()
    timestamp = self.setTimestamp()
    return {"Timestamp": timestamp, "Data": self.matchups}
    
  def getEventData(self, eventId):
    return "https://sportsbook-ca-on.draftkings.com/api/team/markets/dkusva/v3/event/"+eventId+"?format=json"

  def getMatchupBets(self):
    self.betData = {}
    for matchupName, matchupInfo in self.matchups.items():
      print(matchupName, matchupInfo)
      eventId = matchupInfo['EventId']
      time.sleep(random.uniform(.5,1))
      self.processEventId(eventId, matchupName)

  def processEventId(self, eventId, matchupName):
    response = self.getRequest(self.getEventData(str(eventId)))
    data = json.loads(response.content.decode('utf-8'))
    state = data['event']['eventStatus']['state']
    if state == "NOT_STARTED":
      self.updateBettingData(data, matchupName)

  def updateBettingData(self, data, matchupName):
    for eventCategory in data['eventCategories']:
      categoryName = eventCategory['name'].strip()
      # print(categoryName)
      if categoryName == 'Popular' or (self.sport in self.betCategories.keys() and categoryName not in self.betCategories[self.sport]):
        continue
      
      for component in eventCategory['componentizedOffers']:
        subcategoryName = component['subcategoryName'].strip()
        # print(categoryName,subcategoryName)
        if self.sport in self.betSubcategories.keys() and subcategoryName not in self.betSubcategories[self.sport]:
          continue
        for offer in component['offers'][0]:
          if 'label' not in offer.keys() or ('isOpen' not in offer.keys() or offer['isOpen'] != True):
            # print("Invalid offer, skipping",offer)
            continue
          
          label = offer['label'].strip().replace("  "," ").replace("Nicolas Claxton", "Nic Claxton").replace("Lamar Jackson (BAL)","Lamar Jackson")
          
          if (self.sport == "UFC" and self.includeBet(label) == False) or (
            self.sport == "MLB" and ('Alternate' in label or 
                                     'Listed Pitcher' in subcategoryName or 
                                     'H2H' in subcategoryName or 
                                     '1st' in subcategoryName or 
                                     '3-Way' in subcategoryName or 
                                     (categoryName == 'Game Props' and 
                                      subcategoryName != 'Team Total Runs'))):
            continue
          
          participantOutcomes = {}
          for outcome in offer['outcomes']:
            if 'label' in outcome.keys():
              try:
                participant = outcome['participant'].strip().replace("  "," ")
                participant = participant.replace("Nicolas Claxton", "Nic Claxton").replace("Lamar Jackson (BAL)","Lamar Jackson")
                if outcome['label'] in ["Over", "Under"]:
                  outcomeLabel = f"{outcome['label']} Odds" 
                else:
                  participant = outcome['label'] if participant == '' else participant
                  outcomeLabel = "Over Odds"
                  
                oddsAmerican = float(outcome['oddsAmerican'])
                
                if participant not in participantOutcomes:
                  participantOutcomes[participant] = {}
                  participantOutcomes[participant]['Line'] = []
                
                if 'line' in outcome:
                  if outcome['line'] not in list(participantOutcomes[participant]['Line']):
                    participantOutcomes[participant]['Line'].append(outcome['line']) 
                    
                  if outcomeLabel not in participantOutcomes[participant]:  
                    participantOutcomes[participant][outcomeLabel] = [oddsAmerican]
                  else: 
                    participantOutcomes[participant][outcomeLabel].append(oddsAmerican)
                  
                else:
                  participantOutcomes[participant]['Line'] = [-.5] if "Moneyline" in label else [.5]
                  participantOutcomes[participant]['Over Odds'] = [oddsAmerican]
                
              except Exception as e:
                print(categoryName, subcategoryName, outcome, e)
                continue
          for participant, values in participantOutcomes.items(): 
            title = label if participant in label else participant + " " + label
            if (subcategoryName == "Game" and title == "Total") or (
              subcategoryName == "Fight Lines" and title == "Total Rounds") or (
              subcategoryName == "Total Games" and title == "Total Games") or (
              subcategoryName == "Total Sets" and title == "Total Sets") or (
            ):
              if self.sport in ["WTA","ATP"]:
                split = title.split(' ')
                title = f'{matchupName} {split[0]} ({split[1]})' 
              else:
                title = matchupName + " Game Total" 
            title = self.titleRenamer(title)
            renaming = {
              "Three Pointers Made": "3 Point FG",
              "Double-Double":"Double+Double",
              "Triple-Double":"Triple+Double",
              "Points + Rebounds + Assists":"Pts+Rebs+Asts",
              "Anytime Goalscorer": "Goals",
              "Player Shots on Goal": "Shots on Goal",
              "Shots on Goal": "Shots On Goal",
              "Anytime TD Scorer": "TD Scorer",
              "TD Scorer": "Anytime TD",
              "Interceptions Thrown": "Interceptions",
              "Passing Completions":"Completions",
              "Passing Attempts": "Pass Attempts",
              "Passing Touchdowns" : "TD Passes",
              "Cameron Thomas": "Cam Thomas",
              "Alexander Wennberg": "Alex Wennberg",
              "John-Jason Peterka": "JJ Peterka",
              "Thomas Novak": "Tommy Novak",
              "Matthew Boldy": "Matt Boldy",
              "Cameron York": "Cam York",
              "Marvin Bagley": "Marvin Bagley III",
              "UIW": "Incarnate Word",
              "Southeastern Louisiana": "SE Louisiana",
              "Louisiana-Lafayette": "UL - Lafayette",
              "Prairie View": 'Prairie View A&M',
              "Bethune-Cookman": "Bethune Cookman",
              "Arkansas-Pine Bluff": "Arkansas Pine Bluff",
              "Michael Matheson": 'Mike Matheson',
              'Texas A&M-Commerce': 'Texas A&M Commerce',
              'McNeese': 'McNeese State',
              ': Team Total Goals': ' Team Total',
              "ETSU":'East Tenn State',
              'SIUE': 'SIU Edwardsville',
              'Southern Mississippi': 'Southern Miss',
              'Green Bay': 'Wisc Green Bay',
              'Central Connecticut State': 'Central Connecticut',
              'UNC Greensboro': 'NC Greensboro',
              'SFA': 'Stephen F. Austin',
              'Purdue Fort Wayne': 'IPFW',
              'Mississippi Valley': 'Mississippi Valley State',
              'Charleston': 'College Of Charleston',
              'UMBC': 'MD Baltimore County',
              "UConn": "Connecticut",
              "North Carolina State": "NC State",
              "Tarleton State": "Tarleton St",
              
              'Saint Josephs': "St. Joseph's",
              
              # 'Seattle': 'Seattle U',
              # 'Green Bay': 'Wisc Green Bay',
              'Saint Johns': "St. John's",
              'Tarleton State': 'Tarleton St',
              'Southeast Missouri State': 'SE Missouri State',
              'Cal Poly': 'Cal Poly SLO',
              'Saint Francis PA': 'St. Francis PA',
              'Alcorn': 'Alcorn State',
              'ULM': 'UL - Monroe',
              'UC Irvine': 'Cal Irvine',
              'UConn': 'Connecticut',
              'Mount Saint Marys': "Mount St. Mary's (MD)",
              'Mikey Eyssimont': 'Michael Eyssimont',
              'UNC Asheville': 'NC Asheville',
              'A&M-Corpus Christi': 'Texas A&M Corpus Christi',
              'SIUE': 'SIU Edwardsville',
              'Prairie View': 'Prairie View A&M',
              'Detroit Mercy': 'Detroit',
              'UC Riverside': 'Cal Riverside',
              'Boston University': 'Boston U',
              'Bethune-Cookman': 'Bethune Cookman',
              'Saint Peters': "St. Peter's",
              # 'Milwaukee': 'Wisc Milwaukee',
              'Gardner-Webb': 'Gardner Webb',
              'CSU Bakersfield': 'Cal State Bakersfield',
              'Miami FL': 'Miami Florida',
              'Saint Bonaventure': 'St. Bonaventure',
              'Texas A&M-Commerce': 'Texas A&M Commerce',
              'Michael Matheson': 'Mike Matheson',
              'Arkansas-Pine Bluff': 'Arkansas Pine Bluff',
              'Kennesaw State': 'Kennesaw St',
              'UIW': 'Incarnate Word',
              'Saint Thomas MN': 'St. Thomas',
              'Mississippi Valley': 'Mississippi Valley State',
              'UT Martin': 'Tennessee Martin',
              'North Carolina State': 'NC State',
              'Southeastern Louisiana': 'SE Louisiana',
              'UNC Greensboro': 'NC Greensboro',
              'McNeese': 'McNeese State',
              'Queens NC': 'Queens',
              'LIU': 'Long Island',
              'Southern Mississippi': 'Southern Miss',
              'Alexander Wennberg': 'Alex Wennberg',
              'Middle Tennessee': 'Middle Tennessee State',
              'Miami OH': 'Miami Ohio',
              'Central Connecticut State': 'Central Connecticut',
              # 'Kansas City': 'UMKC',
              'Saint Marys': 'Saint Marys CA',
              'Alexander Wennberg Goals': 'Alex Wennberg Goals',
              'Charleston': 'College Of Charleston',
              'Calvin Petersen': 'Cal Petersen',
              'Omaha': 'Nebraska Omaha',
              
              "Luis Robert": "Luis Robert Jr.",
              "Jose Caballero": "José Caballero",
              "Martin Maldonado": "Martín Maldonado",
              "Jazz Chisholm": "Jazz Chisholm Jr.",
              "Teoscar Hernandez": "Teoscar Hernández",

              "P.J. Washington": "PJ Washington",
              "Martin Perez": "Martín Pérez",
              "Marcelo Tomas Barrios Vera": "Marcelo Tomas Barrios-Vera",
              "Kike Hernandez": "Enrique Hernandez",
              "Martin Perez": "Martín Pérez",
              "Gary Sanchez": "Gary Sánchez",
              "Cristian Garin": "Christian Garin",
              "Michael Harris": "Michael Harris II",
              "Giovanni Mpetshi Perricard": "Giovanni Perricard",
              
              "Josh Smith": "Josh H. Smith",
              "Guiomar Maristany Zuleta De Reales": "Guiomar M Zuleta de Reales",
              "Mike Siani": "Michael Siani",
              
              "Danielle Rose Collins": "Danielle Collins",
              "Luis Urías": "Luis Urias",
              "Pedro Pages": "Pedro Pagés",
              "Jose Urena": "José Ureña",
              "Jaqueline Adina Cristian": "Jaqueline Cristian",
              "Jaqueline Adina Cristian": "Jaqueline Cristian",
              "Elena Gabriela Ruse": "Elena-Gabriela Ruse",
              "Jeffrey John Wolf": "JJ Wolf",
              "Giorgia Pedone": "Georgia Pedone",
              "Anna Karolina Schmiedlova": "Anna Schmiedlova",
              "Abdullah Shelbayh": "Abedallah Shelbayh",
              
              "Pedro Boscardin Dias": "Pedro Dias",
              "Seongchan Hong": "Seong-chan Hong",
              "Randy Vasquez": "Randy Vásquez",
              "Mackenzie McDonald": "Mackenzie Mcdonald",
              "Pedro Pagés": "Pedro Pages",
              "Anca Alexia Todoni": "Anca Todoni",
              "Miriam Bianca Bulgaru": "Miriam Bulgaru",
              "Oscar Colas": "Oscar Colás",
              "Albert Suarez": "Albert Suárez",
              "Tung-Lin Wu": "Tung-Lin WU",
              "Anastasiya Konstantinovna Soboleva": "Anastasiya Soboleva",
              "Oscar Colas": "Oscar Colás", 
              'Mateo Barreiros Reyes': 'Mateo Alejandro Barreiros Reyes',
              
              'Joan Nadal Vives': 'Joan Nadal',
              'Toby Alex Kodat': 'Toby Kodat',
              'Yexin Ma': 'Ye-Xin Ma',
              'Henry Searle': 'Harry Searle',
              'Roddery Munoz': 'Roddery Muñoz',
              'Antoine Cornut-Chauvinc': 'Antoine Cornut Chauvinc',
              'Pablo Carreno Busta': 'Pablo Carreno-Busta',
              'Oleksii Krutykh': 'Oleksil Krutykh',
              'Samantha Murray Sharan': 'Samantha Murray',
              'Aidan Mchugh': 'Aiden McHugh',
              
              'Guiomar M Zuleta de Reales': 'Guiomar De Reales',
              'Joao Lucas Reis da Silva': 'Joao Lucas Silva',
              'Bianca Andreescu': 'Bianca Vanessa Andreescu',
              'Greet Minnen': 'Greetje Minnen',
              'Santiago Rodriguez Taverna': 'Santiago FA Rodriguez Taverna',
              "Jose Fermin": "José Fermín",
            }
            for old_str, new_str in renaming.items():
              subcategoryName = subcategoryName.replace(old_str, new_str).strip()
              title = title.replace(old_str, new_str).strip()
            betInfo = {
                  'Category': categoryName, 'Matchup': matchupName,
                  'Participant': participant, 'Type': subcategoryName,
                  'Title': title,
            }
            for k,v in values.items():
              if len(list(v)) == 1:
                v = v[0]
              betInfo[k] = v
            self.matchups[matchupName]['Bets'].append(betInfo)

  def includeBet(self, label):
      if "Alternate" in label or 'No Action)' in label:
        return False
      
      for f in ["Moneyline", "Total Rounds"]:
        if f in label:
          return True
    
      return False
      
  def setBetFilters(self):
    self.betCategories = {
      "NHL": ['Goalscorer', 'Player Props', 'Shots on Goal', 'Game Lines', 'Team Totals', 'Goalie Props'],
      "NBA": ['Player Combos', 'Player Defense', 'Game Lines', 'Player Assists','Team Props', 'Player Points', 'Player Rebounds','Player Threes','Halves','Quarters'],
      "NFL": ['TD Scorers', 'Team Props', 'Receiving Props', 'Rushing Props', 'D/ST Props', 'Game Lines', 'Passing Props'],
      "NCAAB":["Game Lines", "Halves","Team Props"],
      "MMA": ['Fight Lines'],
      "EPL":["Game Lines", "Goalscorer Props", "Shots/Assists Props"],
      "ATP":["Match Lines","Sets","Player Props"],
      "WTA":["Match Lines","Sets","Player Props"],
      "MLB":["Game Lines", "Team Props", "Batter Props", "Pitcher Props","Game Props"],
     }
    self.betSubcategories = {
      "NFL": ["Game", "Alternate Spread", "Alternate Total", "TD Scorer", "Rush TDs", "Rec TDs", "2+ TDs",
        "3+ TDs", "Pass TDs", "Pass Yards", "X+ Pass Yards", "Alt Pass Yds", "Pass + Rush Yds", "Pass Attempts",
        "Pass Completions", "Interceptions", "Longest Completion", "Fantasy Points", "Receiving Yards", 
        "X+ Receiving Yards", "Alt Rec Yards", "Receptions", "Longest Reception", "Most Receiving Yards",
        "Rush Yards", "X+ Rush Yards", "Alt Rush Yds", "Rush Attempts", "Rush + Rec Yards", "Alt Rush + Rec Yds",
        "Race to X Rush Yds", "Longest Rush", "Sacks", "Solo Tackles", "Assists", "Tackles + Ast",
        "FG Made", "Kicking Pts", "PAT Made", "Team Totals", "Team Totals - Listed Half",
        "Team Totals - Listed Quarter","Defense Props"],
      "NBA": ["Game","Alternate Spread","Alternate Total","Points","X+ Points","Alt Points",
              "Points - 1st Quarter","Threes","X+ Threes","Pts + Reb + Ast",
              "Pts + Reb","Pts + Ast","Ast + Reb","Triple-Double","Double-Double",
              "ALT PTS+AST","ALT PTS+REB+AST","Alt Pts+Reb", "Rebounds",
              "X+ Rebounds","Alt Rebounds","Rebounds - 1st Quarter",
              "Assists", "X+ Assists","Alt Assists", "Assists - 1st Quarter",
              "Steals","Alt Steals","Blocks", "Alt Blocks","Steals + Blocks",
              "Turnovers", "Team Totals","Alt Team Totals", "1st Half",
              "Team Totals - 1st Half", "Team Totals - 2nd Half", "1st Quarter", 
              "2nd Quarter", "3rd Quarter","4th Quarter", "Team Totals - Quarters"],
      "NCAAB": ["Game", "Alternate Spread", "Alternate Total", "1st Half", "Team Totals - 1st Half", "Team Totals"],
      "EPL":["Moneyline (Regular Time)", "Draw No Bet (Regular Time)", 
             "Total Goals (Regular Time)", "Spread (Regular Time)", "Goalscorer",
             "Goalscorer Premier","To Score or Give Assist",
             "To Score Outside the Box", "To Score a Header",
             "Player Shots on Target", "Player Shots", "Player Assists"],
      "MMA": ['Fight Lines'],
      "ATP": ["Moneyline", "Total Games", "Games Spread", "Moneyline - 1st Set",
              "Total Sets", "Player Games Won","Player to Win a Set"],
      "WTA": ["Moneyline", "Total Games", "Games Spread", "Moneyline - 1st Set",
              "Total Sets", "Player Games Won","Player to Win a Set"]
    }
  
  def setMaxEvents(self):
    self.maxEvents = {
      "NHL": 15,
      "NBA": 15,
      "NFL": 16,
      "EPL": 10,
      "MMA": 15,
      "MLB": 15,
      "NCAAB": 60,
    }
  
  def titleRenamer(self, title):
    renameDict = {
      "Moneyline": "MoneyLine",
      ": Team Total Points": " Team Total",
      ": Team Total Goals": " Team Total",
      ": Team Total Runs": " Team Total",
      "Puck Line":"Spread",
      "Run Line": "Spread",
      "  Game Total":" Game Total", 
      "Total Rounds": " Game Total",
      ": Player Total Games Won": " Team Total (Games)",
      "Spread Games": "Spread (Games)",
      "Sets Spread": "Spread (Sets)",
      "Total Sets": " Total (Sets)",
      'Moneyline - 1st Set': '1st Set MoneyLine',
      ' 1st Set': ' 1st Set MoneyLine',
      "Strikeouts Thrown": "Total Strikeouts",
      "Outs": "Pitching Outs",
      "Earned Runs Allowed": "Earned Runs",
    }
    for old_str, new_str in renameDict.items():
      title = title.replace(old_str, new_str).strip()
    
    title = self.teamAbbrevExtender(title)
    return title
  
  def teamAbbrevExtender(self, title):
    team_abbreviations = {
      "NBA": {
        "ATL": "Atlanta", "BKN": "Brooklyn", "BOS": "Boston", "CHA": "Charlotte", 
        "CHI": "Chicago", "CLE": "Cleveland", "DAL": "Dallas", "DEN": "Denver",
        "DET": "Detroit", "GS": "Golden State", "HOU": "Houston", "IND": "Indiana",
        "LA": "Los Angeles", "MEM": "Memphis", "MIA": "Miami", "MIL": "Milwaukee",
        "MIN": "Minnesota", "NO": "New Orleans", "NY": "New York", 
        "OKC": "Oklahoma City", "ORL": "Orlando", "PHI": "Philadelphia", 
        "PHO": "Phoenix", "POR": "Portland", "SAC": "Sacramento", 
        "SA": "San Antonio", "TOR": "Toronto","UTA": "Utah", "WAS": "Washington"},
      "NFL": {
        'ARI': 'Arizona', 'ATL': 'Atlanta', 'BAL': 'Baltimore', 'BUF': 'Buffalo',
        'CAR': 'Carolina','CHI': 'Chicago','CIN': 'Cincinnati','CLE': 'Cleveland',
        'DAL': 'Dallas', 'DEN': 'Denver', 'DET': 'Detroit', 'GB': 'Green Bay',
        'HOU': 'Houston', 'IND': 'Indianapolis', 'JAX': 'Jacksonville', 
        'KC': 'Kansas City', 'LAC': 'Los Angeles', 'LAR': 'Los Angeles', 
        'LV': 'Las Vegas', 'MIA': 'Miami', 'MIN': 'Minnesota', 
        'NE': 'New England', 'NO': 'New Orleans', 'NY': 'New York', 
        'PHI': 'Philadelphia', 'PIT': 'Pittsburgh', 'SEA': 'Seattle', 
        'SF': 'San Francisco', 'TB': 'Tampa Bay', 'TEN': 'Tennessee', 
        'WAS': 'Washington'},
      "NHL": {
        'ANA': 'Anaheim', 'ARI': 'Arizona', 'BOS': 'Boston', 'BUF': 'Buffalo',
        'CGY': 'Calgary', 'CAR': 'Carolina', 'CHI': 'Chicago', 'COL': 'Colorado',
        'CBJ': 'Columbus', 'DAL': 'Dallas', 'DET': 'Detroit', 'EDM': 'Edmonton',
        'FLA': 'Florida', 'LA': 'Los Angeles', 'MIN': 'Minnesota', 'MTL': 'Montreal',
        'NSH': 'Nashville', 'NJ': 'New Jersey', 'NY': 'New York', 'OTT': 'Ottawa', 
        'PHI': 'Philadelphia', 'PIT': 'Pittsburgh', 'SJ': 'San Jose',
        'STL': 'St. Louis', 'SEA': 'Seattle', 'TB': 'Tampa Bay', 
        'TOR': 'Toronto', 'VAN': 'Vancouver', 'VGK': 'Vegas', 'WPG': 'Winnipeg', 
        'WAS': 'Washington'},
      "MLB": { 
        "LA": "Los Angeles", "BAL": "Baltimore", "STL": "St. Louis", 
        "NY": "New York", "HOU": "Houston", "WAS": "Washington",
        "CIN": "Cincinnati", "TOR": "Toronto", "TB": "Tampa Bay", "PIT": "Pittsburgh", 
        "MIA": "Miami", "MIN": "Minnesota", "KC": "Kansas City", "DET": "Detroit",
        "CHI": "Chicago", "SF": "San Francisco", "SD": "San Diego", "CHI": "Chicago",
        "TEX": "Texas", "CLE": "Cleveland", "OAK": "Oakland", "COL": "Colorado",
        "ARI": "Arizona", "BOS": "Boston", "SEA": "Seattle", "MIL": "Milwaukee",
        "NY": "New York", "ATL": "Atlanta", "PHI": "Philadelphia"
      }
    }
    
    if self.sport in team_abbreviations:
      patterns = {re.compile(r'\b' + re.escape(abbrev) + r'\b'): full_name for abbrev, full_name in team_abbreviations[self.sport].items()}
      for pattern, full_name in patterns.items():
        title = pattern.sub(full_name, title)
    
    return title