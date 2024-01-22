from genslides.task.base import TaskDescription
from genslides.task.websurf import WebSurfTask

import json


class WebSurfArrayTask(WebSurfTask):
    def __init__(self, task_info: TaskDescription, type="WebSurfArray") -> None:
        super().__init__(task_info, type)


    def getLinksData(self, link_list):
        output = {"type":"iteration","data": link_list}
        return json.dumps(output)

