from genslides.task.base import TaskDescription
from genslides.task.readfile import ReadFileTask
import os
import json

class ReadDialTask(ReadFileTask):
    def __init__(self, task_info: TaskDescription, type="ReadDial") -> None:
        super().__init__(task_info, type)
        self.saveJsonToFile(self.msg_list)

    def parentAction(self):
        pass

    def getRichPrompt(self) -> str:
        if self.parent:
            return self.parent.msg_list[-1]["content"]
        return self.prompt



    def executeResponse(self):
        if os.path.isfile(self.getRichPrompt()):
            param_name = "path_to_read"
            self.updateParam(param_name,self.getRichPrompt())

            with open(self.getRichPrompt(), 'r') as f:
                print("path_to_read =", self.getRichPrompt())
                rq = json.load(f)
                self.msg_list= rq