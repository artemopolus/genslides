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

import genslides.utils.convert2genslidesjson as Converter
import genslides.utils.archivator as Archive

import genslides.task_tools.cmds as CommandTool
import genslides.task_tools.text as Txt

import os
import shutil
import pathlib
import datetime
import logging

logger = logging.getLogger(__name__)


class ExtProjectTask(CollectTask):
    def __init__(self, task_info: TaskDescription, type="ExtProject") -> None:
        self.onStart()
        super().__init__(task_info, type)
        self.is_freeze = True

    def onStart(self):
        self.intpar : BaseTask = None
        self.intch = []
        self.intch_trg : BaseTask = None
        self.intman : Actioner.Manager = None
        self.intact : Actioner.Actioner = None
        self.allow_child_update = False

    def canChildUpdate(self) -> bool:
        return self.allow_child_update
    
    def setChildUpdateState(self, state : bool):
        self.updateUpdationInfo(f"Allow update: {state}")
        self.allow_child_update = state

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
        logger.debug('Delete external proj files')
        # res, param = self.getParamStruct('external')
        # if res and 'path' in param:
        #     print('Remove', param['path'])
        #     shutil.rmtree(param['path'])
        self.removeProject()
        super().beforeRemove()

    def getLastMsgAndParent(self, hide_task = True, max_symbols = -1, param = {}, add_task_name = False):
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
        self.updateUpdationInfo(f"Standart unfreeze process for ext project")
        if self.checkBlock():
            self.freezeTask()
        else:
            if self.is_freeze:
                if self.parent and not self.parent.is_freeze:
                    self.unfreezeTask()
                elif not self.parent and self.is_freeze:
                    self.unfreezeTask()
        self.updateUpdationInfo(f"Freeze status: {self.is_freeze}")

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
    
    def getLastMsgAndParent(self, hide_task = True, max_symbols = -1, param = {}, add_task_name = False):
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
            logger.debug("Update: parent msgs is different")
            self.intact.loadTmpManagerTasks()
            self.intact.manager.disableOutput2()
            self.intact.updateAll(force_check=True)
            self.intact.manager.enableOutput2()
        elif self.intact.manager.getFrozenTasksCount():
            self.intact.loadTmpManagerTasks()
            logger.info("Frozen tasks:%s",self.intact.manager.getFrozenTasksCount())
            self.intact.manager.disableOutput2()
            self.intact.updateAll(force_check=True)
            self.intact.manager.enableOutput2()
        else:
            logger.info("Do not update %s",self.getName())
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
    
    def runJsonCommandByInnerActioner( self, cmds : list):
        act = self.getActioner()
        if act != None:
            result = None
            eres, eparam = self.getParamStruct('external')
            if eres:
                eparam["task_reports_after_cmd"] = ""
                eparam["filtered_cmds"] = "" 
            if isinstance( cmds , str ):
                result = act.getJsonCmd( cmds )
            elif isinstance( cmds , list ):
                cmds = act.filterJsonCommands( cmds )
                if eres:
                    eparam["filtered_cmds"] = Loader.Loader.convJsonToText( cmds )
                result = act.getJsonCustomCmd( cmds )

            if eres:
                eparam["task_reports_after_cmd"] = Loader.Loader.convJsonToText(self.manager.getTaskReports())
                self.setParamStruct( eparam )
            
            return result
        return None
    

 
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

    def updateInternalGlobalKeys(self):
        if not self.intman:
            return
        global_vars_update = {}
        for key in self.manager.getGlobalKeys():
            self.updateUpdationInfo(f"Update new key: {key}\n")
            res, value = self.manager.getGlobalValue( key )
            if res:
                global_vars_update[key] = value

        eres, eparam = self.getParamStruct('external', True)
        if eres:
            if eparam.get("replace_manager_globalvars", False):
                forcing_keys = self.findKeyParam(eparam.get("target_manager_globalvars",""))
                jres, jobj, jreport = Loader.Loader.loadJsonFromTextStr(forcing_keys)
                self.updateUpdationInfo(f"For Global Vars: {jreport}")
                if jres and isinstance(jobj, dict):
                    for k, v in jobj.items():
                        global_vars_update[k] = v
                else:
                    self.updateUpdationInfo(f"Error replacing Globals:{forcing_keys}")
        for key, value in global_vars_update.items():
            self.getActioner().getCurrentManager().appendGlobalVariables( key, value )

    def getRelatedActionersPaths(self, actpaths_list):
        if self.intact != None:
            if self.intact.getPath() not in actpaths_list:
                actpaths_list.append(self.intact.getPath())
            actpaths_list = self.intact.getRelatedActionersPaths( actpaths_list )
        return super().getRelatedActionersPaths(actpaths_list)
    
    def getLoadedActionerPath( self, actpaths_list : list[str] ):
        eres, eparam = self.getParamStruct('external')
        if eres and 'inexttree' in eparam and eparam['inexttree'] == 'fromact' and 'exttreetask_path' in eparam:
            str_trg_path = self.findKeyParam(eparam['exttreetask_path'])
            trg_path = Loader.Loader.getUniPath(str_trg_path)
            actpaths_list.append( trg_path )
        act = self.getActioner()
        if act != None:
            actpaths_list = act.getLoadedActionerPath( actpaths_list )
        return super().getLoadedActionerPath(actpaths_list)


    def reloadTaskActioner(self, actioners : list ):
        self.updateUpdationInfo("Reload actioner")
        eres, eparam = self.getParamStruct('external')
        if eres and eparam['inexttree'] == 'fromact' and 'exttreetask_path' in eparam:
            str_trg_path = self.findKeyParam(eparam['exttreetask_path'])
            trg_path = Loader.Loader.getUniPath(str_trg_path)
            self.updateUpdationInfo(f"Try to find {trg_path} ")
            for actioner in actioners:
                if actioner.getPath() == trg_path:
                    man = actioner.std_manager
                    jumper = man.getTaskByName(eparam['jumper'])
                    if jumper and jumper.checkType('ExternalInput') and self.getParent() != jumper.getParent():
                        self.intact = actioner
                        self.intman = man
                        jumper.setParent(self.getParent())
                        self.updateInternalGlobalKeys()
                        self.intact.autoUpdateExtTreeTaskActs(actioners)
                        return None
                    else:
                        jumper_name = eparam['jumper']
                        self.updateUpdationInfo(f"No task with name {jumper_name} with path { trg_path}")
            self.updateUpdationInfo(f"No actioners for {trg_path}")

    def checkCurrentActionerTaskPath(self):
        if self.getActioner() != None:
            return not self.checkActionerTaskPath( self.getActioner().getPath() )
        return True
        return super().checkCurrentActionerTaskPath()

    def checkActionerTaskPath(self, path):
        eres, eparam = self.getParamStruct('external')
        if eres and eparam['inexttree'] == 'fromact' and 'exttreetask_path' in eparam:
            target_path = Loader.Loader.getUniPath( path )
            exttree_path = Loader.Loader.getUniPath( self.findKeyParam(eparam['exttreetask_path']) )
            self.updateUpdationInfo(f"Check \n{target_path}\n ==\n{exttree_path}")
            return target_path == exttree_path
        return super().checkActionerTaskPath(path)
    
    def setActionerTaskPath(self, path):
        eres, eparam = self.getParamStruct('external')
        if eres and eparam['inexttree'] == 'fromact' and 'exttreetask_path' in eparam:
            relpath = Loader.Loader.getManRePath(path, self.manager.getPath())
            eparam['exttreetask_path'] = relpath
            self.setParamStruct(eparam)
            self.saveAllParams()
        return super().setActionerTaskPath(path)

    def loadActionerTasks(self, actioners: list):
        self.updateUpdationInfo("Load actioner task")
        eres, eparam = self.getParamStruct('external')
        if not eres:
            return None
        if 'inexttree' not in eparam:
            return None
        if self.getActioner() != None:
            str_trg_path = self.findKeyParam(eparam.get('exttreetask_path',""))
            trg_path = Loader.Loader.getUniPath(str_trg_path)
            self.updateUpdationInfo(f"Try to check {trg_path} for actioner ")
            if eparam['inexttree'] == 'fromact' and 'exttreetask_path' in eparam:
                if self.getActioner().getPath() == trg_path:
                    self.updateUpdationInfo(f"Task {self.getName()} already loaded\n")
                    self.updateInternalGlobalKeys()
                    self.getActioner().autoUpdateExtTreeTaskActs(actioners)
                    return None
            else:
                self.updateUpdationInfo(f"Task {self.getName()} already loaded\n")
                self.updateInternalGlobalKeys()
                self.getActioner().autoUpdateExtTreeTaskActs(actioners)
                return None
            self.updateUpdationInfo(f"Try to load actioner for {trg_path}")
        
        if eparam['inexttree'] == 'None':
           
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
            self.updateUpdationInfo(f"Try to find {trg_path} ")
            for actioner in actioners:
                # print("Check",actioner.getPath())
                if actioner.getPath() == trg_path:
                    man = actioner.std_manager
                    jumper = man.getTaskByName(eparam['jumper'])
                    if jumper == None:
                        jumper_name = eparam['jumper']
                        self.updateUpdationInfo(f"No task with name {jumper_name} with path { trg_path}")
                    elif jumper.checkType('ExternalInput') and self.getParent() == jumper.getParent():
                        self.updateUpdationInfo("Only update actioners")
                        self.intact = actioner
                        self.intman = man
                        self.updateInternalGlobalKeys()
                        self.intact.autoUpdateExtTreeTaskActs(actioners)
                        return None
                    elif jumper.checkType('ExternalInput') and self.getParent() != jumper.getParent():
                        self.updateUpdationInfo("Update actioner and jumper")
                        self.intact = actioner
                        self.intman = man
                        jumper.setParent(self.getParent())
                        self.updateInternalGlobalKeys()
                        self.intact.autoUpdateExtTreeTaskActs(actioners)
                        return None
            ava_paths = "\n".join( [a.getPath() for a in actioners] )
            self.updateUpdationInfo(f"No actioners for {trg_path}\n {ava_paths}")
        return None
    
    def reconnectJumperTreeExtTree(self):
        eres, eparam = self.getParamStruct('external', True)
        actioner = self.intact
        if eres and actioner:
            str_trg_path = self.findKeyParam(eparam['exttreetask_path'])
            trg_path = Loader.Loader.getUniPath(str_trg_path)
            if actioner.getPath() == trg_path:
                man = actioner.std_manager
                jumper = man.getTaskByName(eparam['jumper'])
                if jumper and jumper.checkType('ExternalInput') and self.getParent() != jumper.getParent():
                    self.updateUpdationInfo(f"Reconnect jumper")
                    jumper.setParent(self.getParent())

    def getExtTreeArchivePaths( self ):
        act = self.getActioner()
        if act != None:
            return act.getSavedArchives()
        return []


    def saveExtTreeProject(self, path):
        act = self.getActioner()
        if act != None:
            act.saveGenslidesArchiveInFolder( path )
            eres, eparam = self.getParamStruct('external', True)
            if eres:
                eparam["exttree_gsarch_path"] = path
                self.setParamStruct(eparam)

    def loadExtTreeProject( self, path):
        act = self.getActioner()
        if act != None:
            if act.loadManagerProjectFromFile( path ):
                eres, eparam = self.getParamStruct('external', True)
                if eres:
                    eparam["exttree_gsarch_path"] = path
                    self.setParamStruct(eparam)
                return True
        return False

    def runBeforeUpdateIternal(self, input = None):
        eres, eparam = self.getParamStruct('external', True)
        if eres:
            autoload_on = eparam.get("exttreetask_autoload", False)
            if autoload_on:
                autoload_result = False
                self.updateUpdationInfo("Autoload project")
                path_to_target_file = Loader.Loader.getUniPath( self.findKeyParam( eparam.get("exttreetask_file_target","") ) )
                act = self.getActioner()
                if act == None:
                    return super().runBeforeUpdateIternal(input)
                if Loader.Loader.checkIsFile(path_to_target_file):
                    path_to_current_file = eparam.get("exttreetask_file_current","")
                    path_to_gsjs = Converter.getConvertedGenslidesJsonName( path_to_target_file )
                    if Converter.isValidGenslidesArchiveFilePath( path_to_target_file):
                        path_to_current_archive = path_to_target_file
                    else:
                        path_to_current_archive = Converter.getGenslidesArchiveFilePathBasedOnJson( path_to_gsjs )
                    self.updateUpdationInfo(f"Target file:{path_to_target_file}")
                    self.updateUpdationInfo(f"Current file:{path_to_current_file}")
                    self.updateUpdationInfo(f"Json data:{path_to_gsjs}")
                    self.updateUpdationInfo(f"Archive:{path_to_current_archive}")
                    if path_to_target_file == path_to_current_file:
                        self.updateUpdationInfo(f"Target file is already loaded:{path_to_target_file}")
                        autoload_result = True
                    # if path_to_target_file == path_to_current_file and Converter.isValidGenslidesArchiveFilePath( path_to_target_file ):
                    #     self.updateUpdationInfo(f"Target file == valid archive:{path_to_target_file}")
                    #     autoload_result = True
                    elif path_to_target_file != path_to_current_file and Fm.checkExistPath(  path_to_current_archive ):
                    # Converter.isValidGenslidesArchiveFilePath( path_to_target_file ):
                        self.updateUpdationInfo(f"Save previous file: {path_to_current_file}\nTarget:{path_to_current_archive}")
                        act.saveGenslidesArchiveByPath( path_to_current_archive)
                        autoload_result = act.loadManagerProjectFromFile( path_to_current_archive )
                        self.updateUpdationInfo(f"Load archive ({path_to_target_file}) result = {autoload_result}")
                        eparam["exttreetask_file_current"] = path_to_target_file
                    # elif path_to_target_file == path_to_current_file and Converter.checkExistOfGenslidesJsonFile( path_to_target_file ) and Converter.checkExistOfGenslidesArchiveFile( path_to_target_file ):
                    #     self.updateUpdationInfo(f"Target file == current file:{path_to_target_file}: json and archive exist")
                    #     autoload_result = True
                    else:
                        self.updateUpdationInfo(f"Load project by path: {path_to_target_file}")

                        if Converter.checkExtensionOfFile( path_to_target_file ):
                            if not Converter.checkExistOfGenslidesArchiveFile( path_to_target_file ):
                                if not Converter.checkExistOfGenslidesJsonFile( path_to_target_file ):
                                    conv_param = eparam.get("exttreetask_gsjson_param","")
                                    jres, jobj, jreport = Loader.Loader.loadJsonFromTextStr( conv_param )
                                    if jres:
                                        conv_output = Converter.convertFileToGenslidesJsonWithParameters(path_to_target_file, jobj)
                                    else:
                                        conv_output = Converter.convertFileToGenslidesJson( path_to_target_file)
                                    if isinstance(conv_output, dict):
                                        self.updateUpdationInfo(conv_output.get("report",""))
                                path_to_template = Loader.Loader.getUniPath( self.findKeyParam( eparam.get("exttreetask_template","") ) )
                                if Archive.Archivator.checkPathToArchive( path_to_template ):
                                    self.updateUpdationInfo(f"Reproduce template ({path_to_template}) with parameters ({path_to_gsjs}) ")
                                    path_to_craeted_gs_archive = act.convertJsonFileToTemplateTreeTasks( path_to_template, path_to_gsjs )
                                    eparam["exttree_gsarch_path"] = path_to_craeted_gs_archive
                                    act.syncRelatedActionersWithFolder()
                                    autoload_result = True
                                else:
                                    self.updateUpdationInfo(f"No valid archive by path:{path_to_template}")
                            else:
                                path_to_archive = Converter.getGenslidesArchiveFilePath( path_to_target_file )
                                self.updateUpdationInfo(f"Load archive from {path_to_archive}")
                                autoload_result = act.loadManagerProjectFromFile( path_to_archive )
                                if autoload_result:
                                    act.syncRelatedActionersWithFolder()
                        else:
                            self.updateUpdationInfo(f"Extension for file ({path_to_target_file}):unknown")

                        cres, cmds = Loader.Loader.loadJsonFromText( self.findKeyParam( eparam.get("autoload_actions","")))
                        if cres and autoload_result:
                            results = self.runJsonCommandByInnerActioner( cmds )
                            self.updateUpdationInfo(f"Autoload_cmds:{results}")

                        eparam["exttreetask_file_current"] = path_to_target_file
                else:
                    self.updateUpdationInfo(f"File {path_to_target_file} is not exist")
                    if Converter.isValidGenslidesArchiveFilePathToCreate( path_to_target_file ):
                        path_to_template = Loader.Loader.getUniPath( self.findKeyParam( eparam.get("exttreetask_template","") ) )
                        self.updateUpdationInfo(f"Load archive from {path_to_template}")
                        autoload_result = act.loadManagerProjectFromFile( path_to_template )
                        if autoload_result:
                            act.saveGenslidesArchiveByPath( path_to_target_file)
                            act.syncRelatedActionersWithFolder()
                            self.updateUpdationInfo(f"Create project and save in {path_to_target_file}")
                            eparam["exttreetask_file_current"] = path_to_target_file
                        else:
                            self.updateUpdationInfo(f"Error on loading tasks")
                    else:
                        self.updateUpdationInfo(f"{path_to_target_file} is not valid archive name")
                 
                eparam["exttreetask_autoload_result"] = autoload_result
                self.setParamStruct(eparam)
        return super().runBeforeUpdateIternal(input)
    
    def updateDescription( self ):
        act = self.getActioner()
        eres, eparam = self.getParamStruct('external',True)
        if eres and act != None:
            tasks_descrp = act.getLabelDescriptions()
            conv_type = eparam.get("description_conv","std")
            if conv_type == "jinja2":
                conv_template = eparam.get("description_jinja2","std")
                info = Txt.jsonToMarkdown({"data":tasks_descrp}, conv_template)
            else:
                info = "\n".join([t["description"] for t in tasks_descrp])
            eparam["description"] = info
            self.setParamStruct(eparam)



    def updateIternal(self, input : TaskDescription = None):
        self.updateUpdationInfo("Update internal")
        self.setChildUpdateState(True)
        eres, eparam = self.getParamStruct('external',True)
        if self.intact is None:
            self.updateUpdationInfo(f"No actioner")
            if eres and "onupdate" in eparam and eparam["onupdate"] == "loadact_ignore":
                if not self.checkParentMsgList(remove=False, update=True):
                    self.updateUpdationInfo(f"Parent Msgs is not same")
                    self.freezeTask()
                    self.setChildUpdateState(False)
            elif eres and "onupdate" in eparam and eparam["onupdate"] == "loadact_check":
                self.freezeTask()
                self.setChildUpdateState(False)
            else:
                self.freezeTask()
                self.setChildUpdateState(False)
            self.updateDescription()
            return
        self.reconnectJumperTreeExtTree()
        self.updateInternalGlobalKeys()
        self.updateUpdationInfo(f"Acioner is loaded")
        if not self.checkParentMsgList(remove=False, update=True):
            self.updateUpdationInfo(f"Parent Msgs is not same")
            if eres and 'actions_on' in eparam and eparam['actions_on'] == False:
                self.updateUpdationInfo("Disabled action execution")
                pass
            elif eres and 'updt_actions' in eparam and eparam['updt_actions'] == "":
                self.updateUpdationInfo("No actions for update")
            elif eres and 'updt_actions' in eparam and eparam['updt_actions'] != "":
                results = self.runJsonCommandByInnerActioner( self.findKeyParam(eparam['updt_actions']) )
                self.updateUpdationInfo(f"UPDATE Actions with results:{results}")
            else:
                self.updateUpdationInfo("Default update")
                self.intact.loadTmpManagerTasks()
                self.intact.manager.disableOutput2()
                if eres and 'update_count' in eparam and isinstance(eparam['update_count'], int):
                    for i in range(eparam['update_count']):
                        self.intact.updateAll(force_check=True)
                else:
                    self.intact.updateAll(force_check=True)
                self.intact.manager.enableOutput2()
        # elif self.isFrozen():
        # elif self.intact.manager.getFrozenTasksCount():
        #     self.intact.loadTmpManagerTasks()
        #     print(f"Frozen tasks:{self.intact.manager.getFrozenTasksCount()}")
        #     self.intact.manager.disableOutput2()
        #     self.intact.updateAll(force_check=True)
        #     self.intact.manager.enableOutput2()
        else:
            self.updateUpdationInfo(f"No update: idle action")
            if eres and 'actions_on' in eparam and eparam['actions_on'] == False:
                pass
            elif eres and 'idle_actions' in eparam and eparam['idle_actions'] != "":
                results = self.runJsonCommandByInnerActioner( self.findKeyParam(eparam['idle_actions']) )
                self.updateUpdationInfo(f"IDLE Actions with results:{results}")
            if eres and "onupdate" in eparam and eparam["onupdate"] == "loadact_ignore":
                self.setChildUpdateState(False)
        if eres and "onupdate" in eparam and eparam["onupdate"] == "loadact_check":
            if self.intact.getFrozenTasksCount() > 0 \
                and eres and 'actions_on' in eparam and eparam['actions_on'] \
                and 'updt_actions' in eparam and eparam['updt_actions'] != "":
                    results = self.runJsonCommandByInnerActioner( self.findKeyParam(eparam['updt_actions']) )
                    # self.updateUpdationInfo(f"UPDATE Actions (frozen) with results:{results}")
            check_frozen_tasks = eparam.get("check_frozen_tasks",True)

            if check_frozen_tasks and self.intact.getFrozenTasksCount() > 0:
                frozen_names = ", ".join([ t.getName() for t in self.getActioner().getFrozenTasks()])
                self.updateUpdationInfo(f"Freeze cz internal tasks: {frozen_names}")
                self.freezeTask()
                self.forceResetHash()
                self.setChildUpdateState(False)

        if eres:
            input_tokens_count = 0
            output_tokens_count = 0
            manager_report = self.getActioner().getCurrentManager().getTaskReports()
            if isinstance(manager_report, list):
                try:
                    for report in self.manager.getTaskReports():
                        input_tokens_count += report.get("intok",0)
                        output_tokens_count += report.get("outtok", 0)
                except Exception as e:
                    logger.debug( "Error with report:\n %s")
                    
                response_report = {
                    "intok":input_tokens_count,
                    "outtok":output_tokens_count
                }
                response_report["time"] = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")        
                response_report["source_task"] = self.getName()
                self.manager.onTaskReport( response_report )

            # eparam["task_reports_after_cmd"] = Loader.Loader.convJsonToText(self.manager.getTaskReports())
        self.updateDescription()

        
    def removeProject(self):
        pass

    def forceCleanChat(self):
        eres, eparam = self.getParamStruct('external',True)
        act = self.getActioner()
        if act == None:
            return super().forceCleanChat()
        if eres and eparam.get("exttreetask_template_load_onreset", False):
            path_to_template = eparam.get("exttreetask_file_current","")
            if not Fm.checkExistPath( path_to_template ):
                self.updateUpdationInfo(f"Reload with template [{path_to_template}]")
                path_to_template = Loader.Loader.getUniPath( self.findKeyParam( eparam.get("exttreetask_template","") ) )
            else:
                self.updateUpdationInfo(f"Reload from Current File {path_to_template}")
            if Fm.checkExistPath( path_to_template ):
                act.loadManagerProjectFromFile ( path_to_template )
                act.syncRelatedActionersWithFolder()
                self.updateUpdationInfo(f"Loaded and synced")
        if eres and 'reset_actions' in eparam and eparam['reset_actions'] != "":
            results = self.runJsonCommandByInnerActioner( self.findKeyParam(eparam['reset_actions']) )
            self.updateUpdationInfo(f"RESET Actions with results:{results}")
        return super().forceCleanChat()

 
    def getExtTreeTaskCmds(self, filter_on = False, min_value = 5):
        lres, lparam = self.getParamStruct("external", True)
        if lres:
            custom_commands = lparam.get("generated_actions",[])
            if filter_on:
                output = []
                for action in custom_commands:
                    if isinstance(action, dict):
                        value = action.get("confidence",0)
                        if value > min_value:
                            output.append(action)
                return output
            else:
                return custom_commands
        return super().getExtTreeTaskCmds(filter_on, min_value)
    
    def updateGeneratedAction ( self ):
        lres, lparam = self.getParamStruct("external", True)
        if lres:
            custom_commands = []
            cmds_txt = lparam.get("custom_actions","[]")
            cmds_txt = self.findKeyParam( cmds_txt )
            jres, jcmds = Loader.Loader.loadJsonFromText( cmds_txt )
            if jres:
                custom_commands = [Loader.Loader.convJsonToText(j) for j in jcmds]
            act = self.getActioner()
            if act != None:
                for task in act.getCurrentManager().getTasks():
                    res, cmds = task.getAutoActCmds(checkhash = False)
                    if res:
                        if isinstance(cmds, list):
                            for cmd in cmds:
                                if "action" in cmd:
                                    cmd["output_task"] = task.getName()
                                    try:
                                        cmd["session"] = self.manager.getUpdateSessionId()
                                    except Exception as e:
                                        print(f"Session error:{e}")
                                    custom_commands.append(Loader.Loader.convJsonToText(cmd))
            lparam["generated_actions"] = custom_commands
            self.setParamStruct(lparam)

    def preExeCmds(self, param):
        act = self.getActioner()
        if act != None:
            if param.get("save_prev", False):
                path = self.findKeyParam( param.get("folder_path","") )
                name = self.findKeyParam( param.get("archive_name","default") )
                max_times = param.get("store_max", 3)
                act.saveTemporaryArchiveWithCheck( path, name, max_times )
        return super().preExeCmds(param)
 
    def exeExTreeTaskCmds( self, cmds ):
        act = self.getActioner()
        if act != None:
            result = self.runJsonCommandByInnerActioner( cmds )
            self.updateGeneratedAction()
            self.setChildUpdateState( True )
            for child in self.getChilds():
                if child.checkType( "OutExtTree" ):
                    child.updateIternal()
            self.setChildUpdateState( False )
            return f"Run ext tree task cmds: {result}"
        return super().exeExTreeTaskCmds( cmds )
    
    def removeJsonTaskCmds( self, cmds ):
        act = self.getActioner()
        if act != None:
            self.updateUpdationInfo(f"Remove ext tree actions")
            for cmd in cmds:
                if "output_task" in cmd:
                    task = act.getCurrentManager().getTaskByName(cmd["output_task"])
                    if task != None:
                        del cmd["output_task"]
                        task.removeAutoCommandFromparam( cmd )
            self.updateGeneratedAction()
            # eres, eparam = self.getParamStruct('external',True)
            # if eres and 'updt_actions' in eparam and eparam['updt_actions'] != "":
            #     results = act.getJsonCmd(self.findKeyParam(eparam['updt_actions']))
                # self.updateUpdationInfo(f"UPDATE Actions with results:{results}")
 
    def getExternalActionerTask(self):
        act = self.getActioner()
        eres, eparam = self.getParamStruct('external',True)
        if not eres:
            return super().getExternalActionerTask()
        if act != None:
            return True, act.getPath(), eparam['jumper']
        return super().getExternalActionerTask()
    
    def setExtTreeSessionId(self, session_id):
        act = self.getActioner()
        if act != None:
            act.getCurrentManager().setUpdateSessionId( session_id )
        return super().setExtTreeSessionId(session_id)
    
    def addInfoForGenslidesCommand(self, cmds):
        report_data = []
        if self.getActioner() != None and isinstance(cmds, list):
            output = []
            for cmd in cmds:
                result_cmd, report = CommandTool.addSupportInformation( cmd, self.getActioner().getCurrentManager() )
                # self.updateUpdationInfo(f"addInfoForGenslidesCommand:\n{report}")
                report_data.append(report)
                logger.debug("addInfoForGenslidesCommand: %s",report)
                if result_cmd.get("aa_status", False):
                    output.append( result_cmd )
            # return Loader.Loader.convJsonToText( output )
            return  True, output, "\n".join(report_data)
        return super().addInfoForGenslidesCommand(cmds)

    def loadFromArchive(self, path_to_template, sync=True, archive_save_path=""):
        act = self.getActioner()
        if act != None:
            path = Loader.Loader.getUniPath( path_to_template )
            autoload_result = act.loadManagerProjectFromFile( path )
            self.reloadTaskActioner( act.getExternalActionersList())
            if autoload_result:
                if sync:
                    act.syncRelatedActionersWithFolder()
                if archive_save_path != "":
                    act.saveGenslidesArchiveByPath( archive_save_path )
 
            return autoload_result
        return super().loadFromArchive(path_to_template, sync, archive_save_path)

    def saveProjectByPath(self, path_to_file):
        act = self.getActioner()
        if act != None:
            return act.saveProjectByPath( path_to_file )
        return super().saveProjectByPath(path_to_file)


