from genslides.task.text import TextTask
from genslides.task.base import TaskDescription
import pprint
from genslides.utils.largetext import SimpleChatGPT



class ResponseTask(TextTask):
    def __init__(self, task_info : TaskDescription, type = "Response") -> None:
        super().__init__(task_info, type)
        tmp_msg_list = self.msg_list.copy()
        msg_list_from_file = self.getResponseFromFile(tmp_msg_list)
        del tmp_msg_list
        # print("Response\n==================>>>>>>>>>>>\n", pprint.pformat( self.msg_list))
        
        if len(msg_list_from_file) == 0 and not self.is_freeze:
            self.executeResponse()
            self.saveJsonToFile(self.msg_list)
        elif len(msg_list_from_file) == 0 and self.is_freeze:
            chat = SimpleChatGPT()
            self.msg_list.append({"role": chat.getAssistTag(), "content": ""})
        else:
            self.msg_list = msg_list_from_file
            print("Get list from file=", self.path)

    def executeResponse(self):
        chat = SimpleChatGPT()
        res, out = chat.recvRespFromMsgList(self.msg_list)
        if res:
            # print("out=", out)
            pair = {}
            pair["role"] = chat.getAssistTag()
            pair["content"] = out
            self.msg_list.append(pair)



    def update(self, input : TaskDescription = None):
        if self.is_freeze and self.parent:
            print("frozen=",self.getName())
            if not self.parent.is_freeze:
                self.is_freeze = False
                tmp_msg_list = self.parent.msg_list.copy()
                print(pprint.pformat(tmp_msg_list))
                msg_list_from_file = self.getResponseFromFile(tmp_msg_list)
                if len(msg_list_from_file):
                    print("I loaded")
                    self.msg_list = msg_list_from_file

            else:
                return "","user",""
        
        print("Update response task=", self.getName())
        # print("Response\n==================>>>>>>>>>>>\n", pprint.pformat( self.msg_list))
        if self.parent:
            trg_list = self.parent.msg_list.copy()
        else:
            trg_list = []
        if len(self.msg_list) == 0:
            self.executeResponse()
            self.saveJsonToFile(self.msg_list)
        else:
            last = self.msg_list[- 1]
            trg_list.append(last)
            if self.msg_list != trg_list:
                trg_list.pop()
                self.msg_list = trg_list.copy()
                self.executeResponse()
                self.saveJsonToFile(self.msg_list)
        super().update(input)
        if len(self.msg_list) == 0:
            return "","user",""
        out = self.msg_list[len(self.msg_list) - 1]
        return "", out["role"],out["content"]

    def getMsgInfo(self):
        if len(self.msg_list):
            out = self.msg_list[len(self.msg_list) - 1]
            return "", out["role"],out["content"]
        return "","user",""
 