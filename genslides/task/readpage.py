from genslides.task.response import ResponseTask
from genslides.task.base import TaskDescription
from genslides.utils.browser import WebBrowser

class ReadPageTask(ResponseTask):
    def __init__(self, task_info: TaskDescription, type="ReadPage") -> None:
        super().__init__(task_info, type)

    def getRichPrompt(self) -> str:
        if self.parent:
            return self.msg_list[-1]["content"]
        return self.prompt

    def executeResponse(self):
        param_name = "url"
        if param_name in self.params:
            self.params[param_name] = self.getRichPrompt()
        else:
            self.params.append({param_name: self.getRichPrompt()})
        browser = WebBrowser()
        text = browser.get(self.getRichPrompt())
        print ("Text=", text)
        self.msg_list.append({
            "role": self.prompt_tag,
            "content": text
        })

    def getInfo(self, short = True) -> str:
        info = ""
        for param in self.params:
            if "url" in param:
                info = param["url"]
                info = info[8:]
        if short and len(info) > 20:
            return info[0:17] + "..."
        else:
            return info
 

