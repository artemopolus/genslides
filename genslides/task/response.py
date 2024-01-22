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


        

        if len(msg_list_from_file) == 0:
            self.onEmptyMsgListAction()
        else:
            self.onExistedMsgListAction(msg_list_from_file)
        print("name=", self.getName())
        print("path=", self.path)
        self.saveJsonToFile(self.msg_list)

    def onEmptyMsgListAction(self):
        self.setChatPram("temperature")
        self.setChatPram("model")
        if self.is_freeze:
            res, model_name = self.getParam("model")
            if res:
                chat = SimpleChatGPT(model_name=model_name)
                self.msg_list.append({"role": chat.getAssistTag(), "content": ""})
        else:
            self.executeResponse()

    def onExistedMsgListAction(self, msg_list_from_file):
        # print("t=",temperature)
        res, val = self.getParam("model")
        if not res:
            res, model_name =  self.reqhelper.getValue(self.getType(), "model")
            if res:
                self.updateParam("model", model_name)
            else:
                self.updateParam("model", "gpt-3.5-turbo")

        self.msg_list = msg_list_from_file
        print("Get list from file=", self.path)

    def setChatPram(self, name):
            res, temperature =  self.reqhelper.getValue(self.getType(), name)
            print("t=",temperature)
            if res:
                self.updateParam(name, temperature)

    def executeResponseInternal(self, chat : SimpleChatGPT):
        # input_msg_list = self.msg_list.copy()
        input_msg_list = [] 
        for msg in self.msg_list:
            input_msg_list.append(msg.copy())
        for msg in input_msg_list:
            msg["content"] = self.findKeyParam(msg["content"])

        # print("Chat=",input_msg_list)

        res, out = chat.recvRespFromMsgList(input_msg_list)
        return res, out

 
    def executeResponse(self):
        res, model_name = self.getParam("model")

        if res:
            print("Exe resp with model=", model_name)
            chat = SimpleChatGPT(model_name=model_name)
        else:
            chat = SimpleChatGPT()
        res, temp = self.getParam("temperature")
        print("temp=", temp)
        if res:
            chat.setTemperature(temp)
        res, out = self.executeResponseInternal(chat)
        if res:
            # print("out=", out)
            pair = {}
            pair["role"] = chat.getAssistTag()
            pair["content"] = out
            self.msg_list.append(pair)


    def update(self, input : TaskDescription = None):
        super().update(input)
        if len(self.msg_list) == 0:
            return "","user",""
        # print("Msg kist:", self.msg_list)
        out = self.msg_list[len(self.msg_list) - 1]
        return "", out["role"],out["content"]


    def updateIternal(self, input : TaskDescription = None):
        # self.preUpdate(input=input)
        res, stopped = self.getParam("stopped")
        if res and stopped:
            print("Stopped=", self.getName())
            return "",self.prompt_tag,""
        
        if self.is_freeze and self.parent:
            print("frozen=",self.getName())
            if not self.parent.is_freeze:
                self.is_freeze = False
                tmp_msg_list = self.getRawParentMsgs()
                # print(pprint.pformat(tmp_msg_list))
                msg_list_from_file = self.getResponseFromFile(tmp_msg_list)
                if len(msg_list_from_file):
                    print("I loaded")
                    self.msg_list = msg_list_from_file

            else:
                # super().update(input)
                return "","user",""
        
       

        print("Update response task=", self.getName(),"[", len(self.msg_list),"]")
        # print("Response\n==================>>>>>>>>>>>\n", pprint.pformat( self.msg_list))

        if len(self.msg_list) == 0:
            print('Empty msg list')
            self.executeResponse()
            self.saveJsonToFile(self.msg_list)
        else:
            sres, sparam = self.getParamStruct(self.getType())
            exe_always = False
            if sres and 'do_always' in sparam and sparam['do_always']:
                exe_always = True
            if not self.checkParentMsgList(update=True, save_curr=False) or exe_always:
                self.executeResponse()
                self.saveJsonToFile(self.msg_list)
            else:
                print("Messages are same")
                pass
        # super().update(input)

    def getMsgInfo(self):
        if len(self.msg_list):
            out = self.msg_list[len(self.msg_list) - 1]
            return "", out["role"],out["content"]
        return "","user",""
    
    def getInfo(self, short = True) -> str:
        if len(self.msg_list) == 0:
            return "empty"
        if short:
            txt = self.msg_list[-1]["content"]
            if len(txt) > 20:
                return txt[:20]
            return txt
        return self.msg_list[-1]["content"]
