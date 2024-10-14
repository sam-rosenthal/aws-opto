import pandas as pd
import json, os
import requests as req
import requests as req
import json
from pathlib import Path

from datetime import datetime, timedelta
from dateutil import parser
import pytz

EVENTGROUPS = {
  "MLB": "84240",
  "NFL": "88808",
  "NBA": "42648",
  "NHL": "42133",
  "PGA": "43759",
  "MMA": "9034",
  "CFB": "87637",
  "NCAAB": "92483"
}

def getEvents(sport):
  events = {}
  url = "https://sportsbook-us-md.draftkings.com//sites/US-MD-SB/api/v5/eventgroups//"+EVENTGROUPS[sport]+"?format=json"
  print(url) 
  dkEvents = req.get(url).json()['eventGroup']['events']
  for dkEvent in dkEvents:
    if dkEvent['eventStatus']['state'] == "NOT_STARTED":
      if 'teamName1' in dkEvent.keys() and len(dkEvent['teamName1']) > 0:
        game = dkEvent['teamName1']+"@"+dkEvent['teamName2']
        game = dkEvent['teamShortName1']+"@"+dkEvent['teamShortName2']
      else:
        game = dkEvent['name']
      startDateTime = parser.parse(dkEvent['startDate']).astimezone(pytz.timezone('US/Eastern'))
      events[game] = {
        "EventId": str(dkEvent['eventId']),
        "StartDate": startDateTime.strftime("%Y-%m-%d %H:%M:%S"),
      }
  return events

    
# def getEvent(sport, game):
#   events = getEvents(sport)
#   if game in events.keys():
#     return events[game]
#   else:
#     print(game, "is not in events list")
#     return None

# def getEventId(sport, game):
#   events = getEvents(sport)
#   if game in events.keys():
#     return events[game]['EventId'] 
#   else:
#     print(game, "is not in events list")
#     return None

# def getEvents(sport):
#   events = getEvents(sport)
#   return list(events.keys())
  
def jsonUrl(eventId):
  return "https://sportsbook-us-md.draftkings.com//sites/US-VA-SB/api/v3/event//"+eventId+"?format=json"

def getShortGameName(sport, date, eventId, game):
  response = req.get(jsonUrl(eventId))
  data = json.loads(response.content.decode('utf-8'))
  awayTeam = data['event']["teamShortName1"]
  homeTeam = data['event']["teamShortName2"]
  return awayTeam+"@"+homeTeam  


def getOdds(eventId):
  response = req.get(jsonUrl(str(eventId)))
  data = json.loads(response.content.decode('utf-8'))
  state = data['event']['eventStatus']['state']
  if state == "NOT_STARTED":
    timestamp = datetime.now().astimezone(pytz.timezone('US/Eastern')).strftime('%Y-%m-%d %H:%M:%S')
    content = {
      'Timestamp': timestamp,
      'Data': data
    }
    return content

