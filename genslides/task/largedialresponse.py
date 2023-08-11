from genslides.task.base import TaskDescription
from genslides.task.largetextresponse import LargeTextResponseTask
from genslides.utils.largetext import SimpleChatGPT


class LargeDialResponseTask(LargeTextResponseTask):
    def __init__(self, task_info: TaskDescription, type="LargeDialResponse") -> None:
        super().__init__(task_info, type)


    def executeResponseInternal(self, chat : SimpleChatGPT):
        if len(self.msg_list) < 2:
            return False, ""
        input_msg_list = self.msg_list.copy()
        text = ""
        for msg in input_msg_list:
            msg["content"] = self.findKeyParam(msg["content"])
            text += msg["content"]

        
        last = input_msg_list[-1]["content"]
        tokens_start = chat.getTokensCount(text)
        tokens_last = chat.getTokensCount(last)
        if (chat.getMaxTokensNum() < tokens_last):
            divide_num_tokens = chat.getMaxTokensNum()  - tokens_start + tokens_last
            parts = self.getParts(last, chat.getTokensCount, 1000, divide_num_tokens)
            summation = ""
            for part in parts:
                print("Partial request")
                req_list = input_msg_list.copy()
                req_list[-1]["content"] = part
                res, ans = chat.recvRespFromMsgList(req_list)
                if res:
                    summation += ans + "\n"
            return True, summation

        else:
            res, out = chat.recvRespFromMsgList(input_msg_list)
        return res, out


