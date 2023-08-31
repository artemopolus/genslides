from genslides.task.base import TaskDescription
from genslides.task.readfile import ReadFileTask

import os
from os import listdir
from os.path import isfile, join


class ReadFileParamTask(ReadFileTask):
    def __init__(self, task_info: TaskDescription, type="ReadFileParam") -> None:
        super().__init__(task_info, type)


    def readContentInternal(self):
        param_name = "read_folder"
        res, read_folder = self.getParam(param_name)
        if res and read_folder:
            res, pparam = self.getParamStruct(param_name)
            print("RF:", pparam)
            try:
                path = pparam["path_to_folder"]
                need_to_clean = pparam["clean_after"]
                onlyfiles = [f for f in listdir(path) if isfile(join(path, f))]
                text = ""
                for filename in onlyfiles:
                    filepath = path + filename

                    with open(filepath, 'r', encoding='utf-8') as f:
                        print("Read from file", filepath)
                        text += f.read() + "\n"
                    if need_to_clean:
                        os.remove(filepath)
                return True, text

            except Exception as e:
                print("Can\'t read params to read folder", e)
        param_name = "path_to_read"
        res, s_path = self.getParam(param_name)
        if res and os.path.isfile(s_path):
            with open(s_path, 'r') as f:
                text = f.read()
                return True, text
        return False, ""


    def loadContent(self, s_path, msg_trgs):
        res, text = self.readContentInternal()
        if res:
            msg_trgs[-1]["content"] = text
        return res, text



    def executeResponse(self):
        res, text = self.readContentInternal()
        if res:
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
 
