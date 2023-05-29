from genslides.task.base import TaskDescription
from genslides.task.response import ResponseTask
from genslides.utils.largetext import SimpleChatGPT


class HotResponseTask(ResponseTask):
    def __init__(self, task_info: TaskDescription, type="HotResponse") -> None:
        super().__init__(task_info, type)


    def executeResponse(self):
        chat = SimpleChatGPT()
        res, out = chat.recvRespFromMsgList(self.msg_list, options=True, temperature=1.5)
        if res:
            # print("out=", out)
            pair = {}
            pair["role"] = chat.getAssistTag()
            pair["content"] = out
            self.msg_list.append(pair)



