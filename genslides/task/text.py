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

from genslides.utils.savedata import SaveData
from genslides.utils.loader import Loader
from genslides.task.base import TaskManager

import json
import os
from os import listdir
from os.path import isfile, join
import pprint
import re


class TextTask(BaseTask):
    def __init__(self, task_info: TaskDescription, type='None') -> None:
        super().__init__(task_info, type)

        print("Type=", self.getType())

        self.path = self.getPath()
        self.copyParentMsg()
        self.params = []
    
    def addChild(self, child) -> bool:
        if super().addChild(child):
            self.syncQueueToParam()
            self.printQueueInit()
            self.saveJsonToFile(self.msg_list)
            return True
        return False
    
    def removeChild(self,child) -> bool:
        if super().removeChild(child):
            self.syncQueueToParam()
            trg =  None
            for param in self.params:
                if "type" in param and "name" in param and param['type'] == 'child' and param['name'] == child.getName():
                    trg = param
            print("Remove from param", trg)
            if trg is not None and trg in self.params:
                self.params.remove(trg)
            self.printQueueInit()
            self.saveJsonToFile(self.msg_list)
            return True
        return False
    
    def fixQueueByChildList(self):
        super().fixQueueByChildList()
        q_names = [q['name'] for q in self.queue if 'name' in q]
        to_del = []
        for param in self.params:
            if 'type' in param and param['type'] == 'child' and 'name' in param:
                if param['name'] not in q_names:
                    to_del.append(param)
        for p in to_del:
            self.params.remove(p)
        self.syncQueueToParam()
    
    def printQueueInit(self):
        print("Data from",self.getName())
        q_names = [q["name"] for q in self.queue if 'name' in q]
        p_names = [p["name"] for p in self.params if "name" in p]
        c_names = [ch.getName() for ch in self.getChilds()]
        print("Queue:", q_names)
        print("Params:", p_names)
        print("Childs:", c_names)
 
    def updateNameQueue(self, old_name : str, new_name : str):
        if old_name == new_name:
            return
        trg = None
        # print("queue:", self.queue)
        print("params:", self.params)
        for param in self.params:
            if "type" in param and "name" in param and param["name"] == old_name:
                trg = param
        print("Delete param:",trg)
        if trg:
            self.params.remove(trg)
            for info in self.queue:
                if info["name"] == old_name:
                    trg = info
        if trg:
            self.queue.remove(trg)
        self.syncParamToQueue()
        # print("queue:", self.queue)
        # print("params:", self.params)
        self.printQueueInit()
       
        self.saveJsonToFile(self.msg_list)

    def getChildQueuePack(self, child) -> dict:
        for param in self.params:
            if "type" in param and param["type"] == "child" and "name" in param and param["name"] == child.getName():
                out = param.copy()
                return out
        pack = super().getChildQueuePack(child)
        print("pack:",pack)
        self.params.append(self.getJsonQueue(pack))
        return pack
    
    def getLinkQueuePack(self, info: TaskDescription) -> dict:
        for param in self.params:
            if "type" in param and param["type"] == "link" and "name" in param and param["name"] == info.target.getName():
                out = param.copy()
                return out
        pack = super().getLinkQueuePack(info)
        self.params.append(self.getJsonQueue(pack))
        return pack
    
    def syncParamToQueue(self):
        print('Sync param to queue')
        for param in self.params:
            if "type" in param:
                if param['type'] == 'child' or param['type'] == 'link':
                    found = False
                    for q in self.queue:
                        try:
                            if q["name"] == param["name"]:
                                q.update(param)
                                found = True
                        except:
                            pass
                    if not found:
                        self.queue.append(param)
        qd = []
        for q in self.queue:
            if 'name' in q:
                found = False
                for param in self.params:
                    if 'name' in param and param['name'] == q['name']:
                        found = True
                if not found:
                    qd.append(q)
        
        for q in qd:
            self.queue.remove(q)
    
    def syncQueueToParam(self):
        print("Sync",self.getName(),"queue to param")
        # print('Queue:', self.queue)
        for pack in self.queue:
            found = False
            for param in self.params:
                if "type" in param  and "name" in param and 'name' in pack and param["name"] == pack["name"]:
                    if param["type"] == "child":
                        pass
                    elif param["type"] == "link":
                        pass
                    else:
                        continue
                    param.update(self.getJsonQueue(pack))
                    found = True
                    break
            if not found:
                self.params.append(self.getJsonQueue(pack))
        self.saveJsonToFile(self.msg_list)

    def onQueueReset(self, info):
        print("Queue reset")
        super().onQueueReset(info)
        self.syncQueueToParam()

    def onQueueCheck(self, param) -> bool:
        if super().onQueueCheck(param):
            self.syncQueueToParam()
            return True
        return False

    def checkParentMsgList(self, update = False, remove = True) -> bool:
        print('Check msg list')
        if self.parent:
            trg = self.parent.msg_list.copy()
            src = self.msg_list.copy()
            last = None
            if len(src) > 0 and remove:
                last = src.pop()
            if trg != src:
                if update:
                    if last:
                        trg.append(last)
                    self.msg_list = trg
                return False
        return True

    def getLastMsgContent(self):
        if len(self.msg_list) > 0:
            return self.msg_list[-1]["content"]
        return "Empty"
    
    def getLastMsgRole(self):
        if len(self.msg_list) > 0:
            return self.msg_list[-1]["role"]
        return "None"
 
    def copyParentMsg(self):
        self.msg_list = self.getParentMsg()
        
    def getLastMsgAndParent(self) -> (bool, list, BaseTask):
        val = [{"role":self.getLastMsgRole(), "content": self.findKeyParam(self.getLastMsgContent())}]
        return True, val, self.parent

    def getMsgByIndex(self, i_trg):
        task = self
        index = 0
        while(index < 1000):
            res, msg, par = task.getLastMsgAndParent()
            if res and i_trg == index:
                # print(task.getName(),"give", len(msg), "msg to", out)
                return True, msg
            if par is None:
                break
            else:
                task = par
            index += 1
        return False, None
 
    def getMsgs(self, except_task = []):
        # print("Get msgs excluded ",except_task)
        task = self
        index = 0
        out = []
        while(index < 1000):
            res, msg, par = task.getLastMsgAndParent()
            if res and task.getName() not in except_task:
                # print(task.getName(),"give", len(msg), "msg to", out)
                msg.extend(out)
                out = msg
            if par is None:
                break
            else:
                task = par
            index += 1

        return out
   
    def getParentMsg(self):
        if self.parent is None:
            return []
        else:
            out =  self.parent.msg_list.copy()
            return out
        
    def forceCleanChildsChat(self):
        chs4clean = self.childs
        index = 0
        while(index < 1000 and len(chs4clean) > 0):
            chs4clean_next = []
            for child in chs4clean:
                child.forceCleanChat()
                for ch in child.childs:
                    chs4clean_next.append(ch)
            chs4clean = chs4clean_next.copy()

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
        task_man = TaskManager()
        mypath = task_man.getPath()
        onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
        self.setName( self.getType() + str(self.id))
        print("Start Name =", self.name)
        name = self.name + task_man.getTaskExtention()
        found = False
        n = self.name
        while not found:
            if name in onlyfiles:
                n = self.getType() + str(self.getNewID())
                name = n + task_man.getTaskExtention()
            else:
                found = True
                print("Res Name=", n)
                self.setName(n)
        return mypath + name

    def getJson(self):
        resp_json_out = {
            'name': self.getName(),
            'chat': self.msg_list,
            'type': self.getType(),
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
            'type': self.getType(),
            'params': self.params
        }
        linked = []
        for info in self.by_ext_affected_list:
            linked.append(info.parent.getName())
        resp_json_out['linked'] = linked
        path = ""
        if self.parent:
            path = self.parent.getClearName()
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

    def resetResetableParams(self, params):
        for param in params:
            try:
                param['cur'] = param['str']
            except:
                pass
        return params
    
    def checkLoadCondition(self, msg_trgs, msg_list) -> bool:
        if msg_trgs == msg_list:
            return True
        return False
    
    def getResponseFromFile(self, msg_list, remove_last=True):
        print("Get response from file:")
        task_man = TaskManager()
        mypath = task_man.getPath()
        onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
        trg_file = self.filename + task_man.getTaskExtention()
        # for file in onlyfiles:
        if trg_file in onlyfiles:
            file = trg_file
            if file.startswith(self.getType()):
                path = mypath + file
                try:
                    print('Open file by path', path)
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
                        if self.checkLoadCondition(msg_trgs, msg_list) or stopped or self.is_freeze:
                            print(10*"====", "\nLoaded from file:",path)
                            self.path = path
                            self.setName(file.split('.')[0])
                            if 'params' in rq:
                                self.params = self.resetResetableParams(rq['params'])
                            return rq['chat']
                        else:
                            print(10*"====", "\nLoaded from file:",path)
                            self.is_freeze = True
                            self.path = path
                            self.setName(file.split('.')[0])
                            if 'params' in rq:
                                self.params = self.resetResetableParams(rq['params'])
                            return rq['chat']
                            # print('No right data in file')
                    else:
                        print('No chat in file')
                except json.JSONDecodeError as e:
                    print('Json error',e)
        return []

    def getResponse(self, request):
        task_man = TaskManager()
        mypath = task_man.getPath()
        onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
        for file in onlyfiles:
            if file.startswith(self.getType()):
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
        text = self.findKeyParam(text)
        # input = TaskDescription(prompt=text, parent=self)
        for task in self.affect_to_ext_list:
            # task.prompt = text
            input = task
            input.prompt = text
            input.enabled = not self.is_freeze
            input.parent = self
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
        if len(self.msg_list) > 0:
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

    def checkInput(self, input: TaskDescription = None):
        if input:
            self.prompt = input.prompt
            self.prompt_tag = input.prompt_tag
            for param in input.params:
                self.updateParam(param["name"], param["value"],param["prompt"])
            
            if input.parent:
                self.parent = input.parent
                self.parent.addChild(self)
                print("New parent=", self.parent)

            self.saveJsonToFile(self.msg_list)

    def getBranchedName(self) -> str:
        index = 0
        trg = self
        names = self.getName() + "_"
        while(index < 1000):
            par = trg.parent
            if par == None:
                break
            # print("type=",par.getType())
            if par.getType() == "Iteration":
                pname = par.getName().replace("Iteration","It")
                res, i = par.getParam("index")
                print("it_res_i",res,i)
                if res:
                    names += pname + "_" + i + "_"
            elif par.getType() == "IterationEnd":
                if par.iter_start:
                    trg = par.iter_start.parent
            else:
                pass
            trg = par
            index += 1
        return names

    def update(self, input: TaskDescription = None):
        self.checkInput(input)
        out = super().update(input)



        return out

    def getInfo(self, short=True) -> str:
        if len(self.msg_list) > 0:
            sprompt = self.msg_list[-1]['content']
        else:
            sprompt = self.prompt
        if short and len(sprompt) > 20:
            return sprompt[0:20] + "..."
        else:
            return sprompt
        
    def updateParam2(self, param_vals : dict):
        if 'type' in param_vals:
            param_name = param_vals['type']
        else:
            return
        for param in self.params:
            if 'type' in param and param['type'] == param_name:
                param.update(param_vals)
                return
        self.params.append(param_vals)


    def updateParam(self, param_name, data, add_param = None):
            found = False
            # print(add_param)
            for param in self.params:
                if param_name in param:
                    param[param_name] = data
                    if add_param is not None:
                        param.update(add_param)
                    found = True
            if not found:
                param_new = {"type": param_name, param_name: data}
                if add_param is not None:
                    param_new.update(add_param)
                self.params.append(param_new)

    def getParamFromExtTask(self, param_name):
        return False, self.parent, None

    def getParamStructFromExtTask(self, param_name):
        return False, self.parent, None
     
    def updateParamStruct(self, param_name, key,val):
        for param in self.params:
            if "type" in param and param["type"] == param_name:
                if key in param:
                    param[key] = val
        self.saveJsonToFile(self.msg_list)
 

    def getParamStruct(self, param_name):
        # print("Search for", param_name,"in", self.getName())
        forbidden_names = ['input', 'output', 'stopped']
        if param_name not in forbidden_names:
            parent_task = self.parent

            index = 0
            while(index < 1000):
                if parent_task is None:
                    break
                res, parent_task, val = parent_task.getParamStructFromExtTask(param_name)
                if res:
                    return True, val
        for param in self.params:
            if "type" in param and param["type"] == param_name:
                return True, param
        return False, None
 
    
    def getParamList(self):
        forbidden_names = ['input', 'output', 'stopped']
        out = []
        for p in self.params:
            if 'type' in p:
                if p['type'] not in forbidden_names:
                    out.append(p)
        return out
    
    def setParam(self, param):
        print("Set param:", param)
        if isinstance(param, str):
            self.params = json.loads(param)
        elif isinstance(param, list):
            self.params = param
        else:
            return
        self.saveJsonToFile(self.msg_list)

    def getParam(self, param_name):
        forbidden_names = ['input', 'output', 'stopped']
        if param_name not in forbidden_names:
            parent_task = self.parent

            index = 0
            while(index < 1000):
                if parent_task is None:
                    break
                res, parent_task, val = parent_task.getParamFromExtTask(param_name)
                if res:
                    return True, val
        # если ничего не нашли загружаем стандартное
        # print("Params=",self.params)
        for param in self.params:
            for k,p in param.items():
                # print("k=",k,"p=",p)
                if param_name == k:
                    return True, p
                
        
        res, default_value =  self.reqhelper.getValue(self.getType(), param_name)
        if res:
            return True, default_value
        # print("Found nothing for", param_name)
        return False, None
    
    def getMsgTag(self)-> str:
        return "msg_content"

    def findKeyParam(self, text: str):
         results = re.findall(r'\{.*?\}', text)
        #  print("Find keys=", text)
        #  print("Results=", results)
         rep_text = text
         for res in results:
             arr = res[1:-1].split(":")
            #  print("Keys:", arr)
             if len(arr) > 1:
                 task = self.getAncestorByName(arr[0])
                 if task:
                    if len(arr) > 5:
                        if 'type' == arr[1]:
                            bres, pparam = task.getParamStruct(arr[2])
                            if bres and arr[3] in pparam and pparam[arr[3]] == arr[4] and arr[5] in pparam:
                                rep = pparam[arr[5]]
                                rep_text = rep_text.replace(res, str(rep))
                    elif arr[1] == self.getMsgTag():
                        param = task.getLastMsgContent()
                        if len(arr) > 3 and arr[2] == 'json':
                            bres, j = Loader.loadJsonFromText(param)
                            if bres:
                                rep = j[arr[3]]
                                rep_text = rep_text.replace(res, str(rep))
                            else:
                                print("No json in", task.getName())
                        else:
                            print("Replace", res, "from",task.getName())
                            rep_text = rep_text.replace(res, str(param))
                    else:
                        p_exist, param = task.getParam(arr[1])
                        if p_exist:
                            # print("Replace ", res, " with ", param)
                            rep_text = rep_text.replace(res, str(param))
                        else:
                            # print("No param")
                            pass
                 else:
                    #  print("No task", arr[0])
                     pass
             else:
                # print("Incorrect len")
                pass
         return rep_text

    def getAllParams(self):
        return json.dumps(self.params, indent=1)

 