from genslides.task.text import TextTask
from genslides.task.base import TaskDescription
import pprint
from genslides.utils.largetext import SimpleChatGPT



class CollectTask(TextTask):
    def __init__(self, task_info : TaskDescription, type = "Collect") -> None:
        super().__init__(task_info, type=type)

        self.is_freeze = True
        tmp_msg_list = self.msg_list.copy()
        # tmp_msg_list.append(pair)
        msg_list_from_file = self.getResponseFromFile(tmp_msg_list)
        # print("list from file=",msg_list_from_file)
        # del tmp_msg_list
        
        if len(msg_list_from_file) == 0:
            self.updateCollectedMsgList(tmp_msg_list)
        else:
            self.msg_list = msg_list_from_file
            print("Get list from file=", self.path)





    # def completeTask(self):
    #     self.is_solved = True
    #     return True

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
                self.msg_list = trg_list.copy()
                self.saveJsonToFile(self.msg_list)


    def checkParentsMsg(self):
            trg_list = self.parent.msg_list.copy()
            cur_list = self.msg_list.copy()
            cut = cur_list.pop()
            if cur_list != trg_list:
                self.msg_list = trg_list
                self.msg_list.append(cut)
                self.saveJsonToFile(self.msg_list)
                print("Freeze from checking")
                self.freezeTask()
            return trg_list


    def update(self, input : TaskDescription = None):
        # print("Update collect_________________________________________________")
        # print("Collect",10*">>>>>>>>>>>")
        # print("Prompt=", self.getRichPrompt())
        trg_list = []
        if self.parent:
            # print("==================>>>>>>>>>>>", pprint.pformat( self.parent.msg_list))
            trg_list = self.checkParentsMsg()
        else:
            trg_list = []
        
        # self.msg_list[len(self.msg_list) - 1]["content"] = self.getRichPrompt()
        # last = self.msg_list[- 1].copy()
        # last["content"] = self.getRichPrompt()
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
        out = TaskDescription(method=self.affectedTaskCallback, id=id, parent=task )
        self.by_ext_affected_list.append(out)
        
        task.setLinkToTask(out)
        return super().createLinkToTask(task) 
    
    def getRichPrompt(self) -> str:
        text = ""
        # print("affect count=",len(self.by_ext_affected_list))
        for task in self.by_ext_affected_list:
            text += task.prompt +"\n"
            # print("text=",task.prompt)
            # print("text=",task.parent.prompt)
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
        for tsk_info in self.by_ext_affected_list:
            if input.id == tsk_info.id:
                tsk_info.prompt = input.prompt
                tsk_info.enabled = input.enabled
                print("Enabling=", tsk_info.id,"=",tsk_info.enabled)

        out = super().affectedTaskCallback(input)
        self.stdProcessUnFreeze()
        self.update()
    #     trg_list = []
    #     if self.parent:
    #         trg_list = self.parent.msg_list.copy()
    #     old_msg_list = self.msg_list.copy()
    #     last = old_msg_list.pop()
    #     last["content"] = self.getRichPrompt()
    #     trg_list.append(last)
    #     if self.msg_list != trg_list:

        return out
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
