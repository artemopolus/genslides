from genslides.task.base import TaskDescription
from genslides.task.collect import CollectTask

# from genslides.commanager.jun import Manager
import genslides.commanager.jun as Manager

from genslides.utils.reqhelper import RequestHelper
from genslides.utils.testrequest import TestRequester
from genslides.utils.searcher import GoogleApiSearcher

import os
import shutil

class ExtProjectTask(CollectTask):
    def __init__(self, task_info: TaskDescription, type="ExtProject") -> None:
        super().__init__(task_info, type)

    def afterFileLoading(self):
        print('Init external project task')
        self.intman = Manager.Manager(RequestHelper(), TestRequester(), GoogleApiSearcher())
        res, param = self.getParamStruct('external')
        if not res:
            return
            # path = os.path.join( self.manager.getPath(), 'ext', task_info.prompt) + '\\'
            # self.setParamStruct({'type':'external','project':task_info.prompt,'path':path})
            # print('Path to task=', path)
            # self.intman.setPath(path)
        else:
            if 'path' in param:
                path = param['path']
            else:
                path = os.path.join( self.manager.getPath(), 'ext', param['project']) + '\\'
                param['path'] = path
                self.updateParam2(param)

            if 'prompt' in param:
                self.prompt = param['prompt']
            else:
                param['prompt'] = self.prompt
                self.updateParam2(param)

            self.intman.setPath(path)
        
        self.intman.loadTasksList()

        print(self.getName(),'internal task list', [t.getName() for t in self.intman.task_list])

        self.intpar = None
        self.intch = None

        for task in self.intman.task_list:
            res, param = task.getParamStruct('input')
            if res and param['input']:
                self.intpar = task
                self.intpar.parent = self.parent
                
            res, param = task.getParamStruct('output')
            if res and param['output']:
                self.intch = task

    def hasNoMsgAction(self):
        self.updateExtProjectInternal(self.prompt)

    def updateExtProjectInternal(self, prompt):
        if self.intpar is not None:
            print('Update external task')
            info = TaskDescription(prompt=prompt, prompt_tag=self.intpar.getLastMsgRole(), stepped=True, manual=True)
            self.intman.curr_task = self.intpar
            self.intman.updateSteppedTree(info)
            if self.intch is not None:
                res_list = self.getRawParentMsgs()
                res_list.extend(self.intch.getMsgs())
                self.setMsgList(res_list)
        self.updateParamStruct('external', 'prompt', prompt)
        self.saveJsonToFile(self.msg_list)

    def haveMsgsAction(self, msgs):
        trg_list = self.getRawParentMsgs()
        trg_list.extend(self.intch.getMsgs())
        if trg_list == msgs:
            pass
        else:
            self.updateExtProjectInternal(self.prompt)
    
    def checkParentsMsg(self):
        return []
    
    def updateCollectedMsgList(self, trg_list : list):
        pass

    def updateIternal(self, input : TaskDescription = None):
        self.haveMsgsAction(self.msg_list)

    def beforeRemove(self):
        print('Delete external proj files')
        res, param = self.getParamStruct('external')
        if res and 'path' in param:
            print('Remove', param['path'])
            shutil.rmtree(param['path'])
        super().beforeRemove()

