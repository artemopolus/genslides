from genslides.task.text import TextTask
from genslides.task.base import TaskDescription
import pprint
from genslides.utils.largetext import SimpleChatGPT

import json

class CollectTask(TextTask):
    def __init__(self, task_info : TaskDescription, type = "Collect") -> None:
        super().__init__(task_info, type=type)

        self.is_freeze = True
        tmp_msg_list = self.msg_list.copy()
        msg_list_from_file = self.getResponseFromFile(tmp_msg_list)

        self.afterFileLoading()
        
        if len(msg_list_from_file) == 0:
            self.hasNoMsgAction()
            # self.updateCollectedMsgList(tmp_msg_list)
        else:
            print("Get list from file=", self.path)
            self.haveMsgsAction(msg_list_from_file)
            # self.setMsgList(msg_list_from_file)


        self.callback_link = []

    def afterFileLoading(self):
        pass

    def hasNoMsgAction(self):
        tmp_msg_list = self.msg_list.copy()
        self.updateCollectedMsgList(tmp_msg_list)

    def haveMsgsAction(self, msgs):
        self.setMsgList(msgs)



    def freezeTask(self):
        print("Freeze!")
        self.is_freeze = True
        for tsk_info in self.by_ext_affected_list:
            tsk_info.enabled = False

    def updateCollectedMsgList(self, trg_list : list):
            # print("update not frozen")
            last = {"content" : self.getRichPrompt(), "role" : self.prompt_tag}
            trg_list.append(last)
            if self.msg_list != trg_list:
                self.setMsgList( trg_list.copy())
                self.saveJsonToFile(self.msg_list)


    def checkParentsMsg(self):
            trg_list = self.parent.msg_list.copy()
            cur_list = self.msg_list.copy()
            cut = cur_list.pop()
            if cur_list != trg_list:
                trg_list.append(cut)
                self.setMsgList( trg_list)
                self.saveJsonToFile(self.msg_list)
                print("Freeze => parents msgs not equal target")
                self.freezeTask()
            return trg_list


    def update(self, input : TaskDescription = None):
        # print("Update collect_________________________________________________")
        # print("Collect",10*">>>>>>>>>>>")
        # print("Prompt=", self.getRichPrompt())
        trg_list = []
        if self.parent:
            trg_list = self.checkParentsMsg()
        else:
            trg_list = []
        
        if not self.is_freeze:
            self.updateCollectedMsgList(trg_list)
        super().update(input)
        print("CollectTask=",self.getName()," frozen=", self.is_freeze)
        if len(self.msg_list) > 0:
            out = self.msg_list[len(self.msg_list) - 1]
            return out["content"], out["role"]
        else:
            return "",""

    def createLinkToTask(self, task) -> TaskDescription:
        id = len(self.by_ext_affected_list)
        print("Create link to ", task.getName(),"id=", id)
        out = TaskDescription(method=self.affectedTaskCallback, id=id, parent=task , target=self)
        self.by_ext_affected_list.append(out)
        
        task.setLinkToTask(out)
        return super().createLinkToTask(task) 
    
    def getRichPrompt(self) -> str:
        res, param = self.getParamStruct('linkedfrom')
        text = ""
        if res:
            names = param['tasks']
            checkers = [t.getName() for t in self.getAffectingOnTask()]
            print('=================>>>>>>>>>>>>Check', names, '==',checkers)
            print(set(names) ==set(checkers))
            for name in names:
                print('Check',name,':',name in checkers)
            if set(names).difference(set(checkers)) == set():
                print('Yes')
                for t in names:
                    for intask in self.by_ext_affected_list:
                        if intask.parent.getName() == t:
                            text += intask.prompt + '\n'
            else:
                print('No')
            return text
        for task in self.by_ext_affected_list:
            text += task.prompt +"\n"
        return text

    def stdProcessUnFreeze(self, input=None):
        # print("1 frozen=", self.is_freeze)
        if self.parent:
            # print("parent frozen=",self.parent.is_freeze)
            pass
        if self.is_freeze:
            to_unfreeze = False
            if self.parent and not self.parent.is_freeze:
                to_unfreeze = True
            elif not self.parent and self.is_freeze:
                to_unfreeze = True
            if to_unfreeze:
                for tsk_info in self.by_ext_affected_list:
                    print("Inp par=", tsk_info.parent.getName(),"=",tsk_info.enabled)
                    if not tsk_info.enabled:
                        return
                # print("Unfreeze")
                self.is_freeze = False
                print("Task",self.getName(),"is freeze:",self.is_freeze)

        else:
            for tsk_info in self.by_ext_affected_list:
                # print("Inp par=", tsk_info.parent.getName(),"=",tsk_info.enabled)
                if not tsk_info.enabled:
                    print("Freeze from children")
                    self.freezeTask()
                    return
            # print("1 frozen=", self.is_freeze)
  

    def affectedTaskCallback(self, input : TaskDescription):
        print("From ", input.parent.getName(), " to ", self.getName())
        if input and input.stepped:
            found = False
            for cl in self.callback_link:
                if cl["pt"] == input.parent:
                    cl["used"] = False
                    found = True
                    break
            if not found:
                self.callback_link.append({"pt":input.parent,"used": False})
                found = True
            if found:
                self.resetTreeQueue()
        for tsk_info in self.by_ext_affected_list:
            if input.id == tsk_info.id:
                tsk_info.prompt = input.prompt
                tsk_info.enabled = input.enabled
                print("Enabling=", tsk_info.id,"=",tsk_info.enabled)

        out = super().affectedTaskCallback(input)
        self.stdProcessUnFreeze()
        if input and input.stepped:
            info = TaskDescription(prompt=self.getLastMsgContent(), prompt_tag=self.getLastMsgRole(),stepped=input.stepped)
            self.update(info)
        else:
            self.update()
    
    
    def findNextFromQueue(self):
        res = super().findNextFromQueue()
        if res:
            return res
        for cl in self.callback_link:
            if cl["used"] == False:
                cl["used"] = True
                return cl["pt"].findNextFromQueue()
        return None



    def removeLinkToTask(self):
        self.prompt = ""
        self.update()
        self.freezeTask()
        super().removeLinkToTask()
        self.saveJsonToFile(self.msg_list)
 
    def getMsgInfo(self):
        if len(self.msg_list) > 0:
            out = self.msg_list[- 1]
            return "", out["role"],out["content"]
        else:
            return "", self.prompt_tag, ""    
    
    def whenParentRemoved(self):
        super().whenParentRemoved()
        self.removeLinkToTask()



    def getInfo(self, short = True) -> str:
        out = ""
        for task in self.by_ext_affected_list:
            out += task.parent.getName()
        return out
    
    def setParamStruct(self, param):
        if 'type' in param and param['type'] == 'linkedfrom':
            param['tasks'] = [t.getName() for t in self.getAffectingOnTask()]
        return super().setParamStruct(param)
