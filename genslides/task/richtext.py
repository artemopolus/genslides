from genslides.task.text import TextTask
from genslides.task.base import TaskDescription
import pprint
from genslides.utils.largetext import SimpleChatGPT



class RichTextTask(TextTask):
    def __init__(self, task_info : TaskDescription) -> None:
        super().__init__(task_info, "RichText")

        chat = SimpleChatGPT()

        self.user_tag = chat.getUserTag()
        self.asis_tag = chat.getAssistTag()
        pair = {
        "role" : self.user_tag,
        "content" : self.getRichPrompt()
        }
        # print("Msg list=", self.msg_list)

        tmp_msg_list = self.msg_list.copy()
        tmp_msg_list.append(pair)
        # print("==================>>>>>>>>>>>", pprint.pformat( tmp_msg_list))
        msg_list_from_file = self.getResponseFromFile(tmp_msg_list)
        del tmp_msg_list
        
        if len(msg_list_from_file) == 0 and not self.is_freeze:
            pair = {}
            pair["role"] = chat.getUserTag()
            pair["content"] = self.getRichPrompt()
            self.msg_list.append(pair)
            res, out = chat.recvRespFromMsgList(self.msg_list)
            if res:
                # print("out=", out)
                pair = {}
                pair["role"] = chat.getAssistTag()
                pair["content"] = out
                self.msg_list.append(pair)

            self.saveJsonToFile(self.msg_list)
        elif len(msg_list_from_file) == 0 and self.is_freeze:
            self.msg_list.append({"role": chat.getUserTag(), "content": self.getRichPrompt()})
            self.msg_list.append({"role": chat.getAssistTag(), "content": ""})
        else:
            self.msg_list = msg_list_from_file
            print("Get list from file=", self.path)
 
    def getTagPrompt(self):
        return self.user_tag

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
        if not self.is_freeze:
            print("frozen")
            if not self.parent.is_freeze:
                self.is_freeze = False
        else:
            return "","user",""
        if self.parent:
            trg_list = self.parent.msg_list.copy()
            # print("Response\n==================>>>>>>>>>>>\n", pprint.pformat( trg_list))
        else:
            return "","user",""
        
        if len(self.msg_list) > 1: 
            last = self.msg_list[- 1]
            if last["role"] == self.asis_tag:
                if input == None:
                    last = self.msg_list[- 2]
                    trg_list.append(last)
                else:
                    # print('I\'m here')
                    trg_list.append({"role" : input.prompt_tag, "content" : input.prompt})
                last = self.msg_list[- 1]
                trg_list.append(last)
                # print("Response\n==================>>>>>>>>>>>\n", pprint.pformat( trg_list))
                # print("Diff\n==================>>>>>>>>>>>\n", pprint.pformat( [i for i in trg_list if i not in self.msg_list]))
                # print("Diff\n==================>>>>>>>>>>>\n", pprint.pformat( [i for i in self.msg_list if i not in trg_list]))

                if self.msg_list == trg_list:
                    super().update()
                    out = self.msg_list[ - 2]
                    return out["content"], out["role"], self.msg_list[-1]["content"]
        
        self.msg_list = self.parent.msg_list.copy()
        self.msg_list.append( {
        "role" : self.user_tag,
        "content" : self.getRichPrompt()
        })
        self.executeResponse()
        self.saveJsonToFile(self.msg_list)
        super().update(input)
        out = self.msg_list[- 2]
        return out["content"], out["role"], self.msg_list[-1]["content"]

    def getMsgInfo(self):
        out = self.msg_list[- 2]
        return out["content"], out["role"], self.msg_list[-1]["content"]
 