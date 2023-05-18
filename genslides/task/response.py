from genslides.task.text import TextTask
from genslides.task.base import TaskDescription
import pprint
from genslides.utils.largetext import SimpleChatGPT



class ResponseTask(TextTask):
    def __init__(self, task_info : TaskDescription) -> None:
        super().__init__(task_info, "Response")
        chat = SimpleChatGPT()
        tmp_msg_list = self.msg_list.copy()
        msg_list_from_file = self.getResponseFromFile(tmp_msg_list)
        del tmp_msg_list
        # print("Response\n==================>>>>>>>>>>>\n", pprint.pformat( self.msg_list))
        
        if len(msg_list_from_file) == 0:
            res, out = chat.recvRespFromMsgList(self.msg_list)
            if res:
                # print("out=", out)
                pair = {}
                pair["role"] = chat.getAssistTag()
                pair["content"] = out
                self.msg_list.append(pair)

            self.saveJsonToFile(self.msg_list)
        else:
            self.msg_list = msg_list_from_file
            print("Get list from file=", self.path)


    def completeTask(self):
        self.is_solved = True
        return True

    def update(self, input : TaskDescription = None):
        if self.parent:
            trg_list = self.parent.msg_list.copy()
        else:
            return "","user"
        
        last = self.msg_list[len(self.msg_list) - 1]
        trg_list.append(last)
        if self.msg_list != trg_list:
            trg_list.pop()
            self.msg_list = trg_list.copy()
            chat = SimpleChatGPT()
            res, out = chat.recvRespFromMsgList(self.msg_list)
            if res:
                # print("out=", out)
                pair = {}
                pair["role"] = chat.getAssistTag()
                pair["content"] = out
                self.msg_list.append(pair)
                self.saveJsonToFile(self.msg_list)
        super().update()
        out = self.msg_list[len(self.msg_list) - 1]
        return out["content"], out["role"]

    def beforeRemove(self):
        self.deleteJsonFile()
        super().beforeRemove()
    
    def whenParentRemoved(self):
        super().whenParentRemoved()
        last = self.msg_list.pop()
        self.msg_list = []
        self.msg_list.append(last)
        self.saveJsonToFile(self.msg_list)

 