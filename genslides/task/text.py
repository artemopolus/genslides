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

import json
import os
from os import listdir
from os.path import isfile, join

class TextTask(BaseTask):
    def __init__(self, reqhelper: ReqHelper, requester: Requester, type='None', prompt=None, parent=None, method=None) -> None:
        super().__init__(reqhelper, requester, type, prompt, parent, method)
        if not os.path.exists("saved"):
            os.makedirs("saved")
        self.path = "saved/" + self.type + str(self.id) + ".json"
        path = self.path
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
    def __init__(self, reqhelper: ReqHelper, requester: Requester, prompt=None, parent=None, method=None) -> None:
        super().__init__(reqhelper, requester, "Information", prompt, parent, method)
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
    def __init__(self, reqhelper: ReqHelper, requester: Requester, prompt=None, parent=None, method=None) -> None:
        super().__init__(reqhelper, requester, "Google", prompt, parent, method)
        self.searcher = GoogleApiSearcher()
        print("Start Google")
        links = self.getResponse( prompt)
        if len(links) == 0:
            links = self.searcher.getSearchs(prompt)
            self.saveRespJson( prompt, links)

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
    def __init__(self, browser : Browser, reqhelper: ReqHelper, requester: Requester, type='Browser', prompt=None, parent=None, method=None) -> None:
        super().__init__(reqhelper, requester, type, prompt, parent, method)
        self.browser = browser
    def completeTask(self):
        if self.checkFile():
            return self.openTxt()
        # text = self.browser.getData(self.prompt)
        # self.saveTxt(text)
        # return text
        return ""
    
class SummaryTask(TextTask):
    def __init__(self, summator : Summator, reqhelper: ReqHelper, requester: Requester, type='Summary', prompt=None, parent=None, method=None) -> None:
        super().__init__(reqhelper, requester, type, prompt, parent, method)
        self.summator = summator
        print('Summary task')
    def completeTask(self):
        print('Complete task')
        self.summator.processText(self.prompt)

class RichTextTask(TextTask):
    def __init__(self, reqhelper: ReqHelper, requester: Requester, prompt=None, parent=None, method=None) -> None:
        super().__init__(reqhelper, requester, "RichText", prompt, parent, method)
        request = self.init + self.prompt + self.endi
        responses = self.getResponse(request)
        if len(responses) == 0:
            chat = ChatGPTsimple()
            response =  chat.getResponse(request)
            responses.append(response)
            self.saveRespJson(request, responses)
        print("response=",responses)
        self.task_description = request

        