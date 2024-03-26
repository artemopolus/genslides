from genslides.task.response import ResponseTask
from genslides.task.text import TextTask
from genslides.task.base import TaskDescription

import os
import re
import json
from os import listdir
from os.path import isfile, join
import pprint



class ReadFileTask(ResponseTask):
    def __init__(self, task_info: TaskDescription, type="ReadFile") -> None:
        super().__init__(task_info, type)
        # print(40*"====")
        # print("Hello i am read task=", self.getName())
        # print(40*"====")
        # param_name = "path_to_read"
        # if param_name in self.params:
        #     path = self.params[param_name]
        #     if os.path.isfile(path):
        #         with open(path, 'r') as f:
        #             print("path_to_read =", path)
        #             text = f.read()
        #             if text != self.msg_list[-1]["content"]:
        #                 self.msg_list[-1]["content"] = text
        self.saveJsonToFile(self.msg_list)

    def onEmptyMsgListAction(self):
        if self.is_freeze:
            self.msg_list.append({"role": self.prompt_tag, "content": ""})
        else:
            self.executeResponse()

    def onExistedMsgListAction(self, msg_list_from_file):
        # print("t=",temperature)
        param_name = "path_to_read"
        res, val = self.getParam(param_name)
        if res:
            self.updateParam(param_name, val)

        self.msg_list = msg_list_from_file
        # print("Get list from file=", self.path)


    def getResponseFromFile(self, msg_list, remove_last = True):
        # print("_______________Get from read task")

        mypath = self.manager.getPath()
        onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
        trg_file = self.filename + self.manager.getTaskExtention()
        # for file in onlyfiles:
        if trg_file in onlyfiles:
            file = trg_file
            if file.startswith(self.getType()):
                path = os.path.join( mypath, file) 
                try:
                    # print(path)
                    with open(path, 'r') as f:
                        rq = json.load(f)
                    if 'chat' in rq:
                        msg_trgs = rq['chat'].copy()
                        # if remove_last:
                            # msg_trgs.pop()

                        
                        self.path = path
                        self.setName( file.split('.')[0])
                        if 'params' in rq:
                            self.setParamIternal(rq['params'])

                        param_name = "path_to_read"
                        # print('Get params')
                        s_path = None
                        for param in self.params:
                            if param_name in param:
                                s_path = param[param_name]
                                self.prompt = s_path
                        if s_path:
                            res, msg_trgs = self.loadContent(s_path, msg_trgs)
                            if res:
                                return msg_trgs
                except json.JSONDecodeError:
                    pass
        return []
    
    def loadContent(self, s_path, msg_trgs):
        if os.path.isfile(s_path):
            with open(s_path, 'r') as f:
                text = f.read()
                msg_trgs[-1]["content"] = text
                return True, msg_trgs
        return False, msg_trgs

    def getRichPrompt(self) -> str:
        if self.parent:
            return self.msg_list[-1]["content"]
        return self.prompt



    def executeResponse(self):
        # print('Exe resp read')
      #   str = "J:\WorkspaceFast\genslides\examples\05table_parts_slides1_req.txt"
        path = self.getRichPrompt()
        if os.path.isfile(path):
            param_name = "path_to_read"
            self.updateParam(param_name, path)
            with open(path, 'r') as f:
                print("path_to_read =", path)
                text = f.read()
                self.msg_list.append({
                    "role": self.prompt_tag,
                    "content": text
                })
    def forceCleanChat(self):
        if len(self.msg_list) > 0:
            self.msg_list = []



