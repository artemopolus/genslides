from genslides.task.base import TaskDescription
from genslides.task.writetofile import WriteToFileTask
import json

class WriteDialToFileTask(WriteToFileTask):
    def __init__(self, task_info: TaskDescription, type="WriteDialToFile") -> None:
        super().__init__(task_info, type)

    def executeResponse(self):
        param_name = "path_to_write"
        self.updateParam(param_name,self.getRichPrompt())
        self.saveJsonToFile(self.msg_list)
       # what to write  0
        # text           1
        # where to write 2
        # path           3
        # this task
        print("-----------------------------------------------------------------------------------Msg lst=", len(self.msg_list))
        if len(self.msg_list) < 3:
            return
        # print("Path=", self.getRichPrompt())
        # if os.path.isfile(self.getRichPrompt()):
        with open(self.getRichPrompt(), 'w',encoding='utf8') as f:
            print(self.getName(), "read", self.getRichPrompt())
            # text = self.msg_list[len(self.msg_list) - 3]["content"]
            resp_json_out = self.msg_list.copy()
            resp_json_out.pop()
            resp_json_out.pop()
            json.dump(resp_json_out, f, indent=1)


