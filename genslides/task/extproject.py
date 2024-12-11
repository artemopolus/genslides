from genslides.task.base import TaskDescription, BaseTask
from genslides.task.collect import CollectTask

# from genslides.commanager.jun import Manager
import genslides.commanager.group as Actioner

from genslides.utils.reqhelper import RequestHelper
from genslides.utils.testrequest import TestRequester
from genslides.utils.searcher import GoogleApiSearcher
import genslides.utils.loader as Loader
import genslides.utils.readfileman as Reader
import genslides.utils.searcher as Searcher
import genslides.utils.filemanager as Fm
import genslides.utils.finder as Finder

import os
import shutil
import pathlib

class ExtProjectTask(CollectTask):
    def __init__(self, task_info: TaskDescription, type="ExtProject") -> None:
        self.onStart()
        super().__init__(task_info, type)
        self.is_freeze = True

    def onStart(self):
        self.intpar = None
        self.intch = []
        self.intch_trg = None
        self.intman = None
        self.intact = None

    def afterFileLoading(self, trg_files = []):
        # print('Init external project task')
        self.intman = Actioner.Manager.Manager(RequestHelper(), TestRequester(), GoogleApiSearcher())
        res, param = self.getParamStruct('external')
        if not res:
            print('No path for ext project task')
            return
        else:
            if 'path' in param:
                path = param['path']
                path = self.findKeyParam(path)
                path = Loader.Loader.getUniPath(path)
            else:
                path = pathlib.Path(self.manager.getPath()) / 'ext' /param['project']
                path = Loader.Loader.checkManagerTag(path, self.manager.getPath(), to_par_fld=False) 
                # path = os.path.join( self.manager.getPath(), 'ext', param['project']) 

                param['path'] = path
                self.updateParam2(param)
                path = Loader.Loader.getUniPath(self.findKeyParam(path))

            if 'prompt' in param:
                self.prompt = param['prompt']
            else:
                param['prompt'] = self.prompt
                self.updateParam2(param)

            self.intman.setPath(path)
        self.intman.initInfo(self.manager.loadexttask, task = None, path = path)
        self.intact = Actioner.Actioner(self.intman)
        self.intact.setPath(path)
        self.intact.clearTmp()
        # print(10*"----------")
        # print('Load tasks from',path)
        # print(10*"----------")
        self.intman.disableOutput2()
        self.intman.loadTasksList(trg_files=trg_files)
        self.intman.enableOutput2()

        # print(self.getName(),'internal task list', [t.getName() for t in self.intman.task_list])

        self.intpar = None
        self.intch = []
        self.updateInOutExtProject()

        print(10*"----------")
        print('Execute', self.getName(),'from',self.intman.getPath())
        # print(10*"----------")

    def getActioner(self):
        if self.intman == None:
            return None
        self.intman.updateTreeArr()
        task = self.intpar
        if task != None and task not in self.intman.tree_arr:
            self.intman.tree_arr.append(task)
        return self.intact

    def updateInOutExtProject(self):
         if self.intman is None:
             return
         for task in self.intman.task_list:
            res, param = task.getParamStruct('input')
            if res and param['input']:
                self.intpar = task
                self.intpar.parent = self.parent
                self.intpar.caretaker = self
                # print('intpar=',self.intpar.getName())
                
            res, param = task.getParamStruct('output')
            if res and param['output']:
                idx = len(self.intch)
                if 'idx' in param:
                    idx = param['idx']
                self.addInternalChild(task, idx)

    def addInternalChild(self, task : BaseTask, idx : int):
        self.intch.append({'idx':idx, 'trg': task})
        if self.intch_trg == None:
            self.intch_trg = task
 
       

    def isTaskInternal(self, task :BaseTask):
        return True if task in self.intman.task_list else False

    def hasNoMsgAction(self):
        self.updateExtProjectInternal(self.prompt)
        if self.intact != None:
            self.intact.callScript('init_created')
        self.updateInOutExtProject()

    def updateExtProjectInternal(self, prompt):
        if self.intpar is not None:
            # print('Update external task')
            # print('With prompt=',prompt)
            info = TaskDescription(prompt=prompt, prompt_tag=self.intpar.getLastMsgRole(), manual=True)
            self.intman.curr_task = self.intpar
            self.intman.updateSteppedTree(info)
            # self.intman.curr_task.update(info)
            if len(self.intch):
                # res_list = self.getRawParentMsgs()
                res_list = self.intch_trg.getMsgs()
                self.setMsgList(res_list)
        self.updateParamStruct('external', 'prompt', prompt)
        self.saveJsonToFile(self.msg_list)

    def haveMsgsAction(self, msgs):
        # trg_list = self.getRawParentMsgs()
        if len(self.intch):
            trg_list = self.intch_trg.getMsgs()
            if trg_list == msgs:
                self.setMsgList(msgs)
            else:
                self.updateExtProjectInternal(self.prompt)
                self.intact.callScript('init_loaded_change')
                self.updateInOutExtProject()
    
    def checkParentsMsg(self):
        return []
    
    def updateCollectedMsgList(self, trg_list : list):
        pass

    def updateIternal(self, input : TaskDescription = None):
        print('Update internal External Task', self.getName())
        # self.haveMsgsAction(self.msg_list)
        if input:
            input.prompt_tag = self.intpar.getLastMsgRole() #quick fix, avoiding to change internal role param
            input.manual = True
            self.prompt = input.prompt
            if input.stepped:
                print('Stepped update')
                # self.intman.curr_task = self.intpar
                # self.intman.updateSteppedTree(input)
                self.updateExtProjectInternal(input.prompt)
                self.intact.callScript('update_input_step')
                self.updateInOutExtProject()
            else:
                # self.intpar.update(input)
                self.updateExtProjectInternal(input.prompt)
                self.intact.callScript('update_input_nostep')
                self.updateInOutExtProject()
        else:
            if self.intpar is not None and not self.intpar.checkParentMsgList(update=False, remove=True):
                print('Normal update', self.getName())
                info = TaskDescription(prompt=self.prompt, prompt_tag=self.intpar.getLastMsgRole(), manual=True)
                self.intpar.update(info)
                self.intact.callScript('update_noinput')
                self.updateInOutExtProject()
            else:
                return
        if len(self.intch):
            self.setMsgList(self.intch_trg.getMsgs())
        self.saveJsonToFile(self.msg_list)

    def removeProject(self):
        if self.intman is not None:
            self.intman.beforeRemove(True)
            del self.intman

    def beforeRemove(self):
        print('Delete external proj files')
        # res, param = self.getParamStruct('external')
        # if res and 'path' in param:
        #     print('Remove', param['path'])
        #     shutil.rmtree(param['path'])
        self.removeProject()
        super().beforeRemove()

    def getLastMsgAndParent(self, hide_task = True, max_symbols = -1, param = {}) -> (bool, list, BaseTask):
        if len(self.intch)==0:
            return super().getLastMsgAndParent()
        return self.intch_trg.getLastMsgAndParent()

    def getLastMsgContentRaw(self):
        return self.prompt

    def getLastMsgContent(self):
        if len(self.intch)==0:
            return self.prompt
        return self.intch_trg.getLastMsgContent()

    def getBranchCode(self, second) -> str:
        code_s = ""
        if self.intman is None:
            # print('No manager', self.getName())
            return ""
        if second in self.intman.task_list and len(self.intpar.getChilds()) > 1:
            trg1 = second
            code_s += self.manager.getShortName(trg1.getType(), trg1.getName())
        elif len(self.getChilds()) > 1:
            trg1 = self
            code_s += self.manager.getShortName(trg1.getType(), trg1.getName())
            trg1 = second
            code_s += self.manager.getShortName(trg1.getType(), trg1.getName())
        return code_s

    def afterRestoration(self):
        self.afterFileLoading()
        return super().afterRestoration()
    
    def setActiveBranch(self, task ):
        for param in self.params:
            if 'type' in param and param['type'] == 'child' and param['name'] == task.getName():
                idx = param['idx']
                for int_child in self.intch:
                    if int_child['idx'] == idx:
                        self.intch_trg = int_child['trg']
                        return

    def getExeCommands(self):
        mres, mparam = self.getParamStruct('manager', True)
        gres, gparam = self.getParamStruct('generator', True)
        if mres and gres:
            acts = mparam['info']['actions'].copy()
            for int_child in self.intch:
                found = False
                for param in self.params:
                    if 'type' in param and param['type'] == 'child' and param['name']:
                        if int_child['idx'] == param['idx']:
                            found = True
                if not found:
                    for act in acts:
                        if str(act['id']) == str(gparam['cmd_id']):
                            res, val, _ = int_child.getLastMsgAndParent()
                            if res:
                                act.update({gparam['cmd_type']:val})
                    return True, acts
        return super().getExeCommands()
 
    def stdProcessUnFreeze(self, input=None):
        res, pparam = self.getParamStruct('block')
        if res and pparam['block']:
            self.is_freeze = True
            return
        if self.parent:
            pass
        if self.is_freeze:
            to_unfreeze = False
            if self.parent and not self.parent.is_freeze:
                to_unfreeze = True
            elif not self.parent and self.is_freeze:
                to_unfreeze = True
            if to_unfreeze:
                # if len(self.by_ext_affected_list) == 0:
                    # return
                for tsk_info in self.by_ext_affected_list:
                    if not tsk_info.enabled:
                        return
                self.is_freeze = False
            else:
                pass
        else:
            for tsk_info in self.by_ext_affected_list:
                if not tsk_info.enabled:
                    print("Freeze from children")
                    self.freezeTask()
                    return
 
    def updateInternalActioners(self):
        if self.intact is None:
            self.freezeTask()
            return
        else:
            self.intact.loadTmpManagerTasks()
            self.intact.manager.disableOutput2()
            self.intact.updateAll(force_check=True)
            self.intact.manager.enableOutput2()

    def getTargetActionerPath(self)-> str:
        eres, eparam = self.getParamStruct('external')
        
        if eres and 'inexttree' in eparam and eparam['inexttree'] == 'fromact' and 'exttreetask_path' in eparam:
            str_trg_path = self.findKeyParam(eparam['exttreetask_path'])
            return Loader.Loader.getUniPath(str_trg_path)
        return ""

 
