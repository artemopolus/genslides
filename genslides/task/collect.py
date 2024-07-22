from genslides.task.text import TextTask
from genslides.task.base import TaskDescription
import pprint
from genslides.utils.largetext import SimpleChatGPT
import genslides.task_tools.records as rd

import json

class ReceiveTask(TextTask):
    def __init__(self, task_info : TaskDescription, type = "Receive") -> None:
        super().__init__(task_info, type=type)

        self.is_freeze = True
        tmp_msg_list = self.msg_list.copy()
        msg_list_from_file = self.getResponseFromFile(tmp_msg_list)

        self.afterFileLoading()
        
        if len(msg_list_from_file) == 0:
            # self.updateCollectedMsgList(tmp_msg_list)
            self.onEmptyMsgListAction()
        else:
            # print("Get list from file=", self.path)
            self.onExistedMsgListAction(msg_list_from_file)
            # self.setMsgList(msg_list_from_file)


        self.callback_link = []

    def onEmptyMsgListAction(self):
        self.hasNoMsgAction()
        return super().onEmptyMsgListAction()

    def onExistedMsgListAction(self, msg_list_from_file):
        self.haveMsgsAction(msg_list_from_file)
        return super().onExistedMsgListAction(msg_list_from_file)

    
    def isReceiver(self) ->bool:
        return True

    def afterFileLoading(self):
        pass

    def hasNoMsgAction(self):
        tmp_msg_list = self.msg_list.copy()
        self.updateCollectedMsgList(tmp_msg_list)

    def haveMsgsAction(self, msgs):
        self.setMsgList(msgs)

    def checkInput(self, input: TaskDescription = None):
        super().checkInput(input)
        if input:
            if self.parent:
                trg_list = self.checkParentsMsg()
            else:
                trg_list = []
            self.updateCollectedMsgList(trg_list)
           


    def freezeTask(self):
        # print('[=]',self.getName(),"is freeze!")
        self.is_freeze = True
        for tsk_info in self.by_ext_affected_list:
            tsk_info.enabled = False

    def updateCollectedMsgList(self, trg_list : list):
        # print("update collected msg list")
        last = {"content" : self.getRichPrompt(), "role" : self.prompt_tag}
        trg_list.append(last)
        self.setMsgList( trg_list.copy())
        self.saveJsonToFile(self.msg_list)


    def checkParentsMsg(self):
            trg_list = self.parent.msg_list.copy()
            cur_list = self.msg_list.copy()
            cut = cur_list.pop()
            if cur_list != trg_list:
                trg_list.append(cut)
                self.setMsgList( trg_list)
                self.saveJsonToFile(self.msg_list)
                # print("Freeze => parents msgs not equal target")
                self.freezeTask()
            return trg_list


    def update(self, input : TaskDescription = None):
        # print("Update collect_________________________________________________")
        # print("Collect",10*">>>>>>>>>>>")
        # print("Prompt=", self.getRichPrompt())
        trg_list = []
        if self.parent:
            trg_list = self.checkParentsMsg()
        else:
            trg_list = []
        
        if not self.is_freeze:
            self.updateCollectedMsgList(trg_list)
        super().update(input)
        # print("CollectTask=",self.getName()," frozen=", self.is_freeze)
        if len(self.msg_list) > 0:
            out = self.msg_list[len(self.msg_list) - 1]
            return out["content"], out["role"]
        else:
            return "",""

    def createLinkToTask(self, task) -> TaskDescription:
        id = len(self.by_ext_affected_list)
        # print("Create link to ", task.getName(),"id=", id)
        out = TaskDescription(method=self.affectedTaskCallback, id=id, parent=task , target=self)
        self.by_ext_affected_list.append(out)
        
        task.setLinkToTask(out)
        return super().createLinkToTask(task) 
    
    def getRichPrompt(self) -> str:
        # TODO: Перенести сюда заполнение шаблона
        res, param = self.getParamStruct('linkedfrom')
        text = ""
        if res:
            names = param['tasks']
            checkers = [t.getName() for t in self.getAffectingOnTask()]
            # print('=================>>>>>>>>>>>>Check', names, '==',checkers)
            # print(set(names) ==set(checkers))
            # for name in names:
                # print('Check',name,':',name in checkers)
            if set(names).difference(set(checkers)) == set():
                # print('Yes')
                for t in names:
                    for intask in self.by_ext_affected_list:
                        if intask.parent.getName() == t:
                            text += intask.prompt + '\n'
            else:
                print('No')
            return text
        eres, eparam = self.getParamStruct(self.getType(), only_current=True)
        for task in self.by_ext_affected_list:
            # print("Copy data from", task.parent.getName())
            try:
                if eres and eparam['input'] == 'records':
                    res, param = task.parent.getParamStruct(param_name='records', only_current=True)
                    if res:
                        text += rd.getRecordsRow(param, eparam)
                elif eres and eparam['input'] == 'request':
                    text += eparam['header'] + task.prompt + eparam['footer']    
                else:
                    text += task.prompt
            except Exception as e:
                text += task.prompt

        # print('Result:', text)
        return text

    def stdProcessUnFreeze(self, input=None):
        
        res, pparam = self.getParamStruct('block')
        if res and pparam['block']:
            self.is_freeze = True
            return

        # print("1 frozen=", self.is_freeze)
        # print(self.getName(),' task is frozen:', self.is_freeze)
        if self.parent:
            # print(self.getName(),"parent frozen=",self.parent.is_freeze)
            pass
        if self.is_freeze:
            to_unfreeze = False
            if self.parent and not self.parent.is_freeze:
                to_unfreeze = True
            elif not self.parent and self.is_freeze:
                to_unfreeze = True
            if to_unfreeze:
                # print('Try unfreeze cz parent')
                if len(self.by_ext_affected_list) == 0:
                    return
                for tsk_info in self.by_ext_affected_list:
                    # print("\t\tLink input=", tsk_info.parent.getName(),"=",tsk_info.enabled)
                    if not tsk_info.enabled:
                        return
                # print("Unfreeze")
                self.is_freeze = False
                # print("Task",self.getName(),"is freeze:",self.is_freeze)
            else:
                # print('Parent is frozen=> can\'t update')
                pass

        else:
            # print('Update input for Collect task')
            for tsk_info in self.by_ext_affected_list:
                # print("Inp par=", tsk_info.parent.getName(),"=",tsk_info.enabled)
                if not tsk_info.enabled:
                    print("Freeze from children")
                    self.freezeTask()
                    return
            # print("1 frozen=", self.is_freeze)
                
    def printLinkState(self):
        pass
        # print('Link[',self.getName(),'] state:',[(tsk_info.parent.getName(),tsk_info.enabled) for tsk_info in self.by_ext_affected_list])


    def updateLinkedPrompts(self, input : TaskDescription):
        for tsk_info in self.by_ext_affected_list:
            if input.id == tsk_info.id:
                
                tsk_info.prompt = input.prompt
                tsk_info.enabled = input.enabled
                # print("Task[", tsk_info.id,"].enabled=",tsk_info.enabled)
                # print('New prompt:', tsk_info.prompt)


    def affectedTaskCallback(self, input : TaskDescription):
        # print("From ", input.parent.getName(), " to ", self.getName())
        if input and input.stepped:
            found = False
            for cl in self.callback_link:
                if cl["pt"] == input.parent:
                    cl["used"] = False
                    found = True
                    break
            if not found:
                self.callback_link.append({"pt":input.parent,"used": False})
                found = True
            if found:
                self.resetTreeQueue()

        self.updateLinkedPrompts(input=input)

        out = super().affectedTaskCallback(input)
        self.stdProcessUnFreeze()
        # if input and input.stepped:
        #     pass
        #     # info = TaskDescription(prompt=self.getLastMsgContent(), prompt_tag=self.getLastMsgRole(),stepped=input.stepped)
        #     # self.update(info)
        # else:
        #     self.update()
    
    
    def findNextFromQueue(self, trgtasknames = []):
        res = super().findNextFromQueue(trgtasknames=trgtasknames)
        if res:
            return res
        # for cl in self.callback_link:
        #     if cl["used"] == False:
        #         cl["used"] = True
        #         return cl["pt"].findNextFromQueue()
        return None



    def removeLinkToTask(self):
        self.prompt = ""
        # self.update()
        self.freezeTask()
        super().removeLinkToTask()
        self.saveJsonToFile(self.msg_list)
 
    def getMsgInfo(self):
        if len(self.msg_list) > 0:
            out = self.msg_list[- 1]
            return "", out["role"],out["content"]
        else:
            return "", self.prompt_tag, ""    
    
    def whenParentRemoved(self):
        super().whenParentRemoved()
        self.removeLinkToTask()



    def getInfo(self, short = True) -> str:
        out = ""
        for task in self.by_ext_affected_list:
            out += task.parent.getName()
        return out
    
    def setParamStruct(self, param):
        if 'type' in param and param['type'] == 'linkedfrom':
            param['tasks'] = [t.getName() for t in self.getAffectingOnTask()]
        return super().setParamStruct(param)
    
    def getTrgLinkInfo(self, trg):
        return True, {'out': trg, 'in': self, 'dir': 'in'}

    # просто задача Receive не должна замораживать себя и наследников
class CollectTask(ReceiveTask):
    def __init__(self, task_info: TaskDescription, type='Collect') -> None:
        super().__init__(task_info, type)
class GarlandTask(CollectTask):
    def __init__(self, task_info: TaskDescription, type="Garland") -> None:
        super().__init__(task_info, type)
        sres, sparam = self.getParamStruct('garland', True)
        if not sres:
            self.setParamStruct({
                            'type':'garland',
                            'insert':True
                            })
 
    def isLinkForCopy(self):
        return False

    def getTrgLinkInfo(self, trg):
        oparam = {'out': trg, 'in': self, 'dir':'out',
                                   'insert':True,
                                   'type': self.getType(),
                                   'tag': self.prompt_tag,
                                   'prompt':'',
                                   'parent': self.parent
                                   }
        sres, sparam = self.getParamStruct('garland', True)
        if sres:
            oparam['insert'] = sparam['insert']
        return True, oparam

