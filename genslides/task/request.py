from genslides.task.text import TextTask
from genslides.task.base import TaskDescription
import pprint

class RequestTask(TextTask):
    def __init__(self, task_info: TaskDescription, ) -> None:
        super().__init__(task_info, "Request")
        pair = {}
        pair["role"] = task_info.prompt_tag
        pair["content"] = self.getRichPrompt()

        tmp_msg_list = self.msg_list.copy()
        tmp_msg_list.append(pair)
        msg_list_from_file = self.getResponseFromFile(tmp_msg_list, remove_last=False)
        del tmp_msg_list
        print("==================>>>>>>>>>>>", pprint.pformat( self.msg_list))
        
        if len(msg_list_from_file) == 0:
            self.msg_list.append(pair)
            self.saveJsonToFile(self.msg_list)
        else:
            self.msg_list = msg_list_from_file
            print("Get list from file=", self.path)

    def update(self, input : TaskDescription = None):
        if self.parent:
            trg_list = self.parent.msg_list.copy()
        else:
            trg_list = []
        if input == None:
            last = self.msg_list[len(self.msg_list) - 1]
            trg_list.append(last)
        else:
            pair = {}
            pair["role"] = input.prompt_tag
            pair["content"] = input.prompt
            trg_list.append(pair)
        if self.msg_list != trg_list:
            self.msg_list = trg_list
            self.saveJsonToFile(self.msg_list)
        super().update()
        out = self.msg_list[len(self.msg_list) - 1]
        return out["content"], out["role"]

