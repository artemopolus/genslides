from genslides.task.text import TextTask
from genslides.task.base import TaskDescription


import os


class WriteToFileTask(TextTask):
    def __init__(self, task_info: TaskDescription, type="WriteToFile") -> None:
        super().__init__(task_info, type)
        tmp_msg_list = self.msg_list.copy()
        msg_list_from_file = self.getResponseFromFile(tmp_msg_list, False)
        del tmp_msg_list
        if len(msg_list_from_file) == 0 and not self.is_freeze:
            self.executeResponse()
        else:
            self.msg_list = msg_list_from_file
            print("Get list from file=", self.path)
        print("name=", self.getName())
        print("path=", self.path)

    def getRichPrompt(self) -> str:
        if self.parent:
            return self.msg_list[-1]["content"]
        return self.prompt

    def executeResponse(self):
        param_name = "path_to_write"
        self.updateParam(param_name)
        self.saveJsonToFile(self.msg_list)
       # what to write  0
        # text           1
        # where to write 2
        # path           3
        # this task
        print("-----------------------------------------------------------------------------------Msg lst=", len(self.msg_list))
        if len(self.msg_list) < 3:
            return
        print("Path=", self.getRichPrompt())
        # if os.path.isfile(self.getRichPrompt()):
        with open(self.getRichPrompt(), 'w') as f:
            print("path_to_read =", self.getRichPrompt())
            text = self.msg_list[len(self.msg_list) - 3]["content"]
            f.write(text)

    def update(self, input: TaskDescription = None):
        if self.parent:
            trg_list = self.parent.msg_list.copy()
        else:
            trg_list = []
        if self.msg_list != trg_list:
            self.msg_list = trg_list
            self.executeResponse()
        super().update(input)
        out = self.msg_list[len(self.msg_list) - 1]
        return out["content"], out["role"], ""
