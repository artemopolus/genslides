from genslides.task.base import TaskDescription
from genslides.task.readfile import ReadFileTask

import os

class ReadFileParamTask(ReadFileTask):
    def __init__(self, task_info: TaskDescription, type="ReadFileParam") -> None:
        super().__init__(task_info, type)

    def loadContent(self, s_path, msg_trgs):
        param_name = "path_to_read"
        res, s_path = self.getParam(param_name)
        if res and os.path.isfile(s_path):
            with open(s_path, 'r') as f:
                text = f.read()
                msg_trgs[-1]["content"] = text
                return True, msg_trgs
        return False, msg_trgs



    def executeResponse(self):
      #   str = "J:\WorkspaceFast\genslides\examples\05table_parts_slides1_req.txt"
        param_name = "path_to_read"
        res, path = self.getParam(param_name)
        if res and os.path.isfile(path):
           with open(path, 'r') as f:
                print("path_to_read =", path)
                text = f.read()
                self.msg_list = self.parent.msg_list.copy()
                self.msg_list.append({
                    "role": self.prompt_tag,
                    "content": text
                })

    def getMsgInfo(self):
        param_name = "path_to_read"
        res, path = self.getParam(param_name)
        value = "None"
        if res:
            value = path
        if len(self.msg_list):
            out = self.msg_list[len(self.msg_list) - 1]
            return value, out["role"],out["content"]
        return value,"user",""
 
