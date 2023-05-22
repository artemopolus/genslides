from genslides.task.response import ResponseTask
from genslides.task.base import TaskDescription
from genslides.utils.searcher import GoogleApiSearcher


class WebSurfTask(ResponseTask):
    def __init__(self, task_info: TaskDescription, type="WebSurf") -> None:
        super().__init__(task_info, type)

    def getRichPrompt(self) -> str:
        return self.prompt

    def executeResponse(self):
        param_name = "web_request"
        if param_name in self.params:
            self.params[param_name] = self.getRichPrompt()
        else:
            self.params.append({param_name: self.getRichPrompt()})
        searcher = GoogleApiSearcher()
        link_list = searcher.getSearchs(self.getRichPrompt())
        

