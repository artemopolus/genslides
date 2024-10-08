from genslides.task.base import BaseTask
from genslides.task.base import TaskDescription

import genslides.utils.reqhelper as ReqHelper
import genslides.utils.request as Requester
import genslides.utils.browser as Browser
import genslides.utils.browser as WebBrowser
import genslides.utils.largetext as Summator
import genslides.utils.readfileman as Reader
import genslides.utils.filemanager as FileMan

from genslides.utils.searcher import GoogleApiSearcher
from genslides.utils.chatgptrequester import ChatGPTrequester
from genslides.utils.chatgptrequester import ChatGPTsimple

from genslides.utils.llmodel import LLModel

import genslides.utils.savedata as savedata
import genslides.utils.writer as wr
from genslides.utils.loader import Loader
from genslides.utils.llmodel import LLModel


import json
import os
from os import listdir
from os.path import isfile, join
import pprint
import re
import ast
import genslides.utils.finder as finder
import genslides.task_tools.array as ar
import genslides.task_tools.records as rd
import copy

class TextTask(BaseTask):
    def __init__(self, task_info: TaskDescription, type='None') -> None:
        self.checkparentsettrue = False
        self.msg_list = []
        self.params = task_info.params
        # print('Get params', self.params)
        super().__init__(task_info, type)

        # print("Type=", self.getType())

        self.path = self.getPath()
        self.copyParentMsg()

        # print('Get params to', self.getName(),':\n', task_info.params)


        # print('Path to my file=', self.path)

        self.caretaker = None

        # print('Input params',task_info.params)
        # print('Task params',self.params)
        self.updateParam2({'type':'task_creation','time':savedata.getTimeForSaving()})       
        self.updateParam2({'type':'branch','code':self.getBranchCodeTag()})       
        self.stdProcessUnFreeze()

    def setCheckParentForce(self, val : bool):
        self.checkparentsettrue = val

    def onEmptyMsgListAction(self):
        print('On empty msg list', self.getName())

    def onExistedMsgListAction(self, msg_list_from_file):
        pass

    def loadInitParam(self):
        init_params = self.reqhelper.getParams(self.getType())
        for param in init_params:
            if 'type' in param:
                found = False
                for p in self.params:
                    if 'type' and p['type'] == param['type']:
                        found = True
                        break
                if not found:
                    self.setParamStruct(param)
    
    def addChild(self, child) -> bool:
        # if self.getName() == 'Response250':
        #     print('---')
        #     print('Add child', child.getName(),'to',self.getName())
        #     self.printQueueInit()
        #     print('---')
        if super().addChild(child):
            # print('Add child', child.getName(),'to',self.getName())
            self.syncQueueToParam()
            res, pparam = self.getParamStruct('bud', only_current=True)
            if res:
                child_tasks = child.getAllChildChains()
                for task in child_tasks:
                    if len(task.getChilds()) == 0:
                        tparam = {'type':'bud','text': pparam['text'],'branch':task.getBranchCodeTag()}
                        task.setParamStruct(tparam)
                self.rmParamStructByName('bud')
            self.updateParam2({'type':'branch','code':self.getBranchCodeTag()})       

            self.saveJsonToFile(self.msg_list)
            return True
        return False
    
    def getPrio(self):
        if self.parent is None:
            return super().getPrio()
        pparam = self.parent.getAllParams()
        for p in pparam:
            if 'type' in p and p['type'] == 'child' and p['name'] == self.getName():
                return p['idx']
        return super().getPrio()
    
    def getQueueParam(self) -> dict:
        par = self.getParent()
        if par:
            pparams = par.getAllParams()
            for p in pparams:
                if 'type' in p and p['type'] == 'child' and p['name'] == self.getName():
                    return p
        return {}

    def setQueueParam(self, qparam) -> dict:
        if 'type' in qparam and qparam['type'] == 'child' and qparam['name'] == self.getName():
            par = self.getParent()
            if par:
                pparams = par.params
                for p in pparams:
                    if 'type' in p and p['type'] == 'child' and p['name'] == self.getName():
                        p.update(qparam)
                        par.saveAllParams()
                        return
                        
    
    def setPrio(self, idx : int):
        if self.parent is None:
            return super().setPrio()
        for p in self.getParent().params:
            if 'type' in p and p['type'] == 'child' and p['name'] == self.getName():
                p['idx'] = idx
        self.getParent().saveAllParams()
        return super().setPrio(idx)

    
    def removeChild(self,child) -> bool:
        print('Remove child', child.getName())
        if super().removeChild(child):
            self.syncQueueToParam()
            trg =  None
            for param in self.params:
                if "type" in param and "name" in param and param['type'] == 'child' and param['name'] == child.getName():
                    trg = param
            print("Remove from param", trg)
            if trg is not None and trg in self.params:
                self.params.remove(trg)
            # self.printQueueInit()
            self.saveJsonToFile(self.msg_list)
            return True
        return False
    
    def resetLinkToTask(self, info : TaskDescription) -> None:
        super().resetLinkToTask(info)
        trg = None
        for p in self.params:
            if p['type'] == 'link' and p['name'] == info.target.getName():
                print('Remove link to',info.target.getName())
                trg = p
                break
        if trg is not None:
            self.params.remove(trg)
        self.syncParamToQueue()
        self.saveAllParams()



    def fixQueueByChildList(self):
        # print('Fix queue by child list')
        super().fixQueueByChildList()
        q_names = [q['name'] for q in self.queue if 'name' in q]
        to_del = []
        used_names = []
        for param in self.params:
            if 'type' in param and param['type'] == 'child' and 'name' in param:
                name = param['name']
                if name in used_names:
                    to_del.append(param)
                else:
                    used_names.append(name)
                if name not in q_names:
                    to_del.append(param)
        for p in to_del:
            self.params.remove(p)
        self.syncQueueToParam()
    
    def printQueueInit(self):
        # print("Print queue init",self.getName())
        q_names = [q["name"] for q in self.queue if 'name' in q]
        p_names = [p["name"] for p in self.params if "name" in p]
        c_names = [ch.getName() for ch in self.getChilds()]
        print("Queue:", q_names)
        print("Params:", p_names)
        print("Childs:", c_names)
 
    def updateNameQueue(self, old_name : str, new_name : str):
        # if self.getName() == 'Response250':
        #     print(self.getName(), 'update queue name:',old_name,'=>', new_name)
        if old_name == new_name:
            return
        trg = None
        # print("queue:", self.queue)
        # print("params:", self.params)
        found = False
        for param in self.params:
            if "type" in param and "name" in param and param["name"] == new_name:
                found = True
        if not found:
            for param in self.params:
                  if "type" in param and "name" in param and param["name"] == old_name:
                       param["name"] = new_name
        else:
            for param in self.params:
                  if "type" in param and "name" in param and param["name"] == old_name:
                      trg = param
 
        # print("Delete param:",trg)
        if trg:
            self.params.remove(trg)
        #     for info in self.queue:
        #         if info["name"] == old_name:
        #             trg = info
        # if trg:
        #     self.queue.remove(trg)
        self.syncParamToQueue()
        # print("queue:", self.queue)
        # print("params:", self.params)
        # self.printQueueInit()
       
        self.saveJsonToFile(self.msg_list)

    def getChildQueuePack(self, child, idx) -> dict:
        for param in self.params:
            if "type" in param and param["type"] == "child" and "name" in param and param["name"] == child.getName():
                out = param.copy()
                return out
        pack = super().getChildQueuePack(child, idx)
        # print("pack:",pack)
        # print('Append to', self.getName(),'pack', child.getName())
        # self.params.append(self.getJsonQueue(pack))
        return pack
    
    def getLinkQueuePack(self, info: TaskDescription) -> dict:
        # print('Check param link queue pack')
        for param in self.params:
            if "type" in param and param["type"] == "link" and "name" in param and param["name"] == info.target.getName():
                out = param.copy()
                return out
        pack = super().getLinkQueuePack(info)
        # print('Get default link queue pack',pack)
        self.params.append(self.getJsonQueue(pack))
        return pack
    
    def syncParamToQueue(self):
        # if self.getName() == 'SetOptions41':
        #     print('Sync', self.getName(), 'param to queue')
        #     print('Init param=', self.params)
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
                # print('Append to', self.getName(),'pack',pack["name"])
                self.params.append(self.getJsonQueue(pack))
        # if self.getName() == 'SetOptions41':
        #     print("Sync",self.getName(),"queue to param")
        #     print('Param', self.params)
        #     print('Queue:', self.queue)
        self.saveJsonToFile(self.msg_list)

    def onQueueReset(self, info):
        # print("Queue reset")
        super().onQueueReset(info)
        # self.syncQueueToParam()

    def onQueueCheck(self, param) -> bool:
        # print('On queue check')
        if super().onQueueCheck(param):
            self.syncQueueToParam()
            return True
        return False

    def checkParentMsgList(self, update = False, remove = True, save_curr = True) -> bool:
        if self.checkparentsettrue:
            return True
        if self.parent:
            # print('Check msg list of',self.getName(),'with', self.parent.getName())
            trg = self.getParent().getMsgList()
            src = self.getMsgList()
            last = None
            if len(src) > 0 and remove:
                last = src.pop()
            if trg != src:
                diff = [t for t in trg if t not in src]
                dif2 = [t for t in src if t not in trg]
                # print('Diff:', diff)
                # print('Diff:', dif2)
                if update:
                    if last and save_curr:
                        trg.append(last)
                    self.setMsgList( trg )
                return False
        return True
    
    def getPromptContentForCopy(self):
    # Сделать отдельную функцию для получения последнего сообщения и переопределить его в SetOptions и ExtProject. В противном случае, при редактировании будут отображаться не те данные, которые были введены изначально. Дублирует по свойствам getLastMsgContent, но замена может повлиять на многие функции, поэтому оставляем изменение к следующеему этапу тестирования.
        if len(self.msg_list) > 0:
            return self.msg_list[-1]["content"]
        else:
            return ""
        
    def getPromptContentForCopyConverted(self):
        if len(self.msg_list) > 0:
            return self.findKeyParam( self.msg_list[-1]["content"])
        else:
            return ""
   

    def getLastMsgContentRaw(self):
        if len(self.msg_list) > 0:
            return self.getRawMsgs()[-1]['content']
        else:
            return ""

    def getLastMsgContent2(self):
        if len(self.msg_list) > 0:
            return self.findKeyParam ( self.getRawMsgs()[-1]['content'] )
        else:
            return ""

    def getLastMsgContent(self):
        if len(self.msg_list) > 0:
            return self.msg_list[-1]["content"]
        return "Empty"
    
    def getLastMsgRole(self):
        return self.prompt_tag
        # if len(self.msg_list) > 0:
            # return self.msg_list[-1]["role"]
        # return "None"
    
    def setMsgList(self, msgs):
        self.msg_list = msgs

    def getMsgList(self):
        return copy.deepcopy(self.msg_list)
 
    def copyParentMsg(self):
        self.msg_list = self.getRawParentMsgs()
        
    def getLastMsgAndParent(self, hide_task = True) -> (bool, list, BaseTask):
        if hide_task:
            res, pparam = self.getParamStruct('hidden', only_current=True)
            if res and pparam['hidden']:
                return False, [], self.parent
        # можно получать не только последнее сообщение, но и группировать несколько сообщений по ролям
        val = [{"role":self.getLastMsgRole(), 
                "content": self.findKeyParam(self.getLastMsgContent())}]
        if self.parent != None:
            self.parent.setActiveBranch(self)
        return True, val, self.parent

   
    def freeTaskByParentCode(self):
        pass

    def getParentForFinder(self):
        return self.getParent()

    def getParentForRaw(self):
        return self.getParent()
    
    def getLastMsgAndParentRaw(self, idx : int) -> list[bool, list, BaseTask]:
        idx += 1
        content = '[[parent_' + str(idx) + ':msg_content]]\n' if idx != 1 else '[[parent:msg_content]]\n'
        content += self.getName() + '\n'
        if len(self.getGarlandPart()):
            content += ','.join([t.getName() for t in self.getGarlandPart()]) + '->' + self.getName() + '\n'
        if len(self.getHoldGarlands()):
            content += self.getName() + '->' + ','.join([t.getName() for t in self.getHoldGarlands()]) + '\n'
        content += '\n\n---\n\n'
        content += self.getLastMsgContent()
        content +='\n'
        val = [{"role":self.getLastMsgRole(), 
                "content": content}]
        if self.parent != None:
            self.parent.setActiveBranch(self)
        return True, val, self.getParentForRaw()

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
 
    def getMsgs(self, except_task = [], hide_task = True):
        # print("Get msgs excluded ",except_task)
        rres, rparam = self.getParamStruct("response")
        if rres and "restricted_index" in rparam and rparam["restricted_index"]:
            target_index = rparam["index"]
        else:
            target_index = -1

        task = self
        index = 0
        out = []
        mres, mparam = self.getParamStruct("message")
        while(index < 1000):
            res, msg, par = task.getLastMsgAndParent(hide_task)
            if res and task.getName() not in except_task:
                # print(task.getName(),"give", len(msg), "msg", msg[-1]["role"]) 
                if mres and mparam["autoconnect"] and len(out) and out[0]["role"] == msg[-1]["role"]:
                    # print(out[0]["role"],"==", msg[-1]["role"])
                    text = mparam["prefix"] + msg[-1]["content"] + mparam["suffix"]
                    text += out[0]["content"]
                    out[0]["content"] = text
                else:
                    msg.extend(out)
                    out = msg
                # print(index, task.getName(),'give',len(out))
            if par is None:
                break
            elif target_index != -1 and index >= target_index:
                break
            else:
                task = par
            index += 1

        return out


    def getRawMsgsInfo(self, except_task = []):
        task = self
        index = 0
        out = []
        while(index < 1000):
            res, msg, par = task.getLastMsgAndParentRaw(index)
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

    def getCountPrice(self):
        # text = ""
        # for msg in self.getMsgs():
        #     text += msg["content"]

        res, param = self.getParamStruct('model')
        if res:
            chat = LLModel(param)
        else:
            chat = LLModel()
        # return chat.getPrice(text)
        return chat.getPriceFromMsgs(self.getMsgs())
    
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
        # проверять имена не только файлов в текущей папке, но и все имена задач менеджера, которые могут быть подключены как 
        mypath = self.manager.getPath()
        mypath = Loader.getUniPath(mypath)
        wr.checkFolderPathAndCreate(mypath)
        onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
        if self.getName() == '':
            self.setName( self.getType() + str(self.id))
        # print("Start Name =", self.name)
        name = self.name + self.manager.getTaskExtention()
        found = False
        n = self.name
        names = [t.getName() for t in self.manager.task_list]
        while not found:
            if name in onlyfiles:
                n = self.getType() + str(self.getNewID())
                name = n + self.manager.getTaskExtention()
            else:
                if n in names:
                    n = self.getType() + str(self.getNewID())
                    name = n + self.manager.getTaskExtention()
                else:
                    found = True
                # print("Res Name=", n)
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
 
    def saveAllParamsByPath(self, path : str):
        resp_json_out = self.getJsonMsg(self.msg_list)
        try:
            with open(path, 'w') as f:
                json.dump(resp_json_out, f, indent=1)
        except Exception as e:
            print('Can\'t save json file:', e)

    def getJsonMsg(self, msg_list):
        pout = self.params.copy()
        for p in pout:
            if 'type' in p and p['type'] == 'model' and 'api_key' in p:
                del p['api_key']
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
            path = self.parent.getClearName(self.manager)
        resp_json_out['parent'] = path
        return resp_json_out
    
    def removeJsonFile(self):
        os.remove(self.path)
    
    def saveJsonToFile(self, msg_list):
        resp_json_out = self.getJsonMsg(msg_list)
        # print("Save json to", self.path,"msg[",len(msg_list),"] params[", len(self.params),"]")
        try:
            with open(self.path, 'w') as f:
                json.dump(resp_json_out, f, indent=1)
        except Exception as e:
            print('Can\'t save json file:', e)

    def getJsonFilePath(self):
        return self.path

    def deleteJsonFile(self):
        path = Loader.getUniPath(self.path)
        print('Remove file', path)
        if os.path.exists(path):
            os.remove(path)

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
        mypath = self.manager.getPath()
        onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]

        if self.trgtaskname != "":
            targettaskfile = self.trgtaskname + self.manager.getTaskExtention()
            if targettaskfile in onlyfiles:
                targettask_path = FileMan.addFolderToPath(mypath,[targettaskfile])
                rq = Reader.ReadFileMan.readJson(Loader.getUniPath(targettask_path))
                if 'chat' in rq and 'param' in rq:
                    self.path = targettask_path
                    self.setName(self.trgtaskname)
                    self.params = self.resetResetableParams(rq['params'])
                    return rq['chat']

  
        # print("Get response from files:", onlyfiles)
        trg_file = self.filename + self.manager.getTaskExtention()
        # print('Target name:', trg_file)
        # for file in onlyfiles:
        if trg_file in onlyfiles:
            file = trg_file
            if file.startswith(self.getType()):
                path = os.path.join(mypath, file)
                try:
                    # print('Open file by path', path)
                    with open(path, 'r') as f:
                        rq = json.load(f)
                    if 'chat' in rq:
                        msg_trgs = rq['chat'].copy()
                        if remove_last and len(msg_trgs):
                            msg_trgs.pop()
                        stopped = False
                        if 'params' in rq:
                            # print("params=", rq['params'])
                            for param in rq['params']:
                                if 'stopped' in param and param['stopped']:
                                    stopped = True
                        if self.checkLoadCondition(msg_trgs, msg_list) or stopped or self.is_freeze:
                            # print(10*"====", "\nLoaded from file:",path)
                            self.path = path
                            self.setName(file.split('.')[0])
                            if 'params' in rq:
                                self.params = self.resetResetableParams(rq['params'])
                            return rq['chat']
                        else:
                            # print(10*"====", "\nLoaded from file:",path)
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

    def useLinksToTask(self, stepped = False):
        # print(self.getName(), 'update link to', [t.getName() for t in self.getAffectedTasks()])
        if len(self.msg_list) == 0:
            return
        text = self.msg_list[len(self.msg_list) - 1]["content"]
        text = self.findKeyParam(text)
        for task in self.affect_to_ext_list:
            input = task
            input.prompt = text
            input.enabled = not self.is_freeze
            input.parent = self
            input.stepped = stepped
            # print(self.getName(),'[ frozen=', self.is_freeze,'] linked to')
            task.method(input)

    def affectedTaskCallback(self, input: TaskDescription):
        pass
        # print("My name is ", self.getName())
        # print("My prompt now is ", self.getRichPrompt())
        # print("Msgs=",pprint.pformat(self.msg_list))

    def beforeRemove(self):
        super().beforeRemove()
        self.deleteJsonFile()

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
        res, pparam = self.getParamStruct('block')
        if res and pparam['block']:
            self.is_freeze = True
            return

        if self.parent:
            self.is_freeze = self.parent.is_freeze

        # res, is_input = self.getParam("input")
        # Инпут изначально планировался как средство остановки обновления до ожидания действий пользователя, теперь его "заменяет" блокировка, может быть он теперь и не нужен?
        res = False

        if res and is_input:
            if input and input.manual:
                self.is_freeze = False
            else:
                self.is_freeze = True
        else:
            if self.parent == None:
                self.is_freeze = False

    def checkInput(self, input: TaskDescription = None):
        # print('Check input')
        if input:
            self.prompt = input.prompt
            self.prompt_tag = input.prompt_tag
            # print('Params:', input.params)
            for param in input.params:
                if 'name' in param and 'value' in param and 'prompt' in param:
                    self.updateParam(param["name"], param["value"],param["prompt"])
            
            if input.parent:
                # self.parent = input.parent
                # self.parent.addChild(self)
                self.setParent(input.parent)
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
            if par.checkType("Iteration"):
                pname = par.getName().replace("Iteration","It")
                res, i = par.getParam("index")
                print("it_res_i",res,i)
                if res:
                    names += pname + "_" + i + "_"
            elif par.checkType("IterationEnd"):
                if par.iter_start:
                    trg = par.iter_start.parent
            else:
                pass
            trg = par
            index += 1
        return names
    
    def getTasksContent(self, except_task = []):
        task = self
        index = 0
        out = []
        while(index < 1000):
            res, msg, par = task.checkGetContentAndParent()
            if res and task.getName() not in except_task:
                msg.extend(out)
                out = msg
            if par is None:
                break
            else:
                task = par
            index += 1
        return out


    def checkGetContentAndParent(self) -> list[bool, list, BaseTask]:
        res, pparam = self.getParamStruct('hidden')
        if res and pparam['hidden']:
            return False, [], self.parent
        val = [rd.getPackForRecord(self.getLastMsgRole(), self.findKeyParam(self.getLastMsgContent()), self.getName())]
        if self.parent != None:
            self.parent.setActiveBranch(self)
        return True, val, self.parent

    def internalUpdateParams(self):
        self.setParamStruct({'type':'branch','code':self.getBranchCodeTag()})
        res, param = self.getParamStruct(param_name='records', only_current=True)
        if res:
            rres, rparam = rd.appendDataForRecord(param, self.getTasksContent())
            if rres:
                self.setParamStruct(rparam)
        if self.manager.allowUpdateInternalArrayParam():
            ares, aparam = self.getParamStruct(param_name='array', only_current=True)
            if ares:
                naparam = ar.checkArrayIteration(self.getLastMsgContent2(), aparam)
                self.updateParam2(naparam)

    def setRecordsParam(self):
        print('Set',self.getName(),'to recording')
        self.setParamStruct(rd.createRecordParam(self.getTasksContent()))

    def clearRecordParam(self):
        res, param = self.getParamStruct(param_name='records', only_current=True)
        if res:
            np = rd.clearRecordData(param)
            self.setParamStruct(np)


    def getChatRecords(self) ->list:
        res, param = self.getParamStruct(param_name='records', only_current=True)
        if res:
            return rd.getDataFromRecordParam(param)
        return []


    def update(self, input: TaskDescription = None):
        self.checkInput(input)
        out = super().update(input)
        self.internalUpdateParams()
        # self.updateParamStruct(param_name='branch', key='code', val=self.getBranchCodeTag())
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
        if param_vals['type'] == 'array':
            res, np = ar.saveArrayToParams(self.getLastMsgContent2(),param_vals)
            if res:
                param_vals = np
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
        # print('Update', param_name, key, 'with', val,'for', self.getName())
        # if isinstance(val,str):
        #     print('get str')
        # elif isinstance(val,list):
        #     print('get list')
        # else:
        #     print('not str and not list')
        if param_name.startswith('child'):
            name = param_name.split(':')[1]
            for param in self.params:
                if "type" in param and param["type"] == 'child' and param['name'] == name:
                    param[key] = val
        else:
            for param in self.params:
                if "type" in param and param["type"] == param_name:
                    if key in param:
                        if param_name == 'array' and key == 'parse':
                            param[key] = val
                            nparam = ar.updateArrayParam(param)
                            param.update(nparam)
                        elif isinstance(val, str) and isinstance(param[key], list):
                            success = True
                            try:
                                value = ast.literal_eval(val)
                                success = True
                            except:
                                success = False
                            try:
                                value = json.loads(val)
                                success = True
                            except:
                                success = False
                            if success:
                                param[key] = value
                        else:
                            param[key] = val
                    else:
                        param[key] = val

        # print('Res params=',self.params)
        self.saveJsonToFile(self.msg_list)

    def getCurParamStructValue(self, param_name, key):
        for param in self.params:
            if "type" in param and param["type"] == param_name:
                if key in param:
                    return True, param[key]
        return False, ''

    def setParamStruct(self, param):
        self.updateParam2(param)
        # print('Init params=',self.params)
        # if 'type' in param:
            # self.params.append(param)
        if self.msg_list:
            self.saveJsonToFile(self.msg_list)

    def rmParamStructByName(self, param_name):
        trg = None
        for param in self.params:
            if 'type' in param and param['type'] == param_name:
                print('Remove', param['type'],'from', self.getName())
                trg = param
        if trg != None:
            self.params.remove(trg)
            self.saveJsonToFile(self.msg_list)

    def rewriteParamStruct(self, trg_param: dict):
        if 'type' in trg_param:
            param_name = trg_param['type']
        else:
            return False
        trg = None
        for param in self.params:
            if 'type' in param and param['type'] == param_name:
                print('Rewrite', param['type'],'from', self.getName())
                trg = param
        if trg != None:
            self.params.remove(trg)
            self.params.append(trg_param)
            self.saveJsonToFile(self.msg_list)
        else:
            print('Nothing to rewrite')
            return False
        return True



    def rmParamStruct(self, param):
        try:
            self.params.remove(param)
            self.saveJsonToFile(self.msg_list)
        except Exception as e:
            print('Error on remove param:',e)
 

    def getParamStruct(self, param_name, only_current = False):
        if not isinstance(param_name, str):
            return False, None
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
        if param_name.startswith('child'):
            name = param_name.split(':')[1]
            for param in self.params:
                if "type" in param and param["type"] == 'child' and param['name'] == name:
                    return True, param
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
    
    def findKeyParam(self, text: str)->str:
         manager = self.manager
         base = self
         idx = 0
         while idx < 10000:
             n_text, task, ress = finder.findByKey2(text, manager, base)
             idx +=1
             if task == base:
                 break
             elif ress == 0:
                 break
             else:
                 base = task
                 text = n_text
         return n_text
    
    def copyAllParams(self, copy_info = False):
        pparams = self.getAllParams()
        to_del = []
        for p in pparams:
            if 'type' in p and p['type'] == 'task_creation':
                to_del.append(p)
            if 'type' in p and p['type'] == 'child':
                to_del.append(p)
            if 'type' in p and p['type'] == 'link':
                to_del.append(p)
            if 'type' in p and p['type'] == 'copied':
                to_del.append(p)
            if 'type' in p and p['type'] == 'branch':
                to_del.append(p)
            # if 'type' in p and p['type'] == 'bud':
            #     to_del.append(p)
        for p in to_del:
            pparams.remove(p)

        if copy_info:
            found = False
            for p in pparams:
                if 'type' in p and p['type'] == 'copied':
                    found = True
                    p['cp_path'].append(self.getName())
                    break
            if not found:
                pparams.append({'type':'copied','cp_path':[self.getName()]})

        return pparams
        

    def getAllParams(self):
        pparams = copy.deepcopy(self.params)
        return pparams
    
    def afterRestoration(self):
        self.saveJsonToFile(self.msg_list)

    def setBranchSummary(self, summary : str):
        print('Set branch summary:', summary)
        pars = self.getAllParents()
        param = {'type':'summary','text': summary}
        pars[0].setParamStruct(param)
        

    def getBranchSummary(self) -> str:
        pars = self.getAllParents()
        res, param = pars[0].getParamStruct('summary')
        if res:
            return param['text']
        return pars[0].getName()
    
    def getWordTokenPairs(self):
        content = self.findKeyParam(self.getLastMsgContent())
        res, param = self.getParamStruct('model')
        output = []
        if res:
            chat = LLModel(param)
            words = content.split(" ")
            for word in words:
                msg = word
                tokens = chat.getTokensFromMessage(msg)
                output.append({"token": msg, "bytes": tokens})
        return output

    def getAutoCommand(self):
        tres, tparam = self.getParamStruct(self.getType() + "Cmd")
        if tres:
            return True, tparam['actions']
        return super().getAutoCommand()
    
    def setAutoCommand(self, type_name, actions):
        self.setParamStruct(
            {
                "type": type_name + "Cmd",
                "actions": actions
            }
        )       
