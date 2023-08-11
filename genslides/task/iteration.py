from genslides.task.text import TextTask
from genslides.task.base import TaskDescription

import json


class IterationTask(TextTask):
    def __init__(self, task_info: TaskDescription, type="Iteration") -> None:
        super().__init__(task_info, type)
        self.dt_states = {"No data":0, "Ready": 1, "Processing" : 2, "Done": 3}
        self.dt_cur = self.dt_states['No data']
        self.array_list = None
        tmp_msg_list = self.msg_list.copy()
        msg_list_from_file = self.getResponseFromFile(tmp_msg_list, False)
        del tmp_msg_list
        if len(msg_list_from_file) == 0 and not self.is_freeze:
            pass
        else:
            self.msg_list = msg_list_from_file
        self.msg_list2 = self.msg_list.copy()
        self.msg_list = []
        self.executeResponse()
        self.is_freeze = True
        self.iter_end = []
    
    def addChild(self, child):
        self.iter_end.append({"child": child, "targets" : None})
        super().addChild(child)
    
    def closeIter(self, task_array) ->bool:
        for index in range(len(task_array)):
            print(index, ". ", task_array[index].getName())
        for ie in self.iter_end:
            if ie["child"] == task_array[-1]:
                print("Found")
                ie["targets"] = task_array
                return True
        return False

    def openIter(self, task):
        tmp = None
        for ie in self.iter_end:
            if ie["child"] == task:
                tmp = ie
        if tmp is not None:
            self.iter_end.remove(tmp)
        self.freezeTask()

    def resetIter(self):
        self.dt_cur = self.dt_states["No data"]

    def saveJsonToFile(self, msg_list):
        super().saveJsonToFile(self.msg_list2)

    def getRichPrompt(self) -> str:
        if self.parent and self.array_list != None and len(self.array_list) > 0:
            return self.array_list[0]
        return "Nothing to iterate"

    def executeResponse(self):
        try:
            if self.dt_cur == self.dt_states["No data"]:
                values = json.loads(self.parent.msg_list[-1]["content"])
                self.array_list = values
                self.updateParam("index", str(0))
                self.updateParam("iterable", values[0])
                # print("Ready to iterate")
                self.dt_cur = self.dt_states["Ready"]
            elif self.dt_cur == self.dt_states["Done"]:
                values = json.loads(self.parent.msg_list[-1]["content"])
                is_not_found = False
                for val in values:
                    if val not in self.array_list:
                        print("Not found=",val)
                        is_not_found = True
                # if self.array_list != values:
                if is_not_found:
                    print("old=", self.array_list)
                    print("new=", values)
                    self.array_list = values
                    self.updateParam("index", str(0))
                    self.updateParam("iterable", values[0])
                    print("Ready to iterate")
                    self.dt_cur = self.dt_states["Ready"]
        except Exception as e:
            print("Can\'t find json data")
            self.dt_cur = self.dt_states["No data"]
        self.saveJsonToFile(self.msg_list2)

    def update(self, input: TaskDescription = None):
        mydict = self.dt_states
        print("State:",list(mydict.keys())[list(mydict.values()).index(self.dt_cur)])
        if self.parent:
            trg_list = self.parent.msg_list.copy()
        else:
            trg_list = []
        if self.msg_list2 != trg_list:
            self.msg_list2 = trg_list
        self.executeResponse()
        print("State:",list(mydict.keys())[list(mydict.values()).index(self.dt_cur)])

        if not self.is_freeze:
            if self.dt_cur == self.dt_states["Ready"]:
                self.dt_cur = self.dt_states["Processing"]
                num_iter = len(self.array_list)
                # num_iter = 2
                print("Unreeze task")
                super().update(input)
                print(10*"====")
                print("Start Iteration")
                print(10*"====")
                for index in range(num_iter):
                    # print("====================>", index)
                    value = self.array_list[index]
                    self.updateParam("index", str(index))
                    self.updateParam("iterable", value)
                    if index == num_iter - 1:
                        self.dt_cur = self.dt_states["Done"]
                    print(10*"====")
                    print("Clear iter=", index)
                    print(10*"====")
                    for ie in self.iter_end:
                        for trg in ie["targets"]:
                            trg.forceCleanChat()
                    super().update(input)
        super().update(input)

        return self.getRichPrompt(), "user", "Numbers"

    def stdProcessUnFreeze(self, input=None):
        pass

    def freezeIterEndTask(self) -> bool:
        mydict = self.dt_states
        print("State==================================",list(mydict.keys())[list(mydict.values()).index(self.dt_cur)])
        if self.dt_cur == self.dt_states["Done"]:
            return False
        elif self.dt_cur == self.dt_states["Ready"]:
            pass
        self.unfreezeTask()
        return True




class IterationEndTask(TextTask):
    def __init__(self, task_info: TaskDescription, type="IterationEnd") -> None:
        super().__init__(task_info, type)
        tmp_msg_list = self.msg_list.copy()
        msg_list_from_file = self.getResponseFromFile(tmp_msg_list, False)
        del tmp_msg_list
        if len(msg_list_from_file) == 0 and not self.is_freeze:
            pass
        else:
            self.msg_list = msg_list_from_file

        self.iter_start = None
        self.msg_list2 = self.msg_list.copy()
        self.msg_list = []
        self.executeResponse()

    def saveJsonToFile(self, msg_list):
        super().saveJsonToFile(self.msg_list2)

 
    def getRichPrompt(self) -> str:
        if self.iter_start:
            return self.iter_start.getName()
        return "No iter found"
    
    def copyIterationMsg(self):
        if (self.iter_start):
            self.msg_list = self.iter_start.msg_list2.copy()

    def executeResponse(self):
        if self.iter_start == None:
            index = 0
            task = self
            out_task_list = []
            while(index < 1000):
                if task.parent == None:
                    print("No iterator found")
                    break 
                else:
                    out_task_list.append(task)
                    if task.parent.type == "Iteration" and task.parent.closeIter(out_task_list):
                        self.iter_start = task.parent
                        break
                    else:
                        task = task.parent
                index += 1
        self.saveJsonToFile(self.msg_list)
        
    def update(self, input: TaskDescription = None):
        if self.parent:
            if len(self.msg_list2) == len(self.parent.msg_list):
                need_to_reset = False
                for i in range(len(self.parent.msg_list)):
                    msg = self.parent.msg_list[i]
                    if msg["role"] == "user":
                        if msg["content"] != self.msg_list2[i]["content"]:
                            need_to_reset = True
                            break
                if need_to_reset:
                    self.msg_list2 = self.parent.msg_list.copy()
                    if self.iter_start:
                        self.iter_start.resetIter()
                   
        # if self.parent and self.parent.msg_list != self.msg_list2:
        #     self.msg_list2 = self.parent.msg_list.copy()
        #     if self.iter_start:
        #         self.iter_start.resetIter()
        self.executeResponse()
        if self.iter_start:
            if self.iter_start.freezeIterEndTask():
                self.freezeTask()
            else:
                print("Now update next task")
                self.unfreezeTask()
                self.copyIterationMsg()
        
        super().update()
        return "IterEnd", "user", "IterEnd"

    def stdProcessUnFreeze(self, input=None):
        pass

    def beforeRemove(self):
        if self.iter_start:
            self.iter_start.openIter(self)
        super().beforeRemove()
