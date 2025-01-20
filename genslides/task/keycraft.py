import genslides.task.request as Rq
import genslides.task.text as Txt

class KeyCraftTask(Txt.TextTask):
    def __init__(self, task_info, type="KeyCraft"):
        super().__init__(task_info, type)
        pair = {}
        pair["role"] = task_info.prompt_tag
        pair["content"] = self.getRichPrompt()

        tmp_msg_list = self.msg_list.copy()
        tmp_msg_list.append(pair)
        msg_list_from_file = self.getResponseFromFile(tmp_msg_list, remove_last=False)
        # print("list from file=",msg_list_from_file)
        del tmp_msg_list
        # print("==================>>>>>>>>>>>", pprint.pformat( self.msg_list))
        
        if len(msg_list_from_file) == 0:
            self.msg_list.append(pair)
            self.onEmptyMsgListAction()
        else:
            self.onExistedMsgListAction(msg_list_from_file)
            # print("Get list from file=", self.path)

        cres, cparam = self.getParamStruct('keycraft', only_current=True)
        if not cres:
            self.setParamStruct({
                "type":"keycraft",
                "input": ""
            })

    def onEmptyMsgListAction(self):
        self.saveJsonToFile(self.msg_list)
        return super().onEmptyMsgListAction()

    def onExistedMsgListAction(self, msg_list_from_file):
        self.msg_list = msg_list_from_file
        return super().onExistedMsgListAction(msg_list_from_file)


    def getRichPrompt(self):
        cres, cparam = self.getParamStruct('keycraft', only_current=True)
        if cres:
            codes = cparam['input'].split(',')
            median = []
            print(codes)
            for code in codes:
                median.append( self.findKeyParam(code.replace(" ","")) )
            text = "[[" + ":".join(median) + "]]"
            print(text)
            return self.findKeyParam( text )
        return ""
    
    def updateIternal(self, input = None):
        content = self.getRichPrompt()
        print(content)
        self.appendMessage({"role":self.prompt_tag,"content": content})
        self.saveAllParams()
        return super().updateIternal(input)
    