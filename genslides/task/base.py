import genslides.utils.reqhelper as ReqHelper
import genslides.utils.request as Requester

from genslides.commands.create import CreateCommand
from genslides.helpers.singleton import Singleton

import os
from os import listdir
from os.path import isfile, join

import json

from genslides.utils.largetext import SimpleChatGPT

class TaskManager(metaclass=Singleton):
    def __init__(self) -> None:
        self.task_id = 0
        self.task_list = []
        self.model_list = []
        chat = SimpleChatGPT()
        self.model_list = chat.getModelNames()

    def getId(self, task) -> int:
        id = self.task_id
        self.task_id += 1
        if task not in self.task_list:
            self.task_list.append(task)
        return id
    
    def getPath(self) -> str:
        if not os.path.exists("saved"):
            os.makedirs("saved")
        return "saved/"
    
    def getLinks(self):
        mypath = self.getPath()
        onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
        out = []
        for filename in onlyfiles:
            path = join(mypath,filename)
            try:
                with open(path, 'r') as f:
                    rq = json.load(f)
                if 'linked' in rq:

                    pair = {}
                    pair['name'] = filename.split('.')[0]
                    pair['linked'] = rq['linked']
                    out.append(pair)
            except Exception as e:
                pass
        return out

    
    def getParentTaskPrompts(self):
        mypath = self.getPath()
        onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
        out = []
        for filename in onlyfiles:
            path = join(mypath,filename)
            try:
                with open(path, 'r') as f:
                    rq = json.load(f)
                if 'parent' in rq:
                    print(path)
                    parent_path = rq['parent']
                    if parent_path == "" and 'chat' in rq and 'type' in rq:
                        print(path)
                        
                        for elem in rq['chat']:
                            if elem['role'] == 'user':
                                pair = {}
                                pair['type'] = rq['type']
                                pair['content'] = elem['content']
                                out.append(pair)
            except Exception as e:
                pass
        return out

    def getTaskPrompts(self, trg_path = ""):
        mypath = self.getPath()
        onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
        out = []
        for filename in onlyfiles:
            path = join(mypath,filename)
            try:
                with open(path, 'r') as f:
                    rq = json.load(f)
                if 'parent' in rq:
                    # print(path):w

                    parent_path = rq['parent']
                    if parent_path == trg_path and 'chat' in rq and 'type' in rq:
                        print("Get propmt from=",path)
                        # if rq['type'].endswith("RichText") or rq['type'].endswith("Response"):
                        if rq['type'] == "RichText":
                            elem = rq['chat'].pop()
                        elem = rq['chat'].pop()
                        pair = {}
                        pair['type'] = rq['type']
                        pair['content'] = elem['content']
                        pair['role'] = elem['role']

                        out.append(pair)
                        
                        # for elem in rq['chat']:
                        #     if elem['role'] == 'user':
                        #         pair = {}
                        #         pair['type'] = rq['type']
                        #         pair['content'] = elem['content']
                        #         out.append(pair)
            except Exception as e:
                pass
        return out




class TaskDescription():
    def __init__(self, prompt = "", method = None, parent=None, helper=None, requester=None, target=None, id = 0, type = "", prompt_tag = "user") -> None:
        self.prompt = prompt
        self.prompt_tag = prompt_tag
        self.method = method
        self.parent = parent
        self.helper = helper
        self.requester = requester
        self.target = target
        self.id = id
        self.type = type

class BaseTask():
    def __init__(self, task_info : TaskDescription, type = 'None') -> None:
        self.childs = []
        self.is_solved = False
        self.reqhelper = task_info.helper
        self.requester = task_info.requester
        self.crtasklist = []

        type = task_info.type
        self.type = type
        self.init = self.reqhelper.getInit(type)
        self.endi = self.reqhelper.getEndi(type)

        self.prompt = task_info.prompt
        self.method = task_info.method
        task_manager = TaskManager()
        self.id = task_manager.getId(self)
        request = self.init + self.prompt + self.endi
        self.task_description = "Task type = " + self.type + "\nRequest:\n" + request
        self.task_creation_result = "Results of task creation:\n"

        self.parent = task_info.parent
        if  self.parent:
            self.parent.addChild(self)
        self.target = task_info.target

        self.affect_to_ext_list = []
        self.by_ext_affected_list = []
        self.name = self.type + str(self.id)

    def getRichPrompt(self) -> str:
        out = self.prompt
        if not out.startswith(self.init):
            out = self.init + out
        if not out.endswith(self.endi):
            out += self.endi
        for task in self.by_ext_affected_list:
            out += " " + task.prompt
        return out

    def getIdStr(self) -> str:
        return str(self.id)
    def getName(self) -> str:
        return self.name


    def getNewID(self) -> int:
        task_manager = TaskManager()
        self.id = task_manager.getId(self)
        return self.id


    def addChildToCrList(self, task : TaskDescription):
        self.crtasklist.append(task)

    def isSolved(self):
        return self.is_solved
    
    def checkChilds(self):
        for child in self.childs:
            if not child.isSolved():
                return False
        return True

    def addChild(self, child):
        if child not in self.childs:
            self.childs.append(child)

    def getCmd(self):
        if len(self.crtasklist) > 0:
            task = self.crtasklist.pop()
            print('Register command:' + str(task.method))
            return CreateCommand( task)
        return None
   
    def update(self, input : TaskDescription = None):
        for child in self.childs:
            child.update()

    def beforeRemove(self):
        if self.parent:
            self.parent.childs.remove(self)
        for child in self.childs:
            child.whenParentRemoved()

    def whenParentRemoved(self):
        self.parent = None

    def getCountPrice(self):
        return 0,0
    
    def affectedTaskCallback(self, input : TaskDescription):
        pass

    def createLinkToTask(self, task) -> TaskDescription:
        id = len(self.by_ext_affected_list)
        out = TaskDescription(method=self.affectedTaskCallback, id=id, parent=task )
        self.by_ext_affected_list.append(out)
        task.setLinkToTask(out)
        return out
    
    def removeLinkToTask(self):
        while len(self.by_ext_affected_list) > 0:
            input = self.by_ext_affected_list.pop()
            input.parent.resetLinkToTask(input)
        
    
    def setLinkToTask(self, info : TaskDescription) -> None:
        self.affect_to_ext_list.append(info)

    def resetLinkToTask(self, info : TaskDescription) -> None:
        self.affect_to_ext_list.remove(info)

    def useLinksToTask(self):
        input = TaskDescription(prompt=self.prompt)
        for task in self.affect_to_ext_list:
            task.method(input)

    def completeTask(self) -> bool:
        print("Complete Task")
        self.useLinksToTask()
        return False 
 