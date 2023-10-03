from genslides.task.base import TaskDescription
from genslides.task.collect import CollectTask

class ExtProjectTask(CollectTask):
    def __init__(self, task_info: TaskDescription, type="ExtProject") -> None:
        super().__init__(task_info, type)
        self.params.append({'type':'extproject','proj': task_info.prompt})
        self.saveJsonToFile(self.msg_list)