class SearcherTask(ExtProjectTask):
    def __init__(self, task_info: TaskDescription, type="Searcher") -> None:
        super().__init__(task_info, type)
        sres, sparam = self.getParamStruct('search', True)
        if not sres:
            self.setParamStruct({
                             'type':'search',
                             'search':'manual',
                             'tags':'',
                             'targets':[]
                            })
            
    def createInternalActioner(self):
        print('Create internal managers')
        sres, sparam = self.getParamStruct('search', True)
        if not sres:
            self.freezeTask()
            return
        # Создать менеджера и акционера
        spath = pathlib.Path( self.manager.getPath() )
        spath = spath / 'ext' / self.getName()
        mpath = Loader.Loader.getUniPath(spath)
        self.intman = Actioner.Manager.Manager(RequestHelper(), TestRequester(), GoogleApiSearcher())
        self.intman.initInfo(self.manager.loadexttask, task = None, path = mpath)
        self.actioner = Actioner.Actioner(self.intman)
        self.actioner.setPath(mpath)
        folder_tmp  = 'tmp'
        projects_out = []
        res_childs_idx = 0
        if len(sparam['targets']) == 0:
            sparam['path'] = self.manager.getPath()
            projects_out_tmp = Searcher.ProjectSearcher.searchByParams(sparam)
            idx = 0
            for project in projects_out_tmp:
                res, path = Fm.createUniqueDir(self.actioner.getPath(), folder_tmp, 'pr')
                if res:
                    if idx == 0:
                        trg_path = self.intman.getPath()
                    else:
                        Fm.createFolder(path)
                        trg_path = str(path)
                    project['trg_path'] = trg_path
                    results = project['results']
                    for result in results:
                        result['idx'] = res_childs_idx
                        res_childs_idx += 1
                    projects_out.append(project)
                idx +=1
            self.updateParamStruct(param_name='search', key='targets', val= projects_out)
        else:
            projects_out = sparam['targets']
        idx = 0
        copy_files = False
        if len(Fm.getFilesInFolder(self.intman.getPath())) < 2:
            copy_files = True
        for project in projects_out:
            project_path = Loader.Loader.getUniPath(project['src_path'])
            project_name = pathlib.Path(project['src_path']).stem
            results = project['results']
            path = project['trg_path']
            trg_path = Loader.Loader.getUniPath(path)
            for result in results:
                if copy_files:
                    tnames = self.manager.getRelatedTaskChains(result['name'], project_path)
                    Fm.copyFiles(project_path, trg_path,[t + '.json' for t in tnames])

            if idx == 0:
                self.intman.disableOutput2()
                self.intman.loadTasksList()
                self.intman.enableOutput2()
                manager = self.intman
            else:
                manager = self.actioner.addTmpManager(trg_path)
                manager.setName(project_name)
            for result in results:
                task = manager.getTaskByName(result['name'])
                internal_child = {'idx':result['idx'], 'trg': task, 'root':task.getRootParent(), 'manager': manager}
                self.intch.append(internal_child)
                if self.intch_trg == None:
                    self.intch_trg = task

            idx += 1


 
    def afterFileLoading(self, trg_files=[]):
        self.createInternalActioner()
        # return super().afterFileLoading(trg_files)
    
    def setActiveBranch(self, task ):
        for param in self.params:
            if 'type' in param and param['type'] == 'child' and param['name'] == task.getName():
                idx = param['idx']
                print('For task', task.getName(),':', idx)
                for int_child in self.intch:
                    if int_child['idx'] == idx:
                        self.intpar = int_child['root']
                        self.intch_trg = int_child['trg']
                        self.actioner.setManager(int_child['manager'])
                        self.intpar = self.parent
                        return

    def updateInOutExtProject(self):
        pass

    def updateIternal(self, input: TaskDescription = None):
        if self.actioner == None:
            self.createInternalActioner()



