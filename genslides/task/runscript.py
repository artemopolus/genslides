from genslides.task.base import TaskDescription
from genslides.task.response import ResponseTask
from genslides.utils.readfileman import ReadFileMan
from genslides.utils.loader import Loader


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
        res, pparam = self.getParamStruct("script")
        if res:
            try:
                path_tmp = self.findKeyParam(pparam["path_to_script"] )
                path_to_python = pparam["path_to_python"]
                need_to_remove = pparam["remove_script"]  
                phrase_script = self.findKeyParam( pparam["init_phrase"] )
                phrase_success = self.findKeyParam( pparam["on_success"] )
                phrase_error = self.findKeyParam( pparam["on_error"] )

                str_path_to_output_files = self.findKeyParam(pparam["output_files"])
            except Exception as e:
                print("Error on script struct param=",e)
        else:
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
            need_to_remove = False
            res, need_to_remove_tmp = self.getParam("remove_script")
            if res:
                need_to_remove = need_to_remove_tmp
            phrase_script = "I run script: "
            phrase_success = "I have execution result: "
            phrase_error = "I have error: "
        onlyfiles = [f for f in listdir(path_tmp) if isfile(join(path_tmp, f))]
        print("Trg files=", onlyfiles)
        data = ""
        for file in onlyfiles:
            if file.endswith(".py"):
                script_path = path_tmp + file
                
                data += phrase_script + path_to_python + " " + script_path + "\n"
                print("Run script", path_to_python," on path", script_path)
                result = subprocess.run([path_to_python, script_path], capture_output=True, text=True)
                if result.returncode:
                    data += phrase_error + result.stderr + "\n"
                else:
                    data += phrase_success + result.stdout + "\n"

                data += "\n\n\nHere below outputs of script:\n\n\n"

                if str_path_to_output_files:
                    tres, output_paths = Loader.stringToPathList(str_path_to_output_files)
                    print('Path to output:', output_paths)
                    if tres:
                        for p in output_paths:
                            # ppath=p.strip("\'")
                            tres, text = ReadFileMan.readPartitial(p,400)
                            data += text + "\n"
                    else:
                        data += "No files on path" + str_path_to_output_files



                if need_to_remove:
                    try:
                        os.remove(script_path)
                        print("Remove ", script_path)
                    except:
                        print("Can't remove ", script_path)
                        pass
            else:
                print("File is not valid=", file)

        if len(data) > 0:
            self.msg_list.append({"role": "user", "content": data})
        else:
            print("No data is getted from")
        
