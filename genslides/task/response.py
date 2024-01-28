from genslides.task.text import TextTask
from genslides.task.base import TaskDescription
import pprint

from genslides.utils.llmodel import LLModel



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
        # print("name=", self.getName())
        # print("path=", self.path)
        self.saveJsonToFile(self.msg_list)

    def onEmptyMsgListAction(self):
        self.setChatPram("temperature")
        self.setChatPram("model")
        # Если задача заморожена
        if self.is_freeze:
            res, param = self.getParamStruct('model')
            # то сохраняем пустое сообщение
            if res:
                chat = LLModel(param) 
                self.msg_list.append({"role": chat.getAssistTag(), "content": ""})
            else:
                self.msg_list.append({"role": "assistant", "content": ""})
        else:
            # в противном случае выполняем запрос
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
        # print("Get list from file=", self.path)

    def setChatPram(self, name):
            res, temperature =  self.reqhelper.getValue(self.getType(), name)
            # print("t=",temperature)
            if res:
                self.updateParam(name, temperature)

    def executeResponseInternal(self, chat : LLModel):
        # input_msg_list = self.msg_list.copy()
        # input_msg_list = [] 
        # for msg in self.msg_list:
        #     input_msg_list.append(msg.copy())
        # for msg in input_msg_list:
        #     msg["content"] = self.findKeyParam(msg["content"])

        input_msg_list = self.getMsgs()
        # print('Request=',input_msg_list)

        return chat.createChatCompletion(input_msg_list)

 
    def executeResponse(self):
        res, param = self.getParamStruct('model')

        if res:
            chat = LLModel(param)
        else:
            chat = LLModel()
        res, out, out_params = self.executeResponseInternal(chat)
        self.updateParam2(out_params)
        if res:
            # print("out=", out)
            pair = {}
            pair["role"] = chat.getAssistTag()
            pair["content"] = out
            self.prompt = out
            self.msg_list.append(pair)
            print('Update response for', self.getName())
            # print('Response=',out)
        # print('Msg list=',self.msg_list)



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
            # print("frozen=",self.getName())
            if not self.parent.is_freeze:
                self.is_freeze = False
                tmp_msg_list = self.getRawParentMsgs()
                # print(pprint.pformat(tmp_msg_list))
                msg_list_from_file = self.getResponseFromFile(tmp_msg_list)
                # print('Parent:',len(tmp_msg_list))
                # print('Current:', len(msg_list_from_file))
                # print('Msg[',len(msg_list_from_file[-1]['content']) ,']:|',msg_list_from_file[-1]['content'],'|')
                if len(msg_list_from_file):
                    print("I loaded")
                    self.msg_list = msg_list_from_file

            else:
                # super().update(input)
                return "","user",""
        
       

        # print("Update response task=", self.getName(),"[", len(self.msg_list),"]")
        # print("Response\n==================>>>>>>>>>>>\n", pprint.pformat( self.msg_list))

        # Если список сообщений пустой, за-за чего?
        if len(self.msg_list) == 0:
            print('Empty msg list', self.getName())
            self.executeResponse()
            self.saveJsonToFile(self.msg_list)
        else:
            # Проверка настроек для конкретного типа задачи
            sres, sparam = self.getParamStruct(self.getType())
            exe_always = False
            if sres and 'do_always' in sparam and sparam['do_always']:
                exe_always = True
            # Проверка сообщений родителя
            if not self.checkParentMsgList(update=True, save_curr=False) or exe_always:
                # Список сообщений родителя отличается
                print('Parent msg differs', self.getName())
                self.executeResponse()
                self.saveJsonToFile(self.msg_list)
            else:
                # Список сообщений такой же
                # print("Messages are same")
                msg = self.getLastMsgContentRaw()
                # print('Response[',len(msg),']|',msg,'|')
                # Если сообщение пустое, то делаем вывод, что задача была морожена
                if len(msg) == 0:
                    # Запрашиваем сообщение
                    print('Msg is empty', self.getName())
                    self.executeResponse()
                    self.saveJsonToFile(self.msg_list)

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
    
    
    def getTextInfo(self, param):
        res, p = self.getParamStruct('response', only_current=True)
        if res:
            out = []
            max_log = -1000
            min_log = 0
            for value in p['logprobs']:
                log = value['logprob']
                if log > param['notgood']:
                    pair = [value['token'], 'good']
                elif log > param['bad']:
                    pair = [value['token'], 'notgood']
                else:
                    pair = [value['token'], 'bad']
                out.append(pair)
                max_log = max(max_log, log)
                min_log = min(min_log, log)

            text = 'Log vars from' + str( max_log) + 'to' + str(min_log)
            return out, text
        else:
            return super().getTextInfo()

