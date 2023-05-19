from genslides.task.text import TextTask
from genslides.task.base import TaskDescription
import pprint
from genslides.utils.largetext import SimpleChatGPT



class RichTextTask(TextTask):
    def __init__(self, task_info : TaskDescription) -> None:
        super().__init__(task_info, "RichText")
        chat = SimpleChatGPT()
        pair = {}
        pair["role"] = chat.getUserTag()
        pair["content"] = self.getRichPrompt()

        tmp_msg_list = self.msg_list.copy()
        tmp_msg_list.append(pair)
        msg_list_from_file = self.getResponseFromFile(tmp_msg_list)
        del tmp_msg_list
        print("==================>>>>>>>>>>>", pprint.pformat( self.msg_list))
        
        if len(msg_list_from_file) == 0:
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
        else:
            self.msg_list = msg_list_from_file
            print("Get list from file=", self.path)


    # def completeTask(self):
    #     print("target=",self.target)
    #     self.is_solved = True
    #     if self.target:
    #         print("Add text:", self.richtext)
    #         self.target(self.richtext[0], self.task_id)
    #     return True

