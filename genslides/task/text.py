from genslides.task.base import BaseTask
from genslides.task.base import TaskDescription

import genslides.utils.reqhelper as ReqHelper
import genslides.utils.request as Requester
import genslides.utils.browser as Browser
import genslides.utils.browser as WebBrowser
import genslides.utils.largetext as Summator

from genslides.utils.searcher import GoogleApiSearcher
from genslides.utils.chatgptrequester import ChatGPTrequester
from genslides.utils.chatgptrequester import ChatGPTsimple
from genslides.utils.largetext import SimpleChatGPT

import json
import os
from os import listdir
from os.path import isfile, join
import pprint
import re


class TextTask(BaseTask):
    def __init__(self, task_info: TaskDescription, type='None') -> None:
        super().__init__(task_info, type)

        print("Type=", self.type)

        self.path = self.getPath()
        self.copyParentMsg()
        self.params = []

    def copyParentMsg(self):
        self.msg_list = self.getParentMsg()
   
    def getParentMsg(self):
        if self.parent is None:
            return []
        else:
            out =  self.parent.msg_list.copy()
            return out

    def forceCleanChat(self):
        if len(self.msg_list) > 1:
            last = self.msg_list[-1]
            self.msg_list = []
            self.msg_list.append(last)

    def getCountPrice(self):
        text = ""
        for msg in self.msg_list:
            text += msg["content"]

        chat = SimpleChatGPT()
        return chat.getPrice(text)

    def getPath(self) -> str:
        if not os.path.exists("saved"):
            os.makedirs("saved")
        mypath = "saved/"
        onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
        self.name = self.type + str(self.id)
        print("Name =", self.name)
        name = self.name + ".json"
        found = False
        while not found:
            if name in onlyfiles:
                self.name = self.type + str(self.getNewID())
                name = self.name + ".json"
            else:
                found = True
        return mypath + name

    def getJson(self):
        resp_json_out = {
            'name': self.getName(),
            'chat': self.msg_list,
            'type': self.type,
            'params': self.params
        }
        linked = []
        for info in self.by_ext_affected_list:
            linked.append(info.parent.getName())
        resp_json_out['linked'] = linked
        path = ""
        if self.parent:
            len_par_path = len(self.parent.path)
            path = self.parent.path[6:(len_par_path - 5)]
        resp_json_out['parent'] = path
        child_names = []
        for child in self.childs:
            child_names.append(child.getName())
        resp_json_out['childs'] = child_names
        return resp_json_out

    def saveJsonToFile(self, msg_list):
        resp_json_out = {
            'chat': msg_list,
            'type': self.type,
            'params': self.params
        }
        linked = []
        for info in self.by_ext_affected_list:
            linked.append(info.parent.getName())
        resp_json_out['linked'] = linked
        path = ""
        if self.parent:
            path = self.parent.path
        resp_json_out['parent'] = path
        print("Save json to", self.path)
        with open(self.path, 'w') as f:
            # print("save to file=", self.path)
            json.dump(resp_json_out, f, indent=1)

    def deleteJsonFile(self):
        os.remove(self.path)

        # path = self.path
        # if not os.path.exists(path):
        #     with open(path, 'w') as f:
        #         print('Create file: ', path)

    def saveTxt(self, text):
        with open(self.path, 'w', encoding="utf-8") as f:
            f.write(text)

    def openTxt(self):
        with open(self.path, 'r', encoding="utf-8") as f:
            return f.read()

    def saveRespJson(self, request, response):
        resp_json_out = {}
        resp_json_out['request'] = request
        resp_json_out['responses'] = response
        with open(self.path, 'w') as f:
            json.dump(resp_json_out, f, indent=1)

    def checkFile(self):
        if not os.path.exists(self.path):
            return False
        if os.stat(self.path).st_size == 0:
            return False
        return True

    def processResponse(self):
        request = self.getRichPrompt()
        responses = self.getResponse(request)
        if len(responses) == 0:
            chat = SimpleChatGPT()
            self.user = chat.getUserTag()
            self.chat = chat.getAssistTag()
            res, text = chat.recvResponse(request)
            if res:
                self.saveRespJson(request, responses)

    def getResponseFromFile(self, msg_list, remove_last=True):
        print("Get response from file:")

        mypath = "saved/"
        onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
        trg_file = self.filename + ".json"
        # for file in onlyfiles:
        if trg_file in onlyfiles:
            file = trg_file
            if file.startswith(self.type):
                path = mypath + file
                try:
                    print(path)
                    with open(path, 'r') as f:
                        rq = json.load(f)
                    if 'chat' in rq:
                        msg_trgs = rq['chat'].copy()
                        if remove_last:
                            msg_trgs.pop()
                        stopped = False
                        if 'params' in rq:
                            # print("params=", rq['params'])
                            for param in rq['params']:
                                if 'stopped' in param and param['stopped']:
                                    stopped = True
                        if msg_trgs == msg_list or stopped or self.is_freeze:
                            print(10*"====", "\nLoaded from file:")
                            self.path = path
                            self.name = file.split('.')[0]
                            if 'params' in rq:
                                self.params = rq['params']
                            print("My new name is ", self.name)
                            return rq['chat']
                except json.JSONDecodeError:
                    pass
        return []

    def getResponse(self, request):
        mypath = "saved/"
        onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
        for file in onlyfiles:
            if file.startswith(self.type):
                path = mypath + file
        # if os.stat(self.path).st_size != 0:
                try:
                    with open(path, 'r') as f:
                        rq = json.load(f)
                    if 'request' in rq and rq['request'] == request:
                        self.path = path
                        return rq['responses']
                except json.JSONDecodeError:
                    pass
        return []

    def createLinkToTask(self, task) -> TaskDescription:
        out = super().createLinkToTask(task)
        self.saveJsonToFile(self.msg_list)
        return out

    def completeTask(self) -> bool:
        res = super().completeTask()
        # info = TaskDescription(prompt=self.getRichPrompt(),
                            #    prompt_tag=self.getTagPrompt())
        # self.update(info)
        return res

    def getTagPrompt(self):
        return self.prompt_tag
        # return self.msg_list[len(self.msg_list) - 1]["role"]

    def useLinksToTask(self):
        # if self.getName() == "Collect8":
        #     print("==========================================================================")
        #     print(len(self.affect_to_ext_list))
        if len(self.msg_list) == 0:
            return
        text = self.msg_list[len(self.msg_list) - 1]["content"]
        # input = TaskDescription(prompt=text, parent=self)
        for task in self.affect_to_ext_list:
            # task.prompt = text
            input = task
            input.prompt = text
            input.enabled = not self.is_freeze
            task.method(input)

    def affectedTaskCallback(self, input: TaskDescription):
        pass
        # print("My name is ", self.getName())
        # print("My prompt now is ", self.getRichPrompt())
        # print("Msgs=",pprint.pformat(self.msg_list))

    def beforeRemove(self):
        self.deleteJsonFile()
        super().beforeRemove()

    def whenParentRemoved(self):
        super().whenParentRemoved()
        last = self.msg_list.pop()
        self.msg_list = []
        self.msg_list.append(last)
        self.saveJsonToFile(self.msg_list)

    def getMsgInfo(self):
        return super().getMsgInfo()

    def preUpdate(self, input: TaskDescription = None):
        if input:
            self.prompt = input.prompt
            self.prompt_tag = input.prompt_tag
            for param in input.params:
                self.updateParam(param["name"], param["value"])

            self.saveJsonToFile(self.msg_list)

    def stdProcessUnFreeze(self, input=None):
        if self.parent:
            self.is_freeze = self.parent.is_freeze

        res, is_input = self.getParam("input")
        # if input:
        #     print("input manual=",input.manual)
        if res and is_input:
            if input and input.manual:
                self.is_freeze = False
            else:
                self.is_freeze = True
        # print("freeze=", self.is_freeze)

    def update(self, input: TaskDescription = None):
        if input:
            self.prompt = input.prompt
            self.prompt_tag = input.prompt_tag
            for param in input.params:
                self.updateParam(param["name"], param["value"])

            self.saveJsonToFile(self.msg_list)

        return super().update(input)

    def getInfo(self, short=True) -> str:
        if short and len(self.prompt) > 20:
            return self.prompt[0:20] + "..."
        else:
            return self.prompt

    def updateParam(self, param_name, data):
            found = False
            for param in self.params:
                if param_name in param:
                    param[param_name] = data
                    found = True
            if not found:
                self.params.append({param_name: data})

    def getParamFromExtTask(self, param_name):
        return False, None, None
    
    def getParam(self, param_name):
        parent_task = self.parent

        index = 0
        while(index < 1000):
            res, parent_task, val = parent_task.getParamFromExtTask(param_name)
            if res:
                return True, val
            if parent_task is None:
                break
        # если ничего не нашли загружаем стандартное
        # print("Params=",self.params)
        for param in self.params:
            for k,p in param.items():
                # print("k=",k,"p=",p)
                if param_name == k:
                    return True, p
        return False, None

    def findKeyParam(self, text: str):
         results = re.findall(r'\{.*?\}', text)
        #  print("Find keys=", text)
         print("Results=", results)
         rep_text = text
         for res in results:
             arr = res[1:-1].split(":")
             if len(arr) == 2:
                 task = self.getAncestorByName(arr[0])
                 if task:
                    p_exist, param = task.getParam(arr[1])
                    if p_exist:
                        print("Replace ", res, " with ", param)
                        rep_text = rep_text.replace(res, str(param))
                    else:
                        print("No param")
                 else:
                     print("No task")
             else:
                print("Incorrect len")
         return rep_text

 