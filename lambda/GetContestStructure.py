import pandas as pd
from datetime import datetime
import sys
import requests
import re 
import json
import pandas as pd
from Util.DKDFSScraping import getContestStructureCSV

def handler(event, context):
    print('request: {}'.format(json.dumps(event)))
    data = json.loads(event['body'])
    contestId = data["contestId"]    
    output = getContestStructureCSV(contestId)
    # print(output)
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'text/plain',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST'
        },
        'body': output
    }
