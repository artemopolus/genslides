from genslides.task.base import TaskDescription, BaseTask
from genslides.task.collect import CollectTask

# from genslides.commanager.jun import Manager
import genslides.commanager.group as Actioner

from genslides.utils.reqhelper import RequestHelper
from genslides.utils.testrequest import TestRequester
from genslides.utils.searcher import GoogleApiSearcher
import genslides.utils.loader as Loader

import os
import shutil
import pathlib

class ExtProjectTask(CollectTask):
    def __init__(self, task_info: TaskDescription, type="ExtProject") -> None:
        self.intpar = None
        self.intch = []
        self.intch_trg = None
        self.intman = None
        super().__init__(task_info, type)
        self.is_freeze = False

    def afterFileLoading(self):
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
        self.actioner = Actioner.Actioner(self.intman)
        self.actioner.setPath(path)
        self.actioner.clearTmp()
        # print(10*"----------")
        # print('Load tasks from',path)
        # print(10*"----------")
        self.intman.disableOutput2()
        self.intman.loadTasksList()
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
        return self.actioner

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
        self.actioner.callScript('init_created')
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
                self.actioner.callScript('init_loaded_change')
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
                self.actioner.callScript('update_input_step')
                self.updateInOutExtProject()
            else:
                # self.intpar.update(input)
                self.updateExtProjectInternal(input.prompt)
                self.actioner.callScript('update_input_nostep')
                self.updateInOutExtProject()
        else:
            if self.intpar is not None and not self.intpar.checkParentMsgList(update=False, remove=True):
                print('Normal update', self.getName())
                info = TaskDescription(prompt=self.prompt, prompt_tag=self.intpar.getLastMsgRole(), manual=True)
                self.intpar.update(info)
                self.actioner.callScript('update_noinput')
                self.updateInOutExtProject()
            else:
                return
        if len(self.intch):
            self.setMsgList(self.intch_trg.getMsgs())
        self.saveJsonToFile(self.msg_list)

    def beforeRemove(self):
        print('Delete external proj files')
        # res, param = self.getParamStruct('external')
        # if res and 'path' in param:
        #     print('Remove', param['path'])
        #     shutil.rmtree(param['path'])
        if self.intman is not None:
            self.intman.beforeRemove(True)
            del self.intman
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
 
 
