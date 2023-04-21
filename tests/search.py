from googleapiclient.discovery import build
import pprint

import json

api_key = ''
cse_key = ''

with open('../config/google.json', 'r') as config:
    input = json.load(config)
    api_key = input['api_key']
    cse_key = input['cse_key']


resource = build("customsearch", 'v1', developerKey=api_key).cse()
result = resource.list(q='simplified python', cx=cse_key).execute()

# pprint.pprint(result)

for item in result['items']:
    print(item['title'], '='*10, item['link'])
