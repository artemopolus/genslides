from genslides.task.text import TextTask
from genslides.task.base import TaskDescription
import pprint
from genslides.utils.llmodel import LLModel
import threading
import queue
class ResponseTask(TextTask):
    # Class-wide attributes
    task_queue = queue.Queue()  # Shared queue for tasks
    worker_thread = None  # Shared worker thread




    def __init__(self, task_info: TaskDescription, type="Response") -> None:
        super().__init__(task_info, type)

        tmp_msg_list = self.msg_list.copy()
        msg_list_from_file = self.getResponseFromFile(tmp_msg_list)
        del tmp_msg_list

        self.freezeTask()

        if len(msg_list_from_file) == 0:
            self.onEmptyMsgListAction()
        else:
            self.onExistedMsgListAction(msg_list_from_file)

        self.saveJsonToFile(self.msg_list)
        
        # Start the worker thread if it hasn't been started yet
        if ResponseTask.worker_thread is None:
            ResponseTask.worker_thread = threading.Thread(target=self.run_worker)
            ResponseTask.worker_thread.start()


    def onEmptyMsgListAction(self):
        # print('On empty msg list action', self.getName())
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
        return super().onEmptyMsgListAction()

    def onExistedMsgListAction(self, msg_list_from_file):
        # print('On existed msg list action', self.getName())
        res, val = self.getParam("model")
        if not res:
            res, model_name =  self.reqhelper.getValue(self.getType(), "model")
            if res:
                self.updateParam("model", model_name)
            else:
                self.updateParam("model", "gpt-3.5-turbo")

        self.msg_list = msg_list_from_file
        if self.checkParentMsgList(update=True, save_curr=False):
            res, content, _ =  self.getLastMsgAndParent()
            if res and content[0]['content'] != "":
                self.stdProcessUnFreeze()
        # print("Get list from file=", self.path)
        return super().onExistedMsgListAction(msg_list_from_file)

    def setChatPram(self, name):
            res, temperature =  self.reqhelper.getValue(self.getType(), name)
            # print("t=",temperature)
            if res:
                self.updateParam(name, temperature)


    def run_worker(self):
        while True:
            task = ResponseTask.task_queue.get()
            if task is None:  # Check for signal to stop the worker
                break
            chat, callback = task
            result = self.executeResponseInternal(chat)
            callback(result)
            ResponseTask.task_queue.task_done()

    @classmethod
    def stop_worker(cls):
        if cls.worker_thread is not None:
            cls.task_queue.put(None)  # Send signal to stop the worker
            cls.worker_thread.join()  # Wait for the worker to finish
            cls.worker_thread = None  # Reset the worker thread reference


    def process_response(self, output):
        res, out, out_params = output
        self.updateParam2(out_params)
        if res:
            pair = {}
            pair["role"] = "assistant"  # Replace chat.getAssistTag() with "assistant"
            pair["content"] = out
            self.prompt = out
            self.msg_list.append(pair)
            print('Update response for', self.getName())
            self.stdProcessUnFreeze()  # Call stdProcessUnFreeze if res is true
        else:
            self.freezeTask()
            self.msg_list.append({"role": "assistant", "content": ""})


    def executeResponse(self):
        self.freezeTask()  # Freeze the task at the beginning
        
        res, param = self.getParamStruct('model')

        if res:
            print('Get options from task')
            chat = LLModel(param)
        else:
            print('Init with default option')
            res, model_name = self.reqhelper.getValue(self.getType(), "model")
            if res:
                print('Init with default params')
                param = {'type': 'model', 'model': model_name}
            chat = LLModel(param)

        # Submit task to the queue with a callback for processing the response
        ResponseTask.task_queue.put((chat, self.process_response))


    def executeResponseInternal(self, chat: LLModel):
        input_msg_list = self.getMsgs()
        input_msg_list.pop()  # Remove last message
        return chat.createChatCompletion(input_msg_list)


    def getResponseTag(self):
        # This function returns the response role/tag used in the chat messages.
        return "assistant"  # You can replace this with the appropriate logic if needed.


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
                # self.is_freeze = False
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
                    print('Last msg is empty', self.getName())
                    # Если сообщение пустое, то убираем его
                    self.msg_list.pop()
                    self.executeResponse()
                    self.saveJsonToFile(self.msg_list)

        # super().update(input)

    def forceSetPrompt(self, prompt):
        if len(self.msg_list) == 0:
            return
        if not self.checkParentMsgList(update=True, save_curr=False):
            self.copyParentMsg()
        else:
            msg = self.getLastMsgContentRaw()
            if len(msg) == 0:
                self.msg_list.pop()
            else:
                return
        res, param = self.getParamStruct('model')
        if res:
            chat = LLModel(param)
        else:
            chat = LLModel()
        
        pair = {}
        pair["role"] = chat.getAssistTag()
        pair["content"] = prompt
        self.prompt = prompt
        self.msg_list.append(pair)
        self.stdProcessUnFreeze()
 


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
        if res and 'logprobs' in p:
            out = []
            max_log = -1000
            min_log = 0

            prob_vector = []

            for value in p['logprobs']:
                log = value['logprob']
                if log > -20:
                    prob_vector.append(log)
                else:
                    prob_vector.append(-20)
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
            return out, text, prob_vector
        else:
            return super().getTextInfo()

    def checkGetContentAndParent(self):
        pres, pparam = self.getParamStruct('hidden')
        if pres and pparam['hidden']:
            return False, [], self.parent
        pack = {
                "role":self.getLastMsgRole(), 
                "content": self.findKeyParam(self.getLastMsgContent()),
                "task": self.getName()
                }
        rres, rparam = self.getParamStruct('response', only_current=True)
        if rres:
            pack["logprobs"] = rparam["logprobs"]
        val = [pack]
        if self.parent != None:
            self.parent.setActiveBranch(self)
        return True, val, self.parent

    def forceCleanChat(self):
        if len(self.msg_list) > 1:
            # last = self.msg_list[-1]
            self.msg_list = []
            # self.msg_list.append(last)
        self.freezeTask()



