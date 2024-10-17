import genslides.task.request as RqTask

class ExternalInput(RqTask.RequestTask):
    def __init__(self, task_info: RqTask.TaskDescription, type="ExternalInput") -> None:
        super().__init__(task_info, type)

    def setParent(self, parent):
        self.parent = parent

    def getParentPath(self):
        return ""

    def isRootParent(self):
        return True
    
    def stdProcessUnFreeze(self, input=None):
        if self.parent == None:
            self.freezeTask()
        else:
            super().stdProcessUnFreeze(input)

    def getLastMsgAndParent(self, hide_task = True, max_symbols = -1, param = {}):
        return False, [], self.parent
 