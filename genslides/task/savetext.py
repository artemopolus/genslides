import genslides.task.text as Txt

class SaveTextTask(Txt.TextTask):
    def __init__(self, task_info : Txt.TextTask, type='SaveText'):
        super().__init__(task_info, type)
        pair = {
            "role" : self.prompt_tag,
            "content" : self.getRichPrompt()
        }

        tmp_msg_list = self.getRawMsgs()
        tmp_msg_list.append(pair)
        msg_list_from_file = self.getResponseFromFile(tmp_msg_list, remove_last=False)
        del tmp_msg_list
        
        if len(msg_list_from_file) == 0:
            self.appendMessage(pair)
            self.onEmptyMsgListAction()
        else:
            self.onExistedMsgListAction(msg_list_from_file)
        
        self.saveAllParams()

    def onEmptyMsgListAction(self):
        self.saveJsonToFile(self.msg_list)
        return super().onEmptyMsgListAction()

    def onExistedMsgListAction(self, msg_list_from_file):
        self.msg_list = msg_list_from_file
        return super().onExistedMsgListAction(msg_list_from_file)

