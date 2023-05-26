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
        print("list from file=",msg_list_from_file)
        del tmp_msg_list
        print("==================>>>>>>>>>>>", pprint.pformat( self.msg_list))
        
        if len(msg_list_from_file) == 0:
            self.msg_list.append(pair)
            self.saveJsonToFile(self.msg_list)
        else:
            self.msg_list = msg_list_from_file
            print("Get list from file=", self.path)



    # def completeTask(self):
    #     self.is_solved = True
    #     return True

    def update(self, input : TaskDescription = None):
        print("Update collect_________________________________________________")
        # print("==================>>>>>>>>>>>", pprint.pformat( self.msg_list))
        print("Collect",10*">>>>>>>>>>>")
        # print("Prompt=", self.getRichPrompt())
        if self.parent:
            trg_list = self.parent.msg_list.copy()
        else:
            trg_list = []
        
        # self.msg_list[len(self.msg_list) - 1]["content"] = self.getRichPrompt()
        last = self.msg_list[- 1].copy()
        last["content"] = self.getRichPrompt()
        trg_list.append(last)
        if self.msg_list != trg_list:
            self.msg_list = trg_list.copy()
            self.saveJsonToFile(self.msg_list)
        super().update(input)
        out = self.msg_list[len(self.msg_list) - 1]
        return out["content"], out["role"]

    def createLinkToTask(self, task) -> TaskDescription:
        id = len(self.by_ext_affected_list)
        out = TaskDescription(method=self.affectedTaskCallback, id=id, parent=task )
        self.by_ext_affected_list.append(out)
        
        task.setLinkToTask(out)
        return super().createLinkToTask(task) 
    
    def getRichPrompt(self) -> str:
        text = ""
        # print("affect count=",len(self.by_ext_affected_list))
        for task in self.by_ext_affected_list:
            text += task.prompt
            # print("text=",task.prompt)
            # print("text=",task.parent.prompt)
        return text

    
    def affectedTaskCallback(self, input : TaskDescription):
        for task in self.by_ext_affected_list:
            if input.id == task.id:
                task.prompt = input.prompt
        # self.prompt = input.prompt
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
        super().removeLinkToTask()
  