import requests, re, pandas as pd, json
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime
from Util.Common import cleanupName

def cleanupSlateName(slateName):
  pattern = r'\((.*?)\)'
  defaultValue = 'Main'
  return re.search(pattern, slateName).group(1).replace("vs", "@").replace(" @ ","@") if re.search(pattern, slateName) else defaultValue

def getSlates(date, sport, site):
  date = date.replace("-","/")
  url = "https://s3.amazonaws.com/json.rotogrinders.com/v2.00/"+date+"/slates/"+sport.lower()+"-master.json"
  # print(url)
  r = requests.get(url).json()
  site = "fanduel" if site == "FD" else "draftkings"
  slates = r[site]
  # dict_keys(['date', 'importId', 'name', 'games', 'start', 'type', 'salaryCap', 'slate_path', 'source', 'taggable', 'default', 'hidden'])
  slateData = {}
  for s in slates.values():
    # print(s.keys())
    if s['type'] in ['classic','showdown','single-game']:
      slateName = cleanupSlateName(s['name']).replace("JAC", "JAX")
      id = s['importId']
      start = s['start']
      slatePath = s['slate_path']
      games = {}
      for g in s['games']:
        # dict_keys(['date', 'time', 'scheduleId', 'rgScheduleId', 'teamAwayId', 'rgTeamAwayId', 'teamHomeId', 'rgTeamHomeId', 'teamAwayHashtag', 'teamHomeHashtag'])
        date = g['date']
        time = g['time']
        awayTeam = g['teamAwayHashtag'].strip().replace("JAC","JAX")
        homeTeam = g['teamHomeHashtag'].strip().replace("JAC","JAX")
        gameString = awayTeam + "@" + homeTeam
        games[gameString] = json.dumps({"Matchup":gameString, "AwayTeam": awayTeam, "HomeTeam": homeTeam, "StartTime": date})
        # print(awayTeam, homeTeam)
      if slateName not in slateData:
        slateData[slateName] = {
          "Id": id,
          "Games": games,
          "Start": start,
          "SlatePath": slatePath
        }
      else: 
        slateData[f"{slateName} {s['date']}"] = {
          "Id": id,
          "Games": games,
          "Start": start,
          "SlatePath": slatePath
        }
  return slateData

def getSlatePlayerData(games, url):
  # print(url)
  response = requests.get(url)
  data = []
  for d in response.json():
    awayTeam = d['schedule']['team_away']['hashtag'].strip().replace("JAC","JAX")
    homeTeam = d['schedule']['team_home']['hashtag'].strip().replace("JAC","JAX")
    game = awayTeam + "@" + homeTeam
    name = cleanupName(d['player']['first_name'] + " " + d['player']['last_name'])
    teamId = d['player']["team_id"]
    team = awayTeam if teamId == d['schedule']['team_away']['id'] else homeTeam
    playerData = {
      "Name": name,
      "Team": team,
      "Game": games[game],
      "Id": [p["player_id"] for p in d['schedule']['salaries']],
      "Position": d['schedule']['salaries'][0]["position"],
      "Salary": [p["salary"] for p in d['schedule']['salaries']]
    }
    playerData["Id"] = playerData["Id"][0] if len(d['schedule']['salaries']) == 1 else playerData["Id"]
    playerData["Salary"] = playerData["Salary"][0] if len(d['schedule']['salaries']) == 1 else str(playerData["Salary"])
    data.append(playerData)
  return data

#API
def getSlateNames(date, sport, site):
  slates = getSlates(date, sport, site)
  return slates.keys()

#API
def getSlate(date, sport, site, slate):
  slates = getSlates(date, sport, site)
  # assert slate in slates.keys(), print(slates.keys())
  try:
    return slates[slate]
  except:
    print(slate,"not in",slates.keys())
    main = [s for s in slates.keys() if "main" in s.lower()][0]
    return slates[main]

#API
def getSlateCSV(date, sport, site, slate):
  s = getSlate(date,sport, site, slate)
  return getSlatePlayerData(s['Games'],s['SlatePath'])

# def getSlateCSVEtr(self, sport, site, slate):
#   csvData = getSlateCSV(self, sport, site, slate)
#   return {}


# getSlateNames("2023/10/06","cfb","DK")
# getSlateCSV("2023/09/17","NFL","DK","Main")
# print(slates.keys())
# slateNames
# slates['93784']
# slateNames = [x['name'] for x in slates.values()]