class InExtTreeTask(ExtProjectTask):
    def __init__(self, task_info: TaskDescription, type="InExtTree") -> None:
        super().__init__(task_info, type)

    def getInExtTreeFolderPath(self):
        eres, eparam = self.getParamStruct('external')
        if eres:
            return Loader.Loader.getUniPath(Finder.findByKey(eparam['exttreetask_path'], self.manager, self, self.manager.helper))
        return ""
        

    def afterFileLoading(self, trg_files=[]):
        # print('After file loading', self.getName())
        eres, eparam = self.getParamStruct('external')
        # if 'inexttree' in eparam  and eparam['inexttree'] != 'None':
        #     return
        self.intman = Actioner.Manager.Manager(RequestHelper(), TestRequester(), GoogleApiSearcher())
        if not eres:
            print('No params for ext project task')
            return
        if eparam['retarget']['chg'] == 'Self':
            eparam['retarget']['chg'] = self.getName()
            exttrgtask = self
        elif eparam['retarget']['chg'] == self.getName():
            exttrgtask = self
        else:
            # print(eparam['retarget']['chg'])
            exttrgtask = self.manager.getTaskByName(eparam['retarget']['chg'])

        if eparam['name'] == '':
            fld_name = self.getName()
        else:
            fld_name = eparam['name']
        if 'exttreetask_path' in eparam:
            trg_path = Loader.Loader.getUniPath(Finder.findByKey(eparam['exttreetask_path'], self.manager, self, self.manager.helper))
        else:
            trg_path = Fm.addFolderToPath(self.manager.getPath(),['ext', fld_name])
            if 'project_path' in eparam:
                src_path = self.findKeyParam(eparam['project_path'])
                src_path = Loader.Loader.getUniPath(src_path)
                if eparam['copy'] == 'Copy':
                    if len(Fm.getFilesInFolder(trg_path)) < 2:
                        Fm.copyDirToDir(src_path=Loader.Loader.getUniPath(src_path), trg_path=Loader.Loader.getUniPath(trg_path))
                else:
                    trg_path = src_path
        self.intman.setPath(trg_path)
        self.intman.initInfo(self.manager.loadexttask, task = None, path = trg_path, params={'task_names':[exttrgtask.getName()]})
        # print('ExtTargetTask=',exttrgtask.getName())
        self.intman.addTask(exttrgtask)
        self.intman.addRenamedPair(eparam['retarget']['std'],eparam['retarget']['chg'])

        self.intact = Actioner.Actioner(self.intman)
        self.intact.setPath(trg_path)
        self.intact.clearTmp()
        # self.intman.disableOutput2()
        # self.intman.loadTasksListFileBased()
        # self.intman.enableOutput2()

        self.intpar = exttrgtask

        self.setMsgList(self.getParent().getMsgList())

        if 'exttreetask_path' not in eparam:
            eparam['exttreetask_path'] = Loader.Loader.checkManagerTag(trg_path, self.manager.getPath(), False) 

        self.setParamStruct(eparam)
        # self.intman.saveInfo()
        self.saveAllParams()

    def reset(self):
        self.onStart()
        self.afterFileLoading()
        self.intact.loadStdManagerTasks()

    def checkGetContentAndParent(self) -> list[bool, list, BaseTask]:
        return False, [], self.parent
    
    def getLastMsgAndParent(self, hide_task = True, max_symbols = -1, param = {}):
        return False, [], self.parent
    
    def onEmptyMsgListAction(self):
        pass
    
    def onExistedMsgListAction(self, msg_list_from_file):
        pass
    
    def getBranchCode(self, second) -> str:
        code_s = ""
        if len(self.getChilds()) > 1:
            trg1 = self
            code_s += self.manager.getShortName(trg1.getType(), trg1.getName())
            trg1 = second
            code_s += self.manager.getShortName(trg1.getType(), trg1.getName())
        return code_s

    def updateIternal(self, input : TaskDescription = None):
        if self.intpar is None:
            return
        print(f"Update internal {self.getName()} task with {self.intpar.getName()} task")
        save_queue = self.intpar.getQueue()
        if not self.checkParentMsgList(remove=False, update=True):
            print("Update: parent msgs is different")
            self.intact.loadTmpManagerTasks()
            self.intact.manager.disableOutput2()
            self.intact.updateAll(force_check=True)
            self.intact.manager.enableOutput2()
        elif self.intact.manager.getFrozenTasksCount():
            self.intact.loadTmpManagerTasks()
            print(f"Frozen tasks:{self.intact.manager.getFrozenTasksCount()}")
            self.intact.manager.disableOutput2()
            self.intact.updateAll(force_check=True)
            self.intact.manager.enableOutput2()
        else:
            print(f"Do not update {self.getName()}")
        # print('Queue status')
        # print(save_queue)
        # print(self.intpar.queue)
        self.intpar.setQueueRaw(save_queue)

    def removeProject(self):
        eres, eparam = self.getParamStruct('external')
        exttrgtask = self.manager.getTaskByName(eparam['retarget']['chg'])
        trgs = self.intact.std_manager.task_list
        for man in self.intact.tmp_managers:
            trgs.extend(man.task_list)
        if self in trgs:
            trgs.remove(self)
        if exttrgtask in trgs:
            trgs.remove(exttrgtask)
        for task in trgs:
            task.beforeRemove()
        trg_path = Fm.addFolderToPath(self.manager.getPath(),['ext', self.getName()])
        Fm.deleteFolder(trg_path)
        del self.intact

    def setManager(self, manager):
        eres, eparam = self.getParamStruct('external')
        project_path = ''
        exttreetask_path = ''
        if 'project_path' in eparam:
            project_path = Loader.Loader.getUniPath(self.findKeyParam(eparam['project_path']))
        if 'exttreetask_path' in eparam:
            exttreetask_path = Loader.Loader.getUniPath(self.findKeyParam(eparam['exttreetask_path']))
        super().setManager(manager)
        if 'project_path' in eparam:
            eparam['project_path'] = Loader.Loader.convertFilePathToTag(project_path, manager.getPath())
        trg_path = Fm.addFolderToPath(self.manager.getPath(),['ext', self.getName()])
        trg_path = Loader.Loader.getUniPath(trg_path)
        if 'exttreetask_path' in eparam and not Loader.Loader.comparePath(trg_path, exttreetask_path):
            eparam['exttreetask_path'] = Loader.Loader.convertFilePathToTag(trg_path, manager.getPath())
            Fm.copyDirToDir(src_path=Loader.Loader.getUniPath(exttreetask_path), trg_path=Loader.Loader.getUniPath(trg_path))
            Fm.deleteFolder(exttreetask_path)

        print('Result param:',eparam)
        self.setParamStruct(eparam)

    def loadActionerTasks(self, actioners: list):
        task_actioner = self.getActioner()
        if task_actioner == None:
            print(f"Error: Task {self.getName()} without actioner")
            return
        if self.intman and self.intman.is_loaded:
            print(f"Task {self.getName()} already loaded")
        else:
            task_actioner.loadStdManagerTasks()
        task_actioner.autoUpdateExtTreeTaskActs(actioners)
        # print('Switch on actioner of', self.getName())
        # print('Path:', task_actioner.getPath())
        # print('Man:', task_actioner.manager.getName())
        return None
    
    def isExternalProjectTask(self):
        return True
    
    def drawAsRootTaskSymbol(self):
        return True
    

 
