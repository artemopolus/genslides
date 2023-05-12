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

class TextTask(BaseTask):
    def __init__(self, task_info : TaskDescription, type='None') -> None:
        super().__init__(task_info, type)
        if not os.path.exists("saved"):
            os.makedirs("saved")
        mypath = "saved/"
        onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
        name = self.type + str(self.id) + ".json"
        found = False
        while not found:
            if name in onlyfiles:
                name = self.type + str(self.getNewID()) + ".json"
            else:
                found = True

        self.path = mypath + name 


        self.gen_req = self.init + self.prompt + self.endi

        if self.parent is None:
            self.msg_list = []
        else:
            self.msg_list = self.parent.msg_list

        chat = SimpleChatGPT()
        pair = {}
        pair["role"] = chat.getUserTag()
        pair["content"] = self.prompt

        tmp_msg_list = self.msg_list
        tmp_msg_list.append(pair)
        msg_list_from_file = self.getResponseFromFile(tmp_msg_list)
        del tmp_msg_list
        
        if len(msg_list_from_file) == 0:
            pair = {}
            pair["role"] = chat.getUserTag()
            pair["content"] = self.gen_req
            self.msg_list.append(pair)
            res, out = chat.recvRespFromMsgList(self.msg_list)
            if res:
                print("out=", out)
                pair = {}
                pair["role"] = chat.getAssistTag()
                pair["content"] = out
                self.msg_list.append(pair)

            self.saveJsonToFile(self.msg_list)
        else:
            self.msg_list = msg_list_from_file
            print("Get list from file=", self.path)

    def saveJsonToFile(self, msg_list):
        resp_json_out = {}
        resp_json_out['chat'] = msg_list 
        resp_json_out['type'] = self.type
        path = ""
        if self.parent:
            path = self.parent.path
        resp_json_out['parent'] = path
        with open(self.path, 'w') as f:
            print("save to file=", self.path)
            json.dump(resp_json_out, f, indent=1)

        
        
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
        request = self.init + self.prompt + self.endi
        responses = self.getResponse(request)
        if len(responses) == 0:
            chat = SimpleChatGPT()
            self.user = chat.getUserTag()
            self.chat = chat.getAssistTag()
            res, text = chat.recvResponse(request)
            if res:
                self.saveRespJson(request, responses)

    def getResponseFromFile(self, msg_list):
        mypath = "saved/"
        onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
        for file in onlyfiles:
            if file.startswith(self.type):
                path = mypath + file
        # if os.stat(self.path).st_size != 0:
                try:
                    with open(path, 'r') as f:
                        rq = json.load(f)
                    if 'chat' in rq:
                        msg_trgs = rq['chat']
                        res = False
                        for msg in msg_list:
                            res = False
                            for trg in msg_trgs:
                                if trg["content"] == msg["content"]:
                                    res = True
                                    break
                        if res:
                            self.path = path
                            return msg_trgs
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


class ChatGPTTask(TextTask):
    def __init__(self, task_info : TaskDescription) -> None:
        super().__init__(task_info, "Information")
        self.request_to = self.init + self.prompt + self.endi
        print("Start ChatGPT")
        responses = self.getResponse(self.request_to)
        if len(responses) == 0:
            class_responses = self.requester.getResponse(self.request_to)
            for elem in class_responses:
                responses.append(elem.info)
            self.saveRespJson(self.request_to, responses)
        self.results = []
        self.marker = len(responses)
        for response in responses:
            self.addChildTask(TaskDescription( prompt= response, method= GoogleTask,parent= self.results))


    def completeTask(self):
        if len(self.results) == self.marker:
            return True
        return False


class GoogleTask(TextTask):
    def __init__(self, task_info : TaskDescription) -> None:
        super().__init__(task_info, "Google")
    # def __init__(self, reqhelper: ReqHelper, requester: Requester, prompt=None, parent=None, method=None) -> None:
    #     super().__init__(reqhelper, requester, "Google", prompt, parent, method)
        self.searcher = GoogleApiSearcher()
        print("Start Google")
        links = self.getResponse( task_info.prompt)
        if len(links) == 0:
            links = self.searcher.getSearchs(task_info.prompt)
            self.saveRespJson( task_info.prompt, links)

    # def completeTask(self):
    #     responses = self.request
    #     links = self.getResponse( responses)
    #     if len(links) == 0:
    #         for resp in responses:
    #             search_list = self.searcher.getSearchs(resp)
    #             for sr in search_list:
    #                 links.append(sr)
    #                 # log += sr + '\n'
    #         self.saveRespJson( responses, links)
    #     return links
    
class BrowserTask(TextTask):
    def __init__(self, task_info : TaskDescription) -> None:
        super().__init__(task_info, "Browser")
    # def __init__(self, browser : Browser, reqhelper: ReqHelper, requester: Requester, type='Browser', prompt=None, parent=None, method=None) -> None:
    #     super().__init__(reqhelper, requester, type, prompt, parent, method)
        self.browser = browser
    def completeTask(self):
        if self.checkFile():
            return self.openTxt()
        # text = self.browser.getData(self.prompt)
        # self.saveTxt(text)
        # return text
        return ""
    
class SummaryTask(TextTask):
    def __init__(self, task_info : TaskDescription) -> None:
        super().__init__(task_info, "Summary")
    # def __init__(self, summator : Summator, reqhelper: ReqHelper, requester: Requester, type='Summary', prompt=None, parent=None, method=None) -> None:
        # super().__init__(reqhelper, requester, type, prompt, parent, method)
        self.summator = summator
        print('Summary task')
    def completeTask(self):
        print('Complete task')
        self.summator.processText(self.prompt)

class RichTextTask(TextTask):
    def __init__(self, task_info : TaskDescription) -> None:
        super().__init__(task_info, "RichText")
    # def __init__(self, reqhelper: ReqHelper, requester: Requester, prompt=None, parent=None, method=None) -> None:
        # super().__init__(reqhelper, requester, "RichText", prompt, parent, method)

        # request = self.init + self.prompt + self.endi
        # responses = self.getResponse(request)
        # if len(responses) == 0:
        #     chat = ChatGPTsimple()
        #     response =  chat.getResponse(request)
        #     responses.append(response)
        #     self.saveRespJson(request, responses)
        # print("response=",responses)
        # self.richtext = responses
        # print("task=",task_info.target)
        # self.task_id = task_info.id


    def completeTask(self):
        print("target=",self.target)
        self.is_solved = True
        if self.target:
            print("Add text:", self.richtext)
            self.target(self.richtext[0], self.task_id)
        return True

        