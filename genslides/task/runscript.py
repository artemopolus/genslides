from genslides.task.base import TaskDescription
from genslides.task.response import ResponseTask


import os
from os.path import isfile, join
from os import listdir
import subprocess

class RunScriptTask(ResponseTask):
    def __init__(self, task_info: TaskDescription, type="RunScript") -> None:
        # self.path_to_script = "output\\scripts\\"
        super().__init__(task_info, type)

    def executeResponse(self):
        # path_tmp = self.path_to_script
        res, path_tmp = self.getParam("path_to_script")
        if not res:
            print("No path to script")
            return
        res, path_to_python = self.getParam("path_to_python")
        if not res:
            print("No path to python")
            return
        if not os.path.exists(path_tmp):
            print("Path to script is not valid")
            return
        onlyfiles = [f for f in listdir(path_tmp) if isfile(join(path_tmp, f))]
        print("Trg files=", onlyfiles)
        data = ""
        for file in onlyfiles:
            if file.endswith(".py"):
                script_path = path_tmp + file
                print("Run script", path_to_python," on path", script_path)
                result = subprocess.run([path_to_python, script_path], capture_output=True, text=True)
                if result.returncode:
                    print("Result=", result.stderr)
                data += result.stdout + "\n"


                res, need_to_remove = self.getParam("remove_script")
                if res and need_to_remove:
                    try:
                        os.remove(script_path)
                        print("Remove ", script_path)
                    except:
                        print("Can't remove ", script_path)
                        pass
            else:
                print("File is not valid=", file)

        if len(data) > 0:
            self.msg_list.append({"role": self.prompt_tag, "content": data})
        else:
            print("No data is getted from",file)
        
