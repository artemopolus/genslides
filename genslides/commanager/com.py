import genslides.commanager.group as Act
import datetime
import genslides.utils.filemanager as FileManager
import genslides.utils.loader as Loader
import genslides.utils.writer as Writer
import genslides.utils.readfileman as Reader

class Commander:
    def __init__(self, path = "session"):
        self.actioner = None
        self.actioners_list : list[dict] = []
        self.session_name_curr = 'untitled'
        self.session_name_path = path
        FileManager.createFolder(self.session_name_path)
        self.session_names_list = FileManager.getClearFilenamesFromFilepaths(FileManager.getFilesPathInFolder(self.session_name_path))
        trg_name = self.session_name_curr
        idx = 0
        while( trg_name in self.session_names_list):
            trg_name = 'untitled' + str(idx)
            idx += 1
        
        self.session_name_curr = trg_name
        self.params = {}

    def clrActionerList(self):
        for act_pack in self.actioners_list:
            act_pack['act'].reset()
        self.actioners_list.clear()

    def getActionerByPath(self, path) -> Act.Actioner:
        for act in self.actioners_list:
            if act['act'].getPath() == path:
                return act['act']
        return None

    def autoloadActionerInExtTreeTasks(self, path : str):
        act = self.getActionerByPath( path )
        if act:
            man = act.getCurrentManager()
            out, out_paths = act.getCurManInExtTreeTasks()
            for name in out:
                task = man.getTaskByName(name)
                if task != None:
                    self.loadActionerInExtTreeTask(task)

    def loadActionerInExtTreeTask(self, task : Act.BaseTask):
        task.loadActionerTasks(self.getActionersList())

    def addExtTreeTaskActioner(self, task : Act.BaseTask):
        task_actioner = task.getActioner()
        if task_actioner != None:
            self.addActionerTolist(task_actioner, params={'type':'exttreetask','task': task})
            self.actioner.loadStdManagerTasks()

    def setCurrentSessionMame(self, name: str):
        self.session_name_curr = name

    def getCurrentSessionName(self):
        return self.session_name_curr
    
    def getPathToSession(self):
        return self.session_name_path

    def saveSession(self, params = {}):
        act_data = []
        for act in self.actioners_list:
            act_info = {
                'act_path': act['act'].getPath(),
                'type' : act['params']['type']
            }
            if act['params']['type'] == 'exttreetask':
                act_info['trg_task_name'] = act['params']['task'].getName()
            else:
                act_data.append(act_info)
        session_data = {
            'actioners': act_data
        }
        session_data.update(self.params)
        session_data.update(params)
        path = FileManager.addFolderToPath(self.session_name_path,[self.session_name_curr + ".json"])
        Writer.writeJsonToFile(Loader.Loader.getUniPath(path), session_data)

    def loadSession(self):
        path = FileManager.addFolderToPath(self.session_name_path,[self.session_name_curr + ".json"])
        session_data = Reader.ReadFileMan.readJson(path)
        projects_info = []
        exttreetask_info = []
        if 'actioners' in session_data:
            for act_info in session_data['actioners']:
                if act_info['type'] == 'project':
                    projects_info.append(act_info)
                elif act_info['type'] == 'exttreetask':
                    exttreetask_info.append(act_info)
        self.clrActionerList()
        for info in projects_info:
            self.loadActionerByPath(info['act_path'])

        active_act = self.actioners_list.copy()
        for info in exttreetask_info:
            name = info['trg_task_name']
            trg_tasks = []
            for act in active_act:
                act_tasks = act['act'].getTasksByName(name)
                
                trg_tasks.extend([t for t in act_tasks if t not in trg_tasks])
            for task in trg_tasks:
                self.addExtTreeTaskActioner(task)

        for act in self.actioners_list:
            act['act'].afterLoading()

        values = ['instructions','uat','workgraph','stepgraph','autoloadext']
        for v in values:
            if v in session_data:
                # if v == 'instructions':
                #     self.params[v].extend( [t for t in session_data[v]] )
                # else:
                    self.params[v] = session_data[v]
        self.saveSession()

        if 'autoloadext' in self.params:
            for act_info in self.params['autoloadext']:
                self.autoloadActionerInExtTreeTasks(act_info['path'])



    def saveManToTmp ( self, manager : Act.Manager.Manager ):
        pass

    def loadExtProject(self, filename, manager : Act.Manager.Manager) -> bool:
        pass

    def createActioner(self, eparam) -> Act.Actioner:
        dt1 = datetime.datetime.now()        
        path = eparam['exttreetask_path']
        manager = Act.Manager.Manager(Act.Manager.RequestHelper(), Act.Manager.TestRequester(), Act.Manager.GoogleApiSearcher())
        manager.onStart()
        manager.initInfo(self.loadExtProject, path = path)
        if 'retarget' in eparam:
            manager.addRenamedPair(eparam['retarget']['std'],eparam['retarget']['chg'])
        elif 'retrgs' in eparam:
            for pair in eparam['retrgs']:
                manager.addRenamedPair(pair['std'], pair['chg'])
        act = Act.Actioner(manager)
        act.setPath(path)
        self.saveManToTmp(manager)
        if 'load' in eparam and eparam['load']:
            manager.disableOutput2()
            if 'loadtype' in eparam:
                manager.loadTasksList(safe = True if eparam['loadtype' == 'safe'] else False)
            else:
                manager.loadTasksList(safe = False)
            manager.enableOutput2()
            act.loadTmpManagers()
        dt2 = datetime.datetime.now()     
        print('Actioner was created by:\t',(dt2-dt1).seconds,'second(s)')    
        return act

    def loadActionerByPath(self, man_path : str):
        actioner = self.createActioner({'exttreetask_path':man_path,'load':True})
        self.addActionerTolist(actioner)

    def addActionerTolist(self, act : Act.Actioner, params = {'type':'project'}, move2selected = True):
        found = False
        for actpack in self.actioners_list:
            if actpack['act'] == act:
                found = True
                break
        if not found:
            self.actioners_list.append({'act':act, 'params':params})
            self.saveSession()
        if move2selected:
            self.actioner = act


