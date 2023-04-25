import genslides.utils.reqhelper as ReqHelper
import genslides.utils.request as Requester

from genslides.commands.create import CreateCommand

class TaskDescription():
    def __init__(self, prompt, method, parent) -> None:
        self.prompt = prompt
        self.method = method
        self.parent = parent

class BaseTask():
    def __init__(self, reqhelper: ReqHelper, requester : Requester, type = 'None', prompt = '', parent = None, method = None) -> None:
        self.left = None
        self.right = None
        self.is_solved = False
        self.reqhelper = reqhelper
        self.requester = requester
        self.crtasklist = []
        self.type = type
        self.init = self.reqhelper.getInit(type)
        self.endi = self.reqhelper.getEndi(type)
        self.prompt = prompt
        self.parent = parent
        self.method = method

    def addChildTask(self, task : TaskDescription):
        self.crtasklist.append(task)
    def isSolved(self):
        return self.is_solved

    def addChild(self, child):
        if (self.left != None):
            self.left = child
        elif (self.right == None):
            self.right = child
        else:
            return False
        return True
    def getCmd(self):
        if len(self.crtasklist) > 0:
            task = self.crtasklist.pop()
            print('Register command:' + str(task.method))
            return CreateCommand( task.parent, self.reqhelper, self.requester, task.prompt , task.method)
        return None
    def completeTask(self):
        return False 
