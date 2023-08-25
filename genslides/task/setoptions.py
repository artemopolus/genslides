from genslides.task.base import TaskDescription
from genslides.task.writetofile import WriteToFileTask

import json


class SetOptionsTask(WriteToFileTask):
    def __init__(self, task_info: TaskDescription, type="SetOptions") -> None:
        super().__init__(task_info, type)

    def executeResponse(self):
        try:
            self.params = json.loads(self.prompt)
        except:
            print("Can't load parameters")

    def updateIternal(self, input: TaskDescription = None):
        if self.parent:
            trg_list = self.parent.msg_list.copy()
        else:
            return
        if self.msg_list != trg_list:
            self.msg_list = trg_list
            self.saveJsonToFile(self.msg_list)


    def checkInput(self, input: TaskDescription = None):
        if input:
            self.prompt = input.prompt
            try:
                in_params = json.loads(self.prompt)
                if in_params != self.params:
                    self.params = in_params
                    print("Params changed update all")
                    self.forceCleanChildsChat()
            except:
                print("Can't load parameters")

            self.saveJsonToFile(self.msg_list)

    def update(self, input : TaskDescription = None):
        super().update(input)
        return json.dumps(self.params), "user", ""
    
    def getMsgInfo(self):
        return json.dumps(self.params, indent=1),"user",""
 
    def getParamFromExtTask(self, param_name):
        for param in self.params:
            for k,p in param.items():
                # print("k=",k,"p=",p)
                if param_name == k:
                    return True,self.parent, p

        return False, self.parent, None
 