from genslides.task.text import TextTask
from genslides.task.base import TaskDescription
import pprint


class ReactTask(TextTask):
    def __init__(self, task_info: TaskDescription) -> None:
        super().__init__(task_info, "React")
        tmp_msg_list = self.msg_list.copy()
        msg_list_from_file = self.getResponseFromFile(tmp_msg_list)
        del tmp_msg_list

        if len(msg_list_from_file) > 0:
            self.msg_list = msg_list_from_file
            # print("Get list from file=", self.path)
        self.saveJsonToFile(self.msg_list)

        self.is_freeze = True


    def update(self, input: TaskDescription = None):
        return "", "user"
    
    def createLinkToTask(self, task) -> TaskDescription:
        id = len(self.by_ext_affected_list)
        out = TaskDescription(
            method=self.affectedTaskCallback, id=id, parent=task, prompt=task.getRichPrompt())
        self.by_ext_affected_list.append(out)

        task.setLinkToTask(out)
        return super().createLinkToTask(task)

    def getRichPrompt(self) -> str:
        text = ""
        return text

    def affectedTaskCallback(self, input: TaskDescription):
        print("From ", input.parent.getName(), " to ", self.getName())
        need_update = False
        for task in self.by_ext_affected_list:
            if input.id == task.id and input.prompt != task.prompt:
                task.prompt = input.prompt
                need_update = True
        if need_update:
            self.is_freeze = False
            out = super().affectedTaskCallback(input)
            self.update()
            self.is_freeze = True
        return out

    def removeLinkToTask(self):
        self.prompt = ""
        self.update()
        self.is_freeze = True
        super().removeLinkToTask()


    def whenParentRemoved(self):
        super().whenParentRemoved()
        self.removeLinkToTask()

    def getInfo(self, short=True) -> str:
        out = ""
        for task in self.by_ext_affected_list:
            out += task.parent.getName()
        return out