class OutExtTreeTask(ExtProjectTask):
    def __init__(self, task_info: TaskDescription, type="OutExtTree") -> None:
        super().__init__(task_info, type)
        self.readbranchmsg_idx = 0

    def getExternalActionerTask(self):
        eres, eparam = self.getParamStruct('external',True)
        if eres and \
            self.getParent() != None and self.getParent().getActioner() != None:
                return True, self.getParent().getActioner().getPath() ,eparam.get("target","")
        return super().getExternalActionerTask()

    def getExtTreeTaskCmds(self, filter_on = False, min_value = 5):
        if self.getParent():
            return self.getParent().getExtTreeTaskCmds(filter_on, min_value)
        return super().getExtTreeTaskCmds(filter_on, min_value)
    
    def exeExTreeTaskCmds(self, cmds):
        if self.getParent():
            return self.getParent().exeExTreeTaskCmds( cmds )
        return super().exeExTreeTaskCmds(cmds)
    
    def removeJsonTaskCmds(self, cmds):
        if self.getParent():
            return self.getParent().removeJsonTaskCmds( cmds )
        return super().removeJsonTaskCmds(cmds)

    def onExistedMsgListAction(self, msg_list_from_file):
        self.updateUpdationInfo(f"msg_list_old:\n{msg_list_from_file}")
        self.setMsgList(msg_list_from_file)
        self.saveJsonToFile(self.msg_list)


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
    
    def setExternalTask( self, task : BaseTask ):
        if task != None:
            self.updateUpdationInfo(f"Set external task {task.getName()}")
            if task != self.intch_trg:
                self.updateUpdationInfo("External is NOT same")
                self.intch_trg = task
                if self.manager.getActioner() != None:
                    res, param = task.getParamStruct("outexttreetask", True)
                    if res:
                        links : list = param.get("links",[])
                        act_path = self.manager.getActioner().getPath()
                        if act_path not in links:
                            links.append(act_path)
                            param["links"] = links
                            task.setParamStruct( param )
                    else:
                        task.setParamStruct({'type':'outexttreetask','links':[self.manager.getActioner().getPath()]})       
                else:
                    self.updateUpdationInfo("No actioner for external")
            else:
                self.updateUpdationInfo("Do not change outexttree task")


    def updateOutExtActMan(self, actioners = []):
        try:
            parent = self.getParent()
            if parent and parent.isExternalProjectTask():
                # if parent.checkType("JumperTree") or parent.checkType("InExtTree"):
                    eres, eparam = self.getParamStruct('external')
                    self.intact = self.parent.intact
                    self.intman = self.parent.intman
                    self.intact.autoUpdateExtTreeTaskActs(actioners)

                    self.setExternalTask(self.intman.getTaskByName(eparam['target']))
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
                            self.setExternalTask(man.getTaskByName(eparam['target']))
                            self.intact.autoUpdateExtTreeTaskActs(actioners)
                            return

            
        except Exception as e:
            self.updateUpdationInfo(f"Failed load man and act:{e}")

    def checkGetContentAndParent(self) -> list[bool, list, BaseTask]:
        return False, [], self.intch_trg
    
    def getLastMsgAndParent(self, hide_task = True, max_symbols = -1, param = {}, add_task_name = False):
        # if self.intch_trg == None:
            return True,self.getMsgList(),None
        # return self.intch_trg.getLastMsgAndParent(hide_task, max_symbols, param )
        # return False, [], self.intch_trg
    
    def getPromptContentForCopyConverted(self):
        if self.intch_trg == None:
            return ""
        return self.intch_trg.getPromptContentForCopyConverted()

    def getParentForFinder(self):
        # if self.intch_trg == None:
            self.readbranchmsg_idx += 1
            return self
        # return self.intch_trg.getParentForFinder()

    def freeTaskByParentCode(self):
        self.readbranchmsg_idx = 0
        return super().freeTaskByParentCode()
    


    def getLastMsgContent(self):
        # if self.intch_trg == None:
            msgs = self.getMsgList()
            length = len(msgs)
            if length > 0 and self.readbranchmsg_idx < length:
                return msgs[length - 1 - self.readbranchmsg_idx]["content"]
            else:
                return ""
        # return self.intch_trg.getLastMsgContent()

    def updateIternal(self, input : TaskDescription = None):
        if not self.getParent():
            return
        if self.getParent().isFrozen():
            self.updateUpdationInfo(f"Skipping update: parent is frozen")
            self.freezeTask()
            return
        if self.intact == None or self.intact != self.getParent().intact:
            self.updateOutExtActMan()
        if self.intact == None:
            self.updateUpdationInfo(f"No internal actioner for {self.getName()}")
            # self.freezeTask()
            return
        if not self.getParent().canChildUpdate():
            self.updateUpdationInfo(f"Block by {self.getParent().getName()}")
            if self.intch_trg != None and self.intch_trg.isFrozen():
                self.updateUpdationInfo(f"{self.intch_trg.getName()} is frozen")
                # self.freezeTask()
            return
        # if self.intch_trg == None:
        eres, eparam = self.getParamStruct('external')
        if eres:
            self.setExternalTask(self.intman.getTaskByName(eparam['target']))
        try:
            if self.intch_trg.is_freeze:
                eres, eparam = self.getParamStruct('external')
                try:
                    task = self.intman.getTaskByName(eparam['target'])
                    self.updateUpdationInfo( f"task {task.getName()} is frozen: {task.isFrozen()} ")
                    self.updateUpdationInfo(f"src manager: {self.intman.getPath()}")
                    self.updateUpdationInfo(f"Target {self.intch_trg.getName()}|{self.intact.getPath()} is frozen:{self.intch_trg.isFrozen()}")
                    self.updateUpdationInfo(f"trg manager: {self.intch_trg.manager.getPath()}")
                    self.updateUpdationInfo(f"managers eq: {self.intch_trg.manager == task.manager}")
                except:
                    pass
                self.freezeTask()
                if self.isExternalProjectTask():
                    self.updateInternalActioners()
            else:
                self.updateUpdationInfo(f"Update Msgs list")
                self.setMsgList(self.intch_trg.getMsgs())
                self.saveAllParams()
                self.stdProcessUnFreeze()
            bres, bparam = self.intch_trg.getParamStruct('bud')
            if bres:
                param = {'type':'bud','text': bparam['text'],'branch':self.getBranchCodeTag()}
                self.setParamStruct(param)
            else:
                self.updateUpdationInfo('No param for summary')
 
            
        except Exception as e:
            self.updateUpdationInfo(f"Abort updating: {e}")
            self.stdProcessUnFreeze()

    
    def getParentForRaw(self):
        return self.intch_trg
    
    def removeProject(self):
        pass

    def getParamStructFromExtTask(self, param_name):
        return False, self.intch_trg, None
    
    def getTaskReport(self, report):
        if self.intch_trg != None:
            return self.intch_trg.getTaskReport( report )
        return super().getTaskReport(report)
    
