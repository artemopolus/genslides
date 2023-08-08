from genslides.task.base import TaskDescription
from genslides.task.writetofile import WriteToFileTask

import json

class WriteJsonToFileTask(WriteToFileTask):
    def __init__(self, task_info: TaskDescription, type="WriteJsonToFile") -> None:
        super().__init__(task_info, type)


    def executeResponse(self):
        if self.parent == None:
            return
        prop = self.msg_list[-1]["content"]
        prop_json = json.dumps(prop)
        if "filepath" in prop_json and "text" in prop_json:
            with open(prop_json["filepath"], 'w',encoding='utf8') as f:
                f.write(prop_json["text"])
            param_name = "path_to_write"
            self.updateParam(param_name,prop_json["filepath"])
            self.saveJsonToFile(self.msg_list)
 
