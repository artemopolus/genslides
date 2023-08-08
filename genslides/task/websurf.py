from genslides.task.response import ResponseTask
from genslides.task.base import TaskDescription
from genslides.utils.searcher import GoogleApiSearcher
from genslides.utils.browser import WebBrowser


class WebSurfTask(ResponseTask):
    def __init__(self, task_info: TaskDescription, type="WebSurf") -> None:
        super().__init__(task_info, type)
        print("Web Request")

    def getRichPrompt(self) -> str:
        return self.msg_list[-1]["content"]
        # return self.prompt

    def getLinksData(self, link_list):
        text = ""
        for link in link_list:          
            browser = WebBrowser()
            text += link + "\n"
            text += browser.get(link)
        return text


    def executeResponse(self):
        param_name = "web_request"
        if param_name in self.params:
            self.params[param_name] = self.getRichPrompt()
        else:
            self.params.append({param_name: self.getRichPrompt()})
        print("Searching")
        searcher = GoogleApiSearcher()
        link_list = searcher.getSearchs(self.getRichPrompt())
        text = self.getLinksData(link_list)

        self.msg_list.append({
            "role": self.prompt_tag,
            "content": text
        })

