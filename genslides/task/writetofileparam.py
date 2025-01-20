from genslides.task.base import TaskDescription, BaseTask
from genslides.task.writetofile import WriteToFileTask
import genslides.utils.writer as writer
from genslides.utils.loader import Loader
import genslides.utils.savedata as sv

import os
import json
from pathlib import Path

class WriteToFileParamTask(WriteToFileTask):
    def __init__(self, task_info: TaskDescription, type="WriteToFileParam") -> None:
        super().__init__(task_info, type)
        param_name = "path_to_write"
        res, path = self.getParam(param_name)
        if res:
            self.writepath = path
        else:
            self.writepath = ''

    def isInputTask(self):
        return False
    

    def getRichPrompt(self) -> str:
        return self.writepath
    
    def checkAnotherOptions(self) -> bool:
        param_name = "path_to_write"
        res, pparam = self.getParamStruct(param_name)
        if res:
            op = 'always_update'
            if op in pparam and pparam[op]:
                return True
        return False
    
    def executeResponse(self):
        # print("Exe resp write to file param")
        param_name = "path_to_write"
        res, path = self.getParam(param_name)
        # print(path)
        path = self.findKeyParam(path)
        # print(path)
        if path == "":
            return
        path = Loader.getUniPath(path)
        # print(path)

        if self.is_freeze or len(self.msg_list) == 0 or res == False:
            return
        self.writepath = path
        ctrl = 'w'
        # text = self.findKeyParam( self.getLastMsgContent() )
        task_msgs = self.getMsgs()
        text = task_msgs[-1]['content'] if len(task_msgs) > 0 else ''
        if res:
            res, pparam = self.getParamStruct(param_name)
            if res:
                if 'input' in pparam:
                    text  = self.findKeyParam(pparam['input'])
                
                if "write" in pparam:
                    if pparam["write"] == "append":
                        ctrl = 'a'
                    elif pparam["write"] == "replace" \
                        and pparam["text_to_replace"] != "" \
                        and pparam["source_to_edit"] != "":
                        if pparam["replace_type"] == "std":
                            source = self.findKeyParam(pparam["source_to_edit"])
                            old_text = self.findKeyParam(pparam["text_to_replace"])
                            text = source.replace(old_text, text)
                        elif pparam["replace_type"] == "json":
                            try:
                                info = Loader.loadJsonFromText(pparam["text_to_replace"])
                                indexes = range(start= info['start'], stop=info['stop'])
                                source = self.findKeyParam(pparam["source_to_edit"])
                                lines = source.split("\n")
                                restext = ''
                                inserted = False
                                for idx, line in enumerate(lines):
                                    if idx in indexes:
                                        if not inserted:
                                            restext += text
                                    else:
                                        restext += line
                                text = restext
                            except Exception as e:
                                print('Json replace error:',e)
                # if "del_msgs" in pparam:
                #     in_val = pparam["del_msgs"]
                #     if isinstance(in_val, int):
                #         text = self.getMsgByIndex(in_val)
                # if "write_dial" in pparam and pparam["write_dial"]:
                #     # print("Get excluded task", pparam)
                #     # print("Dial len=",len(self.msg_list))
                #     if "excld_task" in pparam:
                #         # print("Get msg excluded")
                #         text = json.dumps(self.getMsgs(except_task=pparam["excld_task"]), indent=1)
                #     else:
                #         # resp_json_out = self.msg_list.copy()
                #         resp_json_out = self.getMsgs()
                #         text = json.dumps(resp_json_out, indent=1)
        else:
            print("No struct param=",self.getName())

        print(self.getName(),"write to", path)
        task_param = {
            "type":self.getType(),
            "resfilepath": path,
            "time": sv.getTimeForSaving()
        }
        self.setParamStruct(task_param)
        writer.writeToFile(path, text, ctrl)
       
    def update(self, input : TaskDescription = None):
        super().update(input)
        return self.writepath, "user", ""

    def getMsgInfo(self):
        return self.writepath, "user", ""
 
    def getInfo(self, short = True) -> str:
        return self.getName()
    

