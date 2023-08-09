from genslides.task.base import TaskDescription
from genslides.task.response import ResponseTask


import os
from os.path import isfile, join
from os import listdir
import subprocess

class RunScriptTask(ResponseTask):
    def __init__(self, task_info: TaskDescription, type="RunScript") -> None:
        self.path_to_script = "output\\scripts\\"
        super().__init__(task_info, type)

    def executeResponse(self):
        path_tmp = self.path_to_script
        if not os.path.exists(path_tmp):
            return
        onlyfiles = [f for f in listdir(path_tmp) if isfile(join(path_tmp, f))]
        print("Trg files=", onlyfiles)
        data = ""
        for file in onlyfiles:
            if file.endswith(".py"):
                script_path = path_tmp + file
                result = subprocess.run(["python", script_path], capture_output=True, text=True)
                data += result.stdout + "\n"

        

        if len(data) > 0:
            self.msg_list.append({"role": self.prompt_tag, "content": data})
        
