import requests, csv, json
def getMatchupName(matchup):
  split = matchup.split("@")
  awayTeam = split[0]
  homeTeam = split[1]
  teamMap = {
    "ARI":"cardinals",
    "ATL":"falcons",
    "CAR":"panthers",
    "CHI":"bears",
    "CIN":"bengals",
    "CLE":"browns",
    "BAL":"ravens",
    "BUF":"bills",
    "DAL":"cowboys",
    "DEN":"broncos",
    "DET":"lions",
    "GB":"packers",
    "HOU":"texans",
    "IND":"colts",
    "JAX":"jaguars",
    "KC":"chiefs",
    "LAC":"chargers",
    "LA":"rams",
    "LAR":"rams",
    "LV":"raiders",
    "MIA":"dolphins",
    "MIN":"vikings",
    "NE":"patriots",
    "NO":"saints",
    "NYJ":"jets",
    "NYG":"giants",
    "PHI":"eagles",
    "PIT":"steelers",
    "SF":"49ers",
    "SEA":"seahawks",
    "WAS":"commanders",
    "TB":"buccaneers",
    "TEN":"titans"
  }
  return teamMap[awayTeam]+"-at-"+teamMap[homeTeam]

def getOpponent(matchup, team):
  split = matchup.split("@")
  awayTeam = split[0]
  homeTeam = split[1]
  return awayTeam if team == homeTeam else homeTeam

def cleanupName(name):
  return name.lower().replace(".","").replace("'","").replace(" jr","").replace(" iii","").replace(" iv","").replace(" ii","").replace("-"," ").strip()

def getFullTeamName(teamName):
    # Dictionary to map team names to full names
  nflTeams = {
    'bills': 'Buffalo Bills',
    'dolphins': 'Miami Dolphins',
    'patriots': 'New England Patriots',
    'jets': 'New York Jets',
    'ravens': 'Baltimore Ravens',
    'bengals': 'Cincinnati Bengals',
    'browns': 'Cleveland Browns',
    'steelers': 'Pittsburgh Steelers',
    'texans': 'Houston Texans',
    'colts': 'Indianapolis Colts',
    'jaguars': 'Jacksonville Jaguars',
    'titans': 'Tennessee Titans',
    'broncos': 'Denver Broncos',
    'chiefs': 'Kansas City Chiefs',
    'raiders': 'Las Vegas Raiders',
    'chargers': 'Los Angeles Chargers',
    'cowboys': 'Dallas Cowboys',
    'giants': 'New York Giants',
    'eagles': 'Philadelphia Eagles',
    'commanders': 'Washington commanders',
    'bears': 'Chicago Bears',
    'lions': 'Detroit Lions',
    'packers': 'Green Bay Packers',
    'vikings': 'Minnesota Vikings',
    'falcons': 'Atlanta Falcons',
    'panthers': 'Carolina Panthers',
    'saints': 'New Orleans Saints',
    'buccaneers': 'Tampa Bay Buccaneers',
    'cardinals': 'Arizona Cardinals',
    'rams': 'Los Angeles Rams',
    '49ers': 'San Francisco 49ers',
    'seahawks': 'Seattle Seahawks'
  }
  return nflTeams[teamName.lower()].lower()
  
###############################################
def extractPlayerPosHelper(players, pos, playerName):
  if pos not in players:
    players[pos] = " ".join(playerName) if playerName else "LOCKED"
  else:
    if not isinstance(players[pos], list):
      players[pos] = [players[pos]]
    players[pos].append(" ".join(playerName) if playerName else "LOCKED")
  return players

# @staticmethod
def extractPlayers(lineupString, positionsOrder):
  players = {}
  words = lineupString.split()
  pos = None  # to keep track of current position
  playerName = []

  for word in words:
    if word in positionsOrder:
      if pos:
        players = extractPlayerPosHelper(players, pos, playerName)
      pos = word
      playerName = []
    else:
      playerName.append(word)
  
  # for the last player in the string
  if pos:
    players = extractPlayerPosHelper(players, pos, playerName)
      
  # In case there are positions that weren't found in the lineupString
  for position in positionsOrder:
    if position not in players:
        players[position] = "LOCKED"
  
  return players
