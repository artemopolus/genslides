from genslides.task.text import TextTask
from genslides.task.base import TaskDescription
from genslides.task.collect import CollectTask

class GroupCollectTask(CollectTask):
    def __init__(self, task_info: TaskDescription, type="GroupCollect") -> None:
        super().__init__(task_info, type)

    def updateLinkedPrompts(self, input : TaskDescription):
        # print("========================================================================update linked prompts")
        for tsk_info in self.by_ext_affected_list:
            if input.id == tsk_info.id:
                msgs = input.parent.getMsgs()
                text = ""
                for msg in msgs:
                    text += msg['content']
                    # print(msg)
                tsk_info.prompt = text
                tsk_info.enabled = input.enabled
                # if tsk_info.enabled:
                    # print('Input group msgs:',tsk_info.prompt)
                # print("Enabling=", tsk_info.id,"=",tsk_info.enabled)