def getPropsList(sport, jsonData):
  propsList = []
  betCategories= {
    "NHL": ['Goalscorer', 'Player Props', 'Shots on Goal', 'Game Lines', 'Team Totals', 'Goalie Props'],
    "NBA": ['Player Combos', 'Player Defense', 'Game Lines', 'Player Assists','Team Props', 'Player Points', 'Player Rebounds','Player Threes'],
    "NFL": ['TD Scorers', 'Team Props', 'Receiving Props', 'Rushing Props', 'D/ST Props', 'Game Lines', 'Passing Props']
  }
  for d in jsonData:
    matchup = d['Data']['event']['name'].replace(" @ ","@")
    timestamp = d['Timestamp']

    for eventCategory in d['Data']['eventCategories']:
      categoryName = eventCategory['name'].strip()
      categoryId = eventCategory['categoryId']
      if sport in betCategories.keys() and categoryName not in betCategories[sport]:
        continue
      if categoryName == 'Popular':
        continue
      
      for component in eventCategory['componentizedOffers']:
        subcategoryName = component['subcategoryName']
        subcomponentId = component['componentId']

        for offer in component['offers'][0]:
          offerSubcategoryId = offer['offerSubcategoryId']
          if 'label' in offer.keys():
            label = offer['label'].strip().replace("  "," ").replace("Nicolas Claxton", "Nic Claxton")
          else:
            print("Invalid offer, skipping",offer)
            continue
          providerOfferId = offer['providerOfferId']
          # print(label, offerSubcategoryId)
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
                oddsFractional = outcome['oddsFractional']
                if participant not in participantOutcomes:
                  participantOutcomes[participant] = {}
                  participantOutcomes[participant]['Line'] = []
                    
                if 'line' not in outcome:
                  # print(outcome)
                  participantOutcomes[participant]['Line'] = [".5"]
                  participantOutcomes[participant]['Over Odds'] = [oddsAmerican]
                  continue
                    
                else:
                  if outcome['line'] not in list(participantOutcomes[participant]['Line']):
                    participantOutcomes[participant]['Line'].append(outcome['line']) 
                    
                  if outcomeLabel not in participantOutcomes[participant]:  
                    participantOutcomes[participant][outcomeLabel] = [oddsAmerican]
                  else: 
                    participantOutcomes[participant][outcomeLabel].append(oddsAmerican)
                
              except Exception as e:
                print(categoryName, subcategoryName, outcome, e)
                continue
          for participant, values in participantOutcomes.items(): 
            title = label if participant in label else participant + " " + label
            title = matchup + " Game Total" if subcategoryName == "Game" and title == "Total" else title
            renaming = {
              "Three Pointers Made": "3 Point FG",
              "Double-Double":"Double+Double",
              "Triple-Double":"Triple+Double",
              "Points + Assists + Rebounds":"Pts+Rebs+Asts",
              "Anytime Goalscorer": "Goals",
              "Player Shots on Goal": "Shots on Goal",
              "Shots on Goal": "Shots On Goal",
              "Anytime TD Scorer": "TD Scorer",
              "TD Scorer": "Anytime TD",
              "Interceptions Thrown": "Interceptions",
              "Passing Completions":"Completions",
              "Passing Attempts": "Pass Attempts",
              "Passing Touchdowns" : "TD Passes"
            }
            for old_str, new_str in renaming.items():
              subcategoryName = subcategoryName.replace(old_str, new_str).strip()
              title = title.replace(old_str, new_str).strip()
            rowData = {
                  'Timestamp': timestamp,
                  'Category': categoryName,
                  'Matchup': matchup,
                  'Participant': participant,
                  'Subcategory': subcategoryName,
                  'Title': title,
            }
            for k,v in values.items():
              if len(list(v)) == 1:
                v = v[0]
              rowData[k] = v
 
            propsList.append(rowData)
  return propsList

def getFlatList(propsDict):
  flatList = []
  for subcategory, labels in propsDict.items():
      for label, data in labels.items():
          flatData = {
              'SubcategoryName': subcategory,
              'Label': label,
              **data
          }
          flatList.append(flatData)
  return flatList
# def getOdds(sport,date,eventId,game):
#   response = req.get(jsonUrl(eventId))
#   data = json.loads(response.content.decode('utf-8'))
#   state = data['event']['eventStatus']['state']
#   if state == "NOT_STARTED":
#     timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#     content = {
#       'Timestamp': timestamp,
#       'Data': data
#     }
#     return content
  
      
# def saveOdds(sport,date,eventId,game):
#   response = req.get(jsonUrl(eventId))
#   data = json.loads(response.content.decode('utf-8'))
#   state = data['event']['eventStatus']['state']
#   if state == "NOT_STARTED":
#     fileDir = os.path.join('C:\\Users\\Sam\\Documents\\DFS\\ETR\\Data\\DKOddsScraping', sport, date)
#     os.makedirs(fileDir, exist_ok=True)
#     timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#     content = {
#       'timestamp': timestamp,
#       'data': data
#     }
#     # Create an empty list if the file doesn't exist
#     filePath = os.path.join(fileDir, f'{game}.json')

#     if not os.path.exists(filePath):
#       contentList = []
#     else:
#       # Read the existing JSON file
#       with open(filePath, 'r') as f:
#         contentList = json.load(f)
    
#     # Append the new content to the list
#     contentList.append(content)
    
#     # Write the updated content list to the JSON file
#     with open(filePath, 'w') as f:
#       json.dump(contentList, f)