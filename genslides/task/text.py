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

from genslides.utils.llmodel import LLModel

import genslides.utils.savedata as savedata
import genslides.utils.writer as wr
from genslides.utils.loader import Loader


import json
import os
from os import listdir
from os.path import isfile, join
import pprint
import re
import ast
import genslides.utils.finder as finder

class TextTask(BaseTask):
    def __init__(self, task_info: TaskDescription, type='None') -> None:
        super().__init__(task_info, type)

        print("Type=", self.getType())

        self.path = self.getPath()
        self.copyParentMsg()

        self.params = task_info.params

        print('Path to my file=', self.path)

        self.caretaker = None

        print('Input params',task_info.params)
        print('Task params',self.params)
        self.updateParam2({'type':'task_creation','time':savedata.getTimeForSaving()})
    
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
        # print("Print queue init",self.getName())
        q_names = [q["name"] for q in self.queue if 'name' in q]
        p_names = [p["name"] for p in self.params if "name" in p]
        c_names = [ch.getName() for ch in self.getChilds()]
        # print("Queue:", q_names)
        # print("Params:", p_names)
        # print("Childs:", c_names)
 
    def updateNameQueue(self, old_name : str, new_name : str):
        if old_name == new_name:
            return
        trg = None
        # print("queue:", self.queue)
        # print("params:", self.params)
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
        # print("pack:",pack)
        self.params.append(self.getJsonQueue(pack))
        return pack
    
    def getLinkQueuePack(self, info: TaskDescription) -> dict:
        print('Check param link queue pack')
        for param in self.params:
            if "type" in param and param["type"] == "link" and "name" in param and param["name"] == info.target.getName():
                out = param.copy()
                return out
        pack = super().getLinkQueuePack(info)
        print('Get default link queue pack',pack)
        self.params.append(self.getJsonQueue(pack))
        return pack
    
    def syncParamToQueue(self):
        print('Sync', self.getName(), 'param to queue')
        # print('Init param=', self.params)
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
        # print('After sync param=', self.params)
    
    def syncQueueToParam(self):
        print("Sync",self.getName(),"queue to param")
        # print(10*'===','Queue:', self.queue)
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

    def checkParentMsgList(self, update = False, remove = True, save_curr = True) -> bool:
        if self.parent:
            print('Check msg list of',self.getName(),'with', self.parent.getName())
            trg = self.parent.msg_list.copy()
            src = self.msg_list.copy()
            last = None
            if len(src) > 0 and remove:
                last = src.pop()
            if trg != src:
                if update:
                    if last and save_curr:
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
    
    def setMsgList(self, msgs):
        self.msg_list = msgs
 
    def copyParentMsg(self):
        self.msg_list = self.getRawParentMsgs()
        
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
    
    def replaceImMsgs(self, trg_old, trg_new):
        for msg in self.msg_list:
            text = msg['content']
            text.replace(trg_old, trg_new)
            msg['content'] = text
 
    def getMsgs(self, except_task = []):
        # print("Get msgs excluded ",except_task)
        task = self
        index = 0
        out = []
        while(index < 1000):
            res, msg, par = task.getLastMsgAndParent()
            if res and task.getName() not in except_task:
                # print(task.getName(),"give", len(msg), "msg")
                msg.extend(out)
                out = msg
            if par is None:
                break
            else:
                task = par
            index += 1

        return out
   
    def getRawMsgs(self):
        return self.msg_list.copy()
    
    def getRawParentMsgs(self):
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
        for msg in self.getMsgs():
            text += msg["content"]

        res, param = self.getParamStruct('model')
        if res:
            chat = LLModel(param)
        else:
            chat = LLModel()
        return chat.getPrice(text)
    
    def getUsedTasks(self) -> list:
        msgs = self.getMsgs()
        res, param = self.getParamStruct('model')
        if res:
            chat = LLModel(param)
        else:
            chat = LLModel()
        trg_msgs = chat.checkTokens(msgs)
       
        par_tasks = self.getAllParents()
        out = []
        for par in par_tasks:
            par_msgs = par.getMsgs()
            found = False
            for msg in par_msgs:
                if msg in trg_msgs:
                    found = True
                    break
            if not found:
                break
            else:
                out.append(par)
        return out
    
    def setManager(self, manager):
        super().setManager(manager)
        self.removeJsonFile()
        self.path = self.getPath()
        self.saveJsonToFile(self.msg_list)


    def getPath(self) -> str:
        mypath = self.manager.getPath()
        wr.checkFolderPathAndCreate(mypath)
        onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
        self.setName( self.getType() + str(self.id))
        print("Start Name =", self.name)
        name = self.name + self.manager.getTaskExtention()
        found = False
        n = self.name
        while not found:
            if name in onlyfiles:
                n = self.getType() + str(self.getNewID())
                name = n + self.manager.getTaskExtention()
            else:
                found = True
                print("Res Name=", n)
                self.setName(n)
        return os.path.join( mypath, name)

    def getJson(self):
        return self.getJsonMsg(self.msg_list)
    
    def resaveWithID(self, id : int):
        self.id = id
        old_path = self.path
        self.path = self.getPath()
        print('Rewrite',old_path,'to', self.path)
        os.remove(old_path)
        self.saveAllParams()
    
    def saveAllParams(self):
        self.saveJsonToFile(self.msg_list)


    def getJsonMsg(self, msg_list):
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
        if self.parent and self.caretaker is None:
            path = self.parent.getClearName()
        resp_json_out['parent'] = path
        return resp_json_out
    
    def removeJsonFile(self):
        os.remove(self.path)
    
    def saveJsonToFile(self, msg_list):
        resp_json_out = self.getJsonMsg(msg_list)
        print("Save json to", self.path,"msg[",len(msg_list),"] params[", len(self.params),"]")
        with open(self.path, 'w') as f:
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
            chat = LLModel()
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
        mypath = self.manager.getPath()
        onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
        trg_file = self.filename + self.manager.getTaskExtention()
        # for file in onlyfiles:
        if trg_file in onlyfiles:
            file = trg_file
            if file.startswith(self.getType()):
                path = os.path.join(mypath, file)
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
        mypath = self.manager.getPath()
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
        print(self.getName(), 'update link to', [t.getName() for t in self.getAffectedTasks()])
        if len(self.msg_list) == 0:
            return
        text = self.msg_list[len(self.msg_list) - 1]["content"]
        text = self.findKeyParam(text)
        for task in self.affect_to_ext_list:
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
        # TODO: check why???? Переделать пусть тип задачи решает сколько нужно оставить
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
        print('Check input')
        if input:
            self.prompt = input.prompt
            self.prompt_tag = input.prompt_tag
            print('Params:', input.params)
            for param in input.params:
                if 'name' in param and 'value' in param and 'prompt' in param:
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
        print('Update', param_name, key, 'with', val,'for', self.getName())
        if isinstance(val,str):
            print('get str')
        elif isinstance(val,list):
            print('get list')
        else:
            print('not str and not list')
        for param in self.params:
            if "type" in param and param["type"] == param_name:
                if key in param:
                    if isinstance(val, str) and isinstance(param[key], list):
                        param[key] = ast.literal_eval(val)
                    else:
                        param[key] = val
        print('Res params=',self.params)
        self.saveJsonToFile(self.msg_list)

    def getCurParamStructValue(self, param_name, key):
        for param in self.params:
            if "type" in param and param["type"] == param_name:
                if key in param:
                    return True, param[key]
        return False, ''

    def setParamStruct(self, param):
        # print('Init params=',self.params)
        if 'type' in param:
            self.params.append(param)
        self.saveJsonToFile(self.msg_list)

    def rmParamStruct(self, param):
        try:
            self.params.remove(param)
            self.saveJsonToFile(self.msg_list)
        except Exception as e:
            print('Error on remove param:',e)
 

    def getParamStruct(self, param_name, only_current = False):
        # print('Get in param', param_name, 'struct')
        forbidden_names = finder.getExtTaskSpecialKeys()
        if param_name not in forbidden_names and not only_current:
            parent_task = self.parent
            index = 0
            while(index < 1000):
                if parent_task is None:
                    break
                res, parent_task, val = parent_task.getParamStructFromExtTask(param_name)
                if res:
                    return True, val
        # print('Search in self params')
        for param in self.params:
            if "type" in param and param["type"] == param_name:
                return True, param
        return False, None
 
    
    def getParamList(self):
        forbidden_names = finder.getExtTaskSpecialKeys()
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
        self.syncParamToQueue()
        self.saveJsonToFile(self.msg_list)

    def getParam(self, param_name):
        forbidden_names = finder.getExtTaskSpecialKeys()
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
    
    def findKeyParam(self, text: str):
         manager = self.manager
         base = self
         return finder.findByKey(text, manager, base )

    def getAllParams(self):
        return json.dumps(self.params, indent=1)
    
    def afterRestoration(self):
        self.saveJsonToFile(self.msg_list)

 