class JumperTreeTask(InExtTreeTask):
    def __init__(self, task_info: TaskDescription, type="JumperTree") -> None:
        super().__init__(task_info, type)

    def afterFileLoading(self, trg_files=[]):
        # print('After file loading', self.getName())
        eres, eparam = self.getParamStruct('external')
        if 'inexttree' in eparam  and eparam['inexttree'] != 'None':
            return
        self.intman = Actioner.Manager.Manager(RequestHelper(), TestRequester(), GoogleApiSearcher())
        if not eres:
            print('No params for ext project task')
            return


        if eparam['name'] == '':
            fld_name = self.getName()
        else:
            fld_name = eparam['name']
        if 'exttreetask_path' in eparam:
            trg_path = Loader.Loader.getUniPath(Finder.findByKey2(eparam['exttreetask_path'], self.manager, self, self.manager.helper))
        else:
            trg_path = Fm.addFolderToPath(self.manager.getPath(),['ext', fld_name])
            if 'project_path' in eparam:
                src_path = self.findKeyParam(eparam['project_path'])
                src_path = Loader.Loader.getUniPath(src_path)
                if eparam['copy'] == 'Copy':
                    if len(Fm.getFilesInFolder(trg_path)) < 2:
                        Fm.copyDirToDir(src_path=Loader.Loader.getUniPath(src_path), trg_path=Loader.Loader.getUniPath(trg_path))
                else:
                    trg_path = src_path
        self.intman.setPath(trg_path)
        self.intman.initInfo(self.manager.loadexttask, task = None, path = trg_path, params={'task_names':[]})

        self.intact = Actioner.Actioner(self.intman)
        self.intact.setPath(trg_path)
        self.intact.clearTmp()

        self.setMsgList(self.getParent().getMsgList())

        if 'exttreetask_path' not in eparam:
            eparam['exttreetask_path'] = Loader.Loader.checkManagerTag(trg_path, self.manager.getPath(), False) 

        self.setParamStruct(eparam)
        self.saveAllParams()

    def setParentInternal(self, parent):
        # print("Set parent", self.getName())
        if parent != None:
            eres, eparam = self.getParamStruct('external')
            task_actioner = self.getActioner()
            if eres and task_actioner:
                jumper = task_actioner.manager.getTaskByName(eparam['jumper'])
                if jumper and jumper.checkType('ExternalInput'):
                    # print('Change parent', parent.getName())
                    jumper.setParent(parent)

        return super().setParentInternal(parent)


    def loadActionerTasks(self, actioners: list):
        eres, eparam = self.getParamStruct('external')
        if not eres:
            return None
        if 'inexttree' not in eparam:
            return None
        if eparam['inexttree'] == 'None':
            if self.intact != None:
                print(f"Task {self.getName()} already loaded")
                return
            
            task_actioner = self.getActioner()
            if self.intpar == None:
                jumper = task_actioner.manager.getTaskByName(eparam['jumper'])
                if jumper.checkType('ExternalInput'):
                    jumper.setParent(self.getParent())
                    task_actioner.loadStdManagerTasks()
                    task_actioner.autoUpdateExtTreeTaskActs(actioners)
                    print('Switch on actioner of', self.getName())
                    print('Path:', task_actioner.getPath())
                    print('Man:', task_actioner.manager.getName())
        elif eparam['inexttree'] == 'fromact' and 'exttreetask_path' in eparam:
            # str_trg_path, task, cnt = Finder.findByKey2(eparam['exttreetask_path'], self.manager, self)
            str_trg_path = self.findKeyParam(eparam['exttreetask_path'])
            trg_path = Loader.Loader.getUniPath(str_trg_path)
            print("Try to find", trg_path)
            for actioner in actioners:
                # print("Check",actioner.getPath())
                if actioner.getPath() == trg_path:
                    man = actioner.std_manager
                    jumper = man.getTaskByName(eparam['jumper'])
                    if jumper and jumper.checkType('ExternalInput') and self.getParent() != jumper.getParent():
                        self.intact = actioner
                        self.intman = man
                        jumper.setParent(self.getParent())
                        self.intact.autoUpdateExtTreeTaskActs(actioners)
                        return None
                    else:
                        print("No task with name", eparam['jumper'], "with path", trg_path)
            print("No actioners for", trg_path)
        return None
 
    def updateIternal(self, input : TaskDescription = None):
        if self.intact is None:
            print(f"No actioner for {self.getName()}")
            self.freezeTask()
            return
        elif not self.checkParentMsgList(remove=False, update=True):
            eres, eparam = self.getParamStruct('external')
            if eres and 'updt_actions' in eparam and eparam['updt_actions'] != "":
                self.intact.getJsonCmd(eparam['updt_actions'])
            else:
                self.intact.loadTmpManagerTasks()
                self.intact.manager.disableOutput2()
                if eres and 'update_count' in eparam and isinstance(eparam['update_count'], int):
                    for i in range(eparam['update_count']):
                        self.intact.updateAll(force_check=True)
                else:
                    self.intact.updateAll(force_check=True)
                self.intact.manager.enableOutput2()
        # elif self.intact.manager.getFrozenTasksCount():
        #     self.intact.loadTmpManagerTasks()
        #     print(f"Frozen tasks:{self.intact.manager.getFrozenTasksCount()}")
        #     self.intact.manager.disableOutput2()
        #     self.intact.updateAll(force_check=True)
        #     self.intact.manager.enableOutput2()
        else:
            print(f"No update for {self.getName()}")
            eres, eparam = self.getParamStruct('external')
            if eres and 'idle_actions' in eparam and eparam['idle_actions'] != "":
                self.intact.getJsonCmd(eparam['idle_actions'])
        if self.intact.getFrozenTasksCount() > 0:
            self.freezeTask()

    def removeProject(self):
        pass



