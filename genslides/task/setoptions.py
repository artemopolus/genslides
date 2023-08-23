from genslides.task.base import TaskDescription
from genslides.task.writetofile import WriteToFileTask

import json


class SetOptionsTask(WriteToFileTask):
    def __init__(self, task_info: TaskDescription, type="SetOptions") -> None:
        super().__init__(task_info, type)

    def executeResponse(self):
        try:
            self.params = json.loads(self.prompt)
        except:
            print("Can't load parameters")
