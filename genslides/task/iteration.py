from genslides.task.text import TextTask
from genslides.task.base import TaskDescription, BaseTask
from genslides.utils.largetext import SimpleChatGPT

import json


class IterationTask(TextTask):
    def __init__(self, task_info: TaskDescription, type="Iteration") -> None:
        super().__init__(task_info, type)
        self.dt_states = {"No data":0, "Ready": 1, "Processing" : 2, "Done": 3}
        self.dt_cur = self.dt_states['No data']
        self.iter_data = None
        self.iter_type = "None"
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
    def getInfo(self, short = True) -> str:
        return self.getName()
    
    def isInputTask(self):
        return False
    
    def getLastMsgAndParent(self) -> (bool, list, BaseTask):
        return False, [], self.parent


    def addChild(self, child):
        self.iter_end.append({"child": child, "targets" : None, "freeze": False})
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
        if self.parent and self.iter_data != None and len(self.iter_data) > 0:
            return self.iter_data[0]
        return "Nothing to iterate"
    
    def parseJsonLastMsg(self):
        print("Parse json last message")
        indata = self.parent.msg_list[-1]["content"]
        lst_msg_jsn = json.loads(indata)
        if "type" in lst_msg_jsn:
            it_type = lst_msg_jsn["type"]
            values = []
            if it_type == "iteration" and "data" in lst_msg_jsn:
                values = lst_msg_jsn["data"]
            elif it_type == "for":
                try:
                    values = [i for i in range(lst_msg_jsn["start"],lst_msg_jsn["stop"],lst_msg_jsn["step"])]
                except Exception as e:
                    print("Can\'t read for params=",e)
            else:
                print("Unknown type of iterartion")
                return
            if self.iter_data and self.iter_type == it_type:
                is_not_found = False
                for val in values:
                    if val not in self.iter_data:
                        print("Not found=",val)
                        is_not_found = True
                
                if not is_not_found:
                    print("No changes found")
                    return
            if it_type == "iteration" or it_type == "for":
                self.updateParam("index", str(0))
                if len(values) > 0:
                    self.updateParam("iterable", values[0])
                else:
                    self.updateParam("iterable", "0")

                # print("Ready to iterate")
            else:
                print("No available iteration type")
                return
            try:
                self.cond_max_spent = lst_msg_jsn["max_spent"]
                self.cond_max_iter = lst_msg_jsn["max_iter"]
                self.cond_max_tkns = lst_msg_jsn["max_tkns"]
                self.cond_on = True
            except:
                self.cond_on = False
                print("Can\'t read conditions")

            self.iter_data = values
            self.iter_type = it_type
            self.dt_cur = self.dt_states["Ready"]
            print("iteration setup:\ntype:",self.iter_type,"iter on:", self.iter_data)
        else:
            print("Incorrect format of target message:", indata)
 



    def executeResponse(self):
        # try:
            if self.dt_cur == self.dt_states["No data"]:
                self.parseJsonLastMsg()
            elif self.dt_cur == self.dt_states["Done"]:
                self.parseJsonLastMsg()
        # except Exception as e:
            # print("Can\'t find json data")
            # self.dt_cur = self.dt_states["No data"]
            self.saveJsonToFile(self.msg_list2)


    def checkParentMsgList(self, update = False) -> bool:

        if self.parent:
            trg_list = self.parent.msg_list.copy()
        else:
            trg_list = []
        if self.msg_list2 != trg_list:
            if update:
                self.msg_list2 = trg_list
            return False
        return True

    def forceCleanChat(self):
        if len(self.msg_list2) > 1:
            self.msg_list2 = []
 

    def update(self, input: TaskDescription = None):
        mydict = self.dt_states
        print("State[",self.getName(),"]=",list(mydict.keys())[list(mydict.values()).index(self.dt_cur)])

        if not self.checkParentMsgList(True):
            print("Prev msg was changed: start iteration")
            self.iter_data = None

        self.executeResponse()
        # print("State:",list(mydict.keys())[list(mydict.values()).index(self.dt_cur)])

        if self.is_freeze:
            print("First run")
            super().update(input)
 
        if not self.is_freeze:
            print("Iteration task is not freeze")
            if self.dt_cur == self.dt_states["Ready"]:
                self.dt_cur = self.dt_states["Processing"]
                num_iter = len(self.iter_data)
                res, max_num_iter = self.getParam("max_num_iter")
                if res:
                    num_iter = int(max_num_iter)
                print(10*"====")
                print("Start Iteration")
                print(10*"====")
                for index in range(num_iter):
                    print("Itaration ====================>", index)
                    value = self.iter_data[index]
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
                    if self.checkEndConditions(index,num_iter):
                        break
        # super().update(input)

        return self.getRichPrompt(), "user", "Numbers"
    
    def startConditions(self):
        if self.cond_on:
            chat = SimpleChatGPT()
            if self.cond_max_spent > 0:
                self.cond_strt_spent = chat.getSpentToday()
        
    def checkEndConditions(self, index, num_iter)-> bool:
        if self.cond_on:
            chat = SimpleChatGPT()
            delta = chat.getSpentToday - self.cond_strt_spent
            if self.cond_max_spent > 0 and delta > self.cond_max_spent:
                print("Condition: spent=", delta)
                return False
            if self.cond_max_iter > 0 and index < self.cond_max_iter - 1:
                
                print("Condition: max iter=", index)
                return False
            if self.cond_max_tkns > 0:
                for ie in self.iter_end:
                    msgs = ie["targets"][0].getMsgs()
                    tokens = chat.getTokensCountFromChat(msgs)
                    if tokens > self.cond_max_tkns:
                        print("Condition: tokens=", tokens)
                        return False
        else:
            if index < num_iter - 1:
                return False
        return True


    def stdProcessUnFreeze(self, input=None):
        pass

    def freezeIterEndTask(self) -> bool:
        mydict = self.dt_states
        if self.dt_cur == self.dt_states["Done"]:
            return False
        elif self.dt_cur == self.dt_states["Ready"]:
            pass
        print("Make task unfeeze, state=",list(mydict.keys())[list(mydict.values()).index(self.dt_cur)])
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
    def getInfo(self, short = True) -> str:
        return self.getName()

    def isInputTask(self):
        return False
    

    def getLastMsgAndParent(self) -> (bool, list, BaseTask):
        return False, [], self.parent


    
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
                    if task.parent.getType() == "Iteration" and task.parent.closeIter(out_task_list):
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
                print("Freeze iter end")
                self.freezeTask()
            else:
                print("Now update next task after iter end")
                self.unfreezeTask()
                self.copyIterationMsg()
        else:
            print("No iteration start task")
        
        super().update()
        return "IterEnd", "user", "IterEnd"

    def stdProcessUnFreeze(self, input=None):
        pass

    def beforeRemove(self):
        if self.iter_start:
            self.iter_start.openIter(self)
        super().beforeRemove()
