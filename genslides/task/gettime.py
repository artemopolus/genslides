from genslides.task.base import TaskDescription
from genslides.task.request import RequestTask
from genslides.task.response import ResponseTask
import datetime

class GetTimeTask(ResponseTask):
    def __init__(self, task_info: TaskDescription, type="GetTime") -> None:
        super().__init__(task_info, type)
        print("Get time")

    def getRichPrompt(self) -> str:
        return self.msg_list[-1]["content"]

    def executeResponse(self):
       self.msg_list.append({
            "role": self.prompt_tag,
            "content": str(datetime.datetime.now()) 
        })
       
    def update(self, input : TaskDescription = None):
        self.msg_list[-1]["content"] = str(datetime.datetime.now())
        return super().update(input)
    

