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

import os
import shutil
import pathlib

class ExtProjectTask(CollectTask):
    def __init__(self, task_info: TaskDescription, type="ExtProject") -> None:
        self.intpar = None
        self.intch = []
        self.intch_trg = None
        self.intman = None
        self.intact = None
        super().__init__(task_info, type)
        self.is_freeze = True

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
        # print('Update internal', self.getName())
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

    def getLastMsgAndParent(self) -> (bool, list, BaseTask):
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
            print('No manager', self.getName())
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

    def afterFileLoading(self, trg_files=[]):
        print('After file loading', self.getName())
        self.intman = Actioner.Manager.Manager(RequestHelper(), TestRequester(), GoogleApiSearcher())
        eres, eparam = self.getParamStruct('external')
        if not eres:
            print('No params for ext project task')
            return
        if eparam['retarget']['chg'] == 'Self':
            eparam['retarget']['chg'] = self.getName()
            exttrgtask = self
        elif eparam['retarget']['chg'] == self.getName():
            exttrgtask = self
        else:
            print(eparam['retarget']['chg'])
            exttrgtask = self.manager.getTaskByName(eparam['retarget']['chg'])

        if eparam['name'] == '':
            fld_name = self.getName()
        else:
            fld_name = eparam['name']
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
        self.intman.initInfo(self.manager.loadexttask, task = None, path = trg_path)
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

        self.saveAllParams()


    def checkGetContentAndParent(self) -> list[bool, list, BaseTask]:
        return False, [], self.parent
    
    def getLastMsgAndParent(self):
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
        if not self.checkParentMsgList(remove=False, update=True):
            self.intact.loadTmpManagerTasks()
            self.intact.manager.disableOutput2()
            self.intact.updateAll(force_check=True)
            self.intact.manager.enableOutput2()
        elif self.intact.manager.getFozenTasksCount():
            self.intact.loadTmpManagerTasks()
            print(f"Frozen tasks:{self.intact.manager.getFozenTasksCount()}")
            self.intact.manager.disableOutput2()
            self.intact.updateAll(force_check=True)
            self.intact.manager.enableOutput2()

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
        

class OutExtTreeTask(ExtProjectTask):
    def __init__(self, task_info: TaskDescription, type="OutExtTree") -> None:
        super().__init__(task_info, type)
    
    def afterFileLoading(self, trg_files=[]):
        if not self.getParent().checkType( 'InExtTree'):
            print(f'Parent of {self.getName()} is not InExtTree')
            return
        eres, eparam = self.getParamStruct('external')
        if not eres:
            print(f'No params of {self.getName()}')
            return
        
        try:
            self.intact = self.parent.intact
            self.intman = self.parent.intman

            self.intch_trg = self.intman.getTaskByName(eparam['target'])
            
        except Exception as e:
            print('Failed load man and act:', e)
        self.saveAllParams()

    def checkGetContentAndParent(self) -> list[bool, list, BaseTask]:
        return False, [], self.intch_trg
    
    def getLastMsgAndParent(self):
        return False, [], self.intch_trg
    
    def getLastMsgContent(self):
        if self.intch_trg == None:
            return ""
        return self.intch_trg.getLastMsgContent()

    def updateIternal(self, input : TaskDescription = None):
        if self.intch_trg == None:
            eres, eparam = self.getParamStruct('external')
            if eres:
                self.intch_trg = self.intman.getTaskByName(eparam['target'])
        try:
            if self.intch_trg.is_freeze:
                self.freezeTask()
            else:
                self.stdProcessUnFreeze()
            bres, bparam = self.intch_trg.getParamStruct('bud')
            if bres:
                param = {'type':'bud','text': bparam['text'],'branch':self.getBranchCodeTag()}
                self.setParamStruct(param)
            else:
                print('No param for summary')
 
            
        except:
            self.freezeTask()

    def getParentForFinder(self):
        return self.intch_trg
    
    def removeProject(self):
        pass

