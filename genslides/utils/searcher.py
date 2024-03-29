from googleapiclient.discovery import build

import json
import pathlib
import genslides.task.base as btask
import genslides.utils.readfileman as reader

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
        # print('api_key=' + str(self.api_key))
        # print('cse_key=' + str(self.cse_key))
        super().__init__()

    def getSearchs(self, request: str):
        if len(request) == 0:
            return []
        if request[0] =="\"" and request[-1] == "\"":
            request = request[1:-1]
        print('Web search=', request)
        resource = build("customsearch", 'v1', developerKey=self.api_key).cse()
        result = resource.list(q=request, cx=self.cse_key).execute()
        out = []
        for item in result['items']:
            # print(item['title'], '='*10, item['link'])
            # print(item)
            # out.append(item['link'] + ' title: ' + item['title'] + ' snippet:' + item['snippet'])
            out.append(item['link'] )
        return out
    

class ProjectSearcher():
    def __init__(self) -> None:
        pass

    def getInfoForSearch( task_buds : list[btask.BaseTask]) -> dict:
        # print('Get info for buds', [t.getName() for t in task_buds])
        info_buds = []
        for task in task_buds:

            info_bud = {'task':task.getName(),'summary':'','message':'','branch':task.getBranchCodeTag()}
            bres, bparam = task.getParamStruct('bud')
            if bres:
                info_bud['summary'] = task.findKeyParam(bparam['text'])
            mres, mval, _ = task.getLastMsgAndParent()
            if mres:
                info_bud['message'] = mval
            info_buds.append(info_bud)

        return {'root':task.getName(),'summary':task.getBranchSummary(),'buds':info_buds}
    
    def saveSearchInfo( trees_info : list, target : dict ):
        target['trees'] = trees_info

    def searchInFolder( path : str, tags : list[str]):
        out_infos = []
        info = reader.ReadFileMan.readJson(path)
        if 'trees' in info:
            for tree in info['trees']:
                if 'buds' in tree:
                    for bud in tree['buds']:
                        name = bud['task']
                        code = bud['branch']
                        if 'summary' in bud:
                            # Очень простой поиск
                            for tag in tags:
                                idx = bud['summary'].find(tag)
                                if idx != -1:
                                    out_infos.append(code)
        return out_infos

