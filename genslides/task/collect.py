from genslides.task.text import TextTask
from genslides.task.base import TaskDescription
import pprint
from genslides.utils.largetext import SimpleChatGPT



class CollectTask(TextTask):
    def __init__(self, task_info : TaskDescription) -> None:
        super().__init__(task_info, "Collect")
        # self.prompt = ""
        pair = {}
        pair["role"] = task_info.prompt_tag
        pair["content"] = self.getRichPrompt()

        tmp_msg_list = self.msg_list.copy()
        # tmp_msg_list.append(pair)
        msg_list_from_file = self.getResponseFromFile(tmp_msg_list)
        # print("list from file=",msg_list_from_file)
        del tmp_msg_list
        # print("==================>>>>>>>>>>>", pprint.pformat( self.msg_list))
        
        if len(msg_list_from_file) == 0:
            self.msg_list.append(pair)
            self.saveJsonToFile(self.msg_list)
        else:
            self.msg_list = msg_list_from_file
            print("Get list from file=", self.path)


        self.is_freeze = True



    # def completeTask(self):
    #     self.is_solved = True
    #     return True

    def freezeTask(self):
        print("Freeze!")
        self.is_freeze = True
        for tsk_info in self.by_ext_affected_list:
            tsk_info.enabled = False

    def update(self, input : TaskDescription = None):
        # print("Update collect_________________________________________________")
        # print("==================>>>>>>>>>>>", pprint.pformat( self.msg_list))
        # print("Collect",10*">>>>>>>>>>>")
        # print("Prompt=", self.getRichPrompt())
        if self.parent:
            trg_list = self.parent.msg_list.copy()
            cur_list = self.msg_list.copy()
            cut = cur_list.pop()
            if cur_list != trg_list:
                self.msg_list = trg_list
                self.msg_list.append(cut)
                self.saveJsonToFile(self.msg_list)
                self.freezeTask()
        else:
            trg_list = []
        
        # self.msg_list[len(self.msg_list) - 1]["content"] = self.getRichPrompt()
        # last = self.msg_list[- 1].copy()
        # last["content"] = self.getRichPrompt()
        if not self.is_freeze:
            print("update not frozen")
            last = {"content" : self.getRichPrompt(), "role" : self.prompt_tag}
            trg_list.append(last)
            if self.msg_list != trg_list:
                self.msg_list = trg_list.copy()
                self.saveJsonToFile(self.msg_list)
        out = self.msg_list[len(self.msg_list) - 1]
        super().update(input)
        print("CollectTask=",self.getName()," frozen=", self.is_freeze)
        return out["content"], out["role"]

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

    def stdProcessUnFreeze(self):
        print("1 frozen=", self.is_freeze)
        if self.is_freeze:
            to_unfreeze = False
            if self.parent and not self.parent.is_freeze:
                to_unfreeze = True
            elif not self.parent and self.is_freeze:
                to_unfreeze = True
            if to_unfreeze:
                for tsk_info in self.by_ext_affected_list:
                    # print("Inp par=", tsk_info.parent.getName(),"=",tsk_info.enabled)
                    if not tsk_info.enabled:
                        return
                # print("Unfreeze")
                self.is_freeze = False

        else:
            for tsk_info in self.by_ext_affected_list:
                # print("Inp par=", tsk_info.parent.getName(),"=",tsk_info.enabled)
                if not tsk_info.enabled:
                    self.freezeTask()
                    return
            print("1 frozen=", self.is_freeze)
  

    def affectedTaskCallback(self, input : TaskDescription):
        print("From ", input.parent.getName(), " to ", self.getName())
        for tsk_info in self.by_ext_affected_list:
            if input.id == tsk_info.id:
                tsk_info.prompt = input.prompt
                tsk_info.enabled = input.enabled
                print("Enabling=", tsk_info.id,"=",tsk_info.enabled)

        out = super().affectedTaskCallback(input)
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
 
    def getMsgInfo(self):
        out = self.msg_list[- 1]
        return "", out["role"],out["content"]
    def whenParentRemoved(self):
        super().whenParentRemoved()
        self.removeLinkToTask()



    def getInfo(self, short = True) -> str:
        out = ""
        for task in self.by_ext_affected_list:
            out += task.parent.getName()
        return out
