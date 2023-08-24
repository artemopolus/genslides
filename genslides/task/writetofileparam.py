from genslides.task.base import TaskDescription
from genslides.task.writetofile import WriteToFileTask


class WriteToFileParamTask(WriteToFileTask):
    def __init__(self, task_info: TaskDescription, type="WriteToFileParam") -> None:
        super().__init__(task_info, type)
        param_name = "path_to_write"
        res, path = self.getParam(param_name)
        if res:
            self.writepath = path

    def getRichPrompt(self) -> str:
        return self.writepath

    def executeResponse(self):
        print("Exe resp write to file param")
        param_name = "path_to_write"
        res, path = self.getParam(param_name)
        if self.is_freeze or len(self.msg_list) == 0 or res == False:
            return
        self.writepath = path
        with open(path, 'w',encoding='utf8') as f:
            print("path_to_write =", path)
            text = self.msg_list[len(self.msg_list) - 1]["content"]
            # print("Try to save=", text)
            f.write(text)

    def update(self, input : TaskDescription = None):
        super().update(input)
        return self.writepath, "user", ""

    def getMsgInfo(self):
        return self.writepath, "user", ""
 
