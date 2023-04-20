import genslides.utils.reqhelper as ReqHelper
class BaseTask():
    def __init__(self, reqhelper: ReqHelper) -> None:
        self.left = None
        self.right = None
        self.is_solved = False
        self.reqhelper = None
        self.reqhelper = reqhelper

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
