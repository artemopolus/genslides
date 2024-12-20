from genslides.task.text import TextTask
from genslides.task.base import TaskDescription
import genslides.task_tools.records as rd
import genslides.task.link as Ltask

class ReceiveTask(Ltask.LinkedTask):
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

          


    def freezeTask(self):
        # print('[=]',self.getName(),"is freeze!")
        self.is_freeze = True
        for tsk_info in self.by_ext_affected_list:
            tsk_info.enabled = False



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

    
    def stdProcessUnFreeze(self, input=None):
        
        # res, pparam = self.getParamStruct('block')
        if self.is_blocking():
            self.is_freeze = True
            return

        # print("1 frozen=", self.is_freeze)
        # print(self.getName(),' task is frozen:', self.is_freeze)
        if self.parent and self.parent.is_freeze:
            self.freezeTask()
            # print(self.getName(),"parent frozen=",self.parent.is_freeze)
            return
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



   
    
    def findNextFromQueue(self, only_check = False, trgtasknames = []):
        res = super().findNextFromQueue(only_check=only_check,trgtasknames=trgtasknames)
        if res:
            return res
        # for cl in self.callback_link:
        #     if cl["used"] == False:
        #         cl["used"] = True
        #         return cl["pt"].findNextFromQueue()
        return None




    def getMsgInfo(self):
        if len(self.msg_list) > 0:
            out = self.msg_list[- 1]
            return "", out["role"],out["content"]
        else:
            return "", self.prompt_tag, ""    
    


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
                            'insert':True,
                            'option':'std'
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
            if 'option' in sparam:
                oparam['option'] = sparam['option']
        return True, oparam

