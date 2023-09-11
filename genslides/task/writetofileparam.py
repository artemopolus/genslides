from genslides.task.base import TaskDescription, BaseTask
from genslides.task.writetofile import WriteToFileTask

import json

class WriteToFileParamTask(WriteToFileTask):
    def __init__(self, task_info: TaskDescription, type="WriteToFileParam") -> None:
        super().__init__(task_info, type)
        param_name = "path_to_write"
        res, path = self.getParam(param_name)
        if res:
            self.writepath = path

    def isInputTask(self):
        return False
    
    def getLastMsgAndParent(self) -> (bool, list, BaseTask):
        return False, [], self.parent

    def getRichPrompt(self) -> str:
        return self.writepath

    def executeResponse(self):
        # print("Exe resp write to file param")
        param_name = "path_to_write"
        res, path = self.getParam(param_name)
        path = self.findKeyParam(path)

        if self.is_freeze or len(self.msg_list) == 0 or res == False:
            return
        self.writepath = path
        ctrl = 'w'
        text = self.msg_list[len(self.msg_list) - 1]["content"]
        if res:
            res, pparam = self.getParamStruct(param_name)
            if res:
                if "write" in pparam and pparam["write"] == "append":
                    ctrl = 'a'
                if "write_dial" in pparam and pparam["write_dial"]:
                    # print("Get excluded task", pparam)
                    # print("Dial len=",len(self.msg_list))
                    if "excld_task" in pparam:
                        # print("Get msg excluded")
                        text = json.dumps(self.getMsgs(except_task=pparam["excld_task"]), indent=1)
                    else:
                        resp_json_out = self.msg_list.copy()
                        text = json.dumps(resp_json_out, indent=1)
        else:
            print("No struct param=",self.getName())


        with open(path, ctrl, encoding='utf8') as f:
            print(self.getName(),"write =", path)
            # print("Try to save=", text)
            f.write(text)

    def update(self, input : TaskDescription = None):
        super().update(input)
        return self.writepath, "user", ""

    def getMsgInfo(self):
        return self.writepath, "user", ""
 
    def getInfo(self, short = True) -> str:
        return self.getName()
 