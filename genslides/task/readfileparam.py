from genslides.task.base import TaskDescription, BaseTask
from genslides.task.readfile import ReadFileTask

import os, json
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
        if res:
            rres, pparam = self.getParamStruct(param_name)
            if rres:
                if "role" in pparam:
                    self.prompt_tag = pparam["role"]
                else:
                    self.prompt_tag = "user"
                if "read_dial" in pparam and pparam["read_dial"] and os.path.isfile(s_path):
                    with open(s_path, 'r') as f:
                        try:
                            rq = json.load(f)
                            self.msg_list = rq
                        except ValueError as e:
                            print("json error type=", type(e))
                            self.msg_list = []
                        print(self.getName(),"read =", s_path,"msg=",len(self.msg_list))
    
                    return False, ""
                elif "read_part" in pparam and pparam["read_part"] and "start_part" in pparam and "max_part" in pparam:
                    if os.path.isfile(s_path):
                        with open(s_path, 'r',encoding='utf-8') as f:
                            text = f.read()
                        start = int(pparam["max_part"])
                        stop = start + int(pparam["max_part"])
                        if len(text) > stop*8:
                            med = int((len(text) - stop)/2)
                            return True, "This is parts of file:\n\n" + text[start:stop] + "...\n\n..." + text[med:med + stop]  + "...\n\n..." + text[len(text) - stop :]
                        if len(text) > stop*4:
                            return True, "This is parts of file:\n\n" + text[start:stop] + "...\n\n..." + text[len(text) - stop :]
                        if len(text) > stop:
                            return True, "This is part of file:\n\n" + text[start:stop]
                        if 'delete' in pparam and pparam['delete']:
                            os.remove(s_path)
                            print('File bt path',s_path,'is removed')

                        return True, text
                        

        if res and os.path.isfile(s_path):
            with open(s_path, 'r', encoding='utf-8') as f:
                text = f.read()
                return True, text
        return False, "No file found"


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
 
    def getLastMsgAndParent(self) -> (bool, list, BaseTask):
        val = []
        rres, pparam = self.getParamStruct("path_to_read")
        if rres and "read_dial" in pparam and pparam["read_dial"]:
            for msg in self.msg_list:
                val.append({"role":msg["role"],"content":self.findKeyParam(msg["content"])})
            return True, val, None
        else:
            val = [{"role":self.getLastMsgRole(), "content": self.findKeyParam(self.getLastMsgContent())}]
            return True, val, self.parent