class OutExtTreeTask(ExtProjectTask):
    def __init__(self, task_info: TaskDescription, type="OutExtTree") -> None:
        super().__init__(task_info, type)
    
    def afterFileLoading(self, trg_files=[]):
        if self.getParent():
            # print(f"Parent [{self.getName()}]:{self.getParent().getName()}")
            if self.getParent().checkType( 'InExtTree'):
                pass
            elif self.getParent().checkType( 'JumperTree'):
                pass
            else:
                # print(f'Parent of {self.getName()} is not InExtTree')
                return
        self.updateOutExtActMan()
        self.saveAllParams()

    def loadActionerTasks(self, actioners: list):
        if self.intact != None and self.intman != None:
            print(f"Task {self.getName()} already loaded")
            eres, eparam = self.getParamStruct('external')
            if not eres:
                return None
            if self.intch_trg == self.intman.getTaskByName(eparam['target']):
                return None
        self.updateOutExtActMan(actioners)
        return None
    
    def isExternalProjectTask(self):
        if self.getParent() == None:
            return True
        return not self.getParent().isExternalProjectTask()

    def updateOutExtActMan(self, actioners = []):
        try:
            parent = self.getParent()
            if parent and parent.isExternalProjectTask():
                # if parent.checkType("JumperTree") or parent.checkType("InExtTree"):
                    eres, eparam = self.getParamStruct('external')
                    self.intact = self.parent.intact
                    self.intman = self.parent.intman
                    self.intact.autoUpdateExtTreeTaskActs(actioners)

                    self.intch_trg = self.intman.getTaskByName(eparam['target'])
            else:
                eres, eparam = self.getParamStruct('external')
                if eres and eparam['inexttree'] == 'fromact' and 'exttreetask_path' in eparam:
                    # str_trg_path, task, cnt = Finder.findByKey2(eparam['exttreetask_path'], self.manager, self)
                    str_trg_path = self.findKeyParam(eparam['exttreetask_path'])
                    trg_path = Loader.Loader.getUniPath(str_trg_path)
                    print("Try to load by path:",trg_path)
                    for actioner in actioners:
                        if actioner.getPath() == trg_path:
                            man = actioner.std_manager
                            self.intact = actioner
                            self.intman = man
                            self.intch_trg = man.getTaskByName(eparam['target'])
                            self.intact.autoUpdateExtTreeTaskActs(actioners)
                            return

            
        except Exception as e:
            # print('Failed load man and act:', e)
            pass

    def checkGetContentAndParent(self) -> list[bool, list, BaseTask]:
        return False, [], self.intch_trg
    
    def getLastMsgAndParent(self, hide_task = True, max_symbols = -1, param = {}):
        return False, [], self.intch_trg
    
    def getPromptContentForCopyConverted(self):
        if self.intch_trg == None:
            return ""
        return self.intch_trg.getPromptContentForCopyConverted()

    def getLastMsgContent(self):
        if self.intch_trg == None:
            return ""
        return self.intch_trg.getLastMsgContent()

    def updateIternal(self, input : TaskDescription = None):
        if self.intact == None:
            self.updateOutExtActMan()
        if self.intact == None:
            print(f"No internal actioner for {self.getName()}")
            self.freezeTask()
            return
        if self.intch_trg == None:
            eres, eparam = self.getParamStruct('external')
            if eres:
                self.intch_trg = self.intman.getTaskByName(eparam['target'])
        try:
            if self.intch_trg.is_freeze:
                print(f"Target for {self.getName()} is frozen")
                self.freezeTask()
                if self.isExternalProjectTask():
                    self.updateInternalActioners()
            else:
                self.stdProcessUnFreeze()
            bres, bparam = self.intch_trg.getParamStruct('bud')
            if bres:
                param = {'type':'bud','text': bparam['text'],'branch':self.getBranchCodeTag()}
                self.setParamStruct(param)
            else:
                # print('No param for summary')
                pass
 
            
        except Exception as e:
            print(f"Abort updating of {self.getName()}: {e}")
            self.freezeTask()

    def getParentForFinder(self):
        return self.intch_trg
    
    def getParentForRaw(self):
        return self.intch_trg
    
    def removeProject(self):
        pass

    def getParamStructFromExtTask(self, param_name):
        return False, self.intch_trg, None
 