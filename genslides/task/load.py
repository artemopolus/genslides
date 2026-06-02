import genslides.task.text as TextTask


class LoadTask(TextTask.TextTask):
    def __init__(self, task_info : TextTask.TaskDescription, type = "Load"):
        super().__init__(task_info, type=type)
        pair = {}
        pair["role"] = task_info.prompt_tag
        pair["content"] = self.getRichPrompt()

        tmp_msg_list = self.msg_list.copy()
        tmp_msg_list.append(pair)
        msg_list_from_file = self.getResponseFromFile(tmp_msg_list, remove_last=False)
        del tmp_msg_list
        
        if len(msg_list_from_file) == 0:
            self.msg_list.append(pair)
            self.onEmptyMsgListAction()
        else:
            self.onExistedMsgListAction(msg_list_from_file)

    def onEmptyMsgListAction(self):
        self.saveJsonToFile(self.msg_list)
        return super().onEmptyMsgListAction()

    def onExistedMsgListAction(self, msg_list_from_file):
        self.msg_list = msg_list_from_file
        return super().onExistedMsgListAction(msg_list_from_file)


