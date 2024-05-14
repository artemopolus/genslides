from googleapiclient.discovery import build

import json
import pathlib
import genslides.task.base as Bt
import genslides.utils.readfileman as Rd
import genslides.utils.loader as Ld
import genslides.utils.filemanager as Fm

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

    def getInfoForSearch( task_buds : list[Bt.BaseTask]) -> dict:
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

    def openProject (path : str):
        buds_info = []
        fld_path = pathlib.Path(path)
        files = Fm.getFilesInFolder(Ld.Loader.getUniPath(fld_path))
        all_tasks = []
        for name in files:
             vals = name.split('.')
             if len(vals) == 2 and vals[1] == 'json':
                 all_tasks.append(vals[0])
        trg_path = fld_path / 'project.json'
        proj_info = Rd.ReadFileMan.readJson(Ld.Loader.getUniPath(trg_path))
        print('Read project data')
        if 'trees' in proj_info:
            for tree in proj_info['trees']:
                if 'buds' in tree:
                    for bud in tree['buds']:
                        buds_info.append(bud)
        ext_tasks = []
        if 'task_names' in proj_info:
            ext_tasks = proj_info['task_names']
        return buds_info, ext_tasks, all_tasks

    def searchByParams(params : dict):
        if 'type' in params and params['type'] == 'search':
            if params['search'] == 'tags':
                return ProjectSearcher.searchByTags(params['path'], params['tags'].split(','))
            elif params['search'] == 'manual':
                out = []
                idx = 0
                while idx < 30:
                    project_file = Ld.Loader.getFilePathFromSystemRaw()
                    print('Get manual input', project_file)
                    if project_file.name == 'project.json':
                        out_infos = []
                        proj_info = Rd.ReadFileMan.readJson(Ld.Loader.getUniPath(project_file))
                        if 'trees' in proj_info:
                            for tree in proj_info['trees']:
                                if 'buds' in tree:
                                    for bud in tree['buds']:
                                        name = bud['task']
                                        code = bud['branch']
                                        out_infos.append({"name": name, "code":code})
                        out.append({'src_path':Ld.Loader.getUniPath(project_file.parent), 'results':out_infos})
                    else:
                        break
                    idx += 1
                print('Added',len(out), 'project' if len(out) == 1 else 'projects')
                return out
        return []

    def searchByTags( manager_path : str, tags : list[str]):
        mpath = pathlib.Path(manager_path)
        projects = list(mpath.glob('project*'))
        print('Found projects:',projects)
        print('Search for tags', tags)
        projects_out = []
        for project_path in projects:
            results = ProjectSearcher.searchInFolder(project_path, tags)
            projects_out.append({'path':project_path, 'results':results})
        return projects_out
 

    def searchInFolder( path : str, tags : list[str]):
        out_infos = []
        proj_info = Rd.ReadFileMan.readJson(path)
        if 'trees' in proj_info:
            for tree in proj_info['trees']:
                if 'buds' in tree:
                    for bud in tree['buds']:
                        name = bud['task']
                        code = bud['branch']
                        if 'summary' in bud:
                            # Очень простой поиск
                            for tag in tags:
                                idx = bud['summary'].find(tag)
                                if idx != -1:
                                    out_infos.append({"name": name, "code":code})
        return out_infos

