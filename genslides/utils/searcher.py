from googleapiclient.discovery import build

import json


class WebSearcher:
    def __init__(self) -> None:
        pass
    def getSearchs(self, request: str):
        return []


class GoogleApiSearcher(WebSearcher):
    def __init__(self) -> None:
        self.api_key = ''
        self.cse_key = ''
        with open('config/google.json', 'r') as config:
            input = json.load(config)
            self.api_key = input['api_key']
            self.cse_key = input['cse_key']
        print('api_key=' + str(self.api_key))
        print('cse_key=' + str(self.cse_key))
        super().__init__()

    def getSearchs(self, request: str):
        print('Web search')
        resource = build("customsearch", 'v1', developerKey=self.api_key).cse()
        result = resource.list(q=request, cx=self.cse_key).execute()
        out = []
        for item in result['items']:
            print(item['title'], '='*10, item['link'])
            print(item)
            out.append(item['link'] + ' title: ' + item['title'] + ' snippet:' + item['snippet'])
        return out
