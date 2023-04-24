import genslides.utils.reqhelper as ReqHelper
import genslides.utils.request as Requester

class BaseTask():
    def __init__(self, reqhelper: ReqHelper, requester : Requester, type = 'None', prompt = '') -> None:
        self.left = None
        self.right = None
        self.is_solved = False
        self.reqhelper = reqhelper
        self.requester = requester
        self.responselist = []
        self.type = type
        self.init = self.reqhelper.getInit(type)
        self.endi = self.reqhelper.getEndi(type)
        self.prompt = prompt

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
        return None
    def completeTask(self):
        return False 
