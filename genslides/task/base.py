import genslides.utils.reqhelper as ReqHelper
import genslides.utils.request as Requester

from genslides.commands.create import CreateCommand
from genslides.helpers.singleton import Singleton

class TaskManager(metaclass=Singleton):
    def __init__(self) -> None:
        self.task_id = 0
        self.task_list = []

    def getId(self, task) -> int:
        id = self.task_id
        self.task_id += 1
        if task not in self.task_list:
            self.task_list.append(task)
        return id


class TaskDescription():
    def __init__(self, prompt, method = None, parent=None, helper=None, requester=None, target=None, id = 0) -> None:
        self.prompt = prompt
        self.method = method
        self.parent = parent
        self.helper = helper
        self.requester = requester
        self.target = target
        self.id = id

class BaseTask():
    def __init__(self, task_info : TaskDescription, type = 'None') -> None:
        self.childs = []
        self.is_solved = False
        self.reqhelper = task_info.helper
        self.requester = task_info.requester
        self.crtasklist = []
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

    def getName(self) -> str:
        return str(self.id)
    def getLabel(self) -> str:
        return self.type + ' ' + str(self.id)


    def getNewID(self) -> int:
        task_manager = TaskManager()
        self.id = task_manager.getId(self)
        return self.id


    def addChildTask(self, task : TaskDescription):
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
    def completeTask(self):
        return False 
