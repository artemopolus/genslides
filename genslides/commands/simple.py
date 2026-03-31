from abc import ABCMeta, abstractmethod

import genslides.task.base as base
import genslides.utils.savedata as Save

class SimpleCommand(metaclass=ABCMeta):
    def __init__(self, input : base.TaskDescription ) -> None:
        self.input = input
        self.name = "simple"
        self.time = Save.getTimeForSaving()
        self.task : base.BaseTask = None
        self.session_exe_id = ""
        self.manager = None
        self.manager_info = {}

    def setManagerInfo( self, data: dict ):
        self.manager_info = data


    def setSessionId(self, id):
        self.session_exe_id = id

    def getSessionId(self):
        return self.session_exe_id

    def setManager( self, man ):
        self.manager = man
    
    def getCmdInfo( self ):
        cmd_info = {
            "name":self.name,
            "time":self.time,
            "info": self.manager_info
        }
        return cmd_info

    def getName(self):
        task_name = "None" if self.task == None else self.task.getName()
        return f"{self.name} ({self.time}): {task_name}"

    @abstractmethod
    def execute(self) -> None:
        return None, 'stay'

    @abstractmethod
    def unexecute(self) -> None:
        return None, 'stay'
