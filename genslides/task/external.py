import genslides.task.request as RqTask

class ExternalInput(RqTask.RequestTask):
    def __init__(self, task_info: RqTask.TaskDescription, type="ExternalInput") -> None:
        super().__init__(task_info, type)

    def setParent(self, parent):
        self.parent = parent

    def getClearName(self, manager) -> str:
        return ""
    
    def isRootParent(self):
        return True
    