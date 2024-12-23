import genslides.task.text as TextTask
import genslides.task_tools.records as rd
import genslides.task_tools.text as txt
import json

class LinkedTask(TextTask.TextTask):
    def __init__(self, task_info: TextTask.TaskDescription, type='Linked') -> None:
        super().__init__(task_info, type)
        self.callback_link = []

    def checkParentsMsg(self):
        if self.parent:
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
        return []

    def checkInputInternal(self, input :TextTask.TaskDescription = None):
        if input:
            if self.parent:
                trg_list = self.checkParentsMsg()
            else:
                trg_list = []
            self.updateCollectedMsgList(trg_list)



    def checkInput(self, input: TextTask.TaskDescription = None):
        super().checkInput(input)
        self.checkInputInternal(input)

    def updateCollectedMsgList(self, trg_list : list):
        # print("update collected msg list")
        last = {"content" : self.getRichPrompt(), "role" : self.prompt_tag}
        self.appendMessage(last)
        self.saveAllParams()

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

    def createLinkToTask(self, task) -> TextTask.TaskDescription:
        id = len(self.by_ext_affected_list)
        # print("Create link to ", task.getName(),"id=", id)
        out = TextTask.TaskDescription(method=self.affectedTaskCallback, id=id, parent=task , target=self)
        self.by_ext_affected_list.append(out)
        
        task.setLinkToTask(out)
        return super().createLinkToTask(task) 

    def updateLinkedPrompts(self, input : TextTask.TaskDescription):
        for tsk_info in self.by_ext_affected_list:
            if input.id == tsk_info.id:
                
                tsk_info.prompt = input.prompt
                tsk_info.enabled = input.enabled
                # print("Task[", tsk_info.id,"].enabled=",tsk_info.enabled)
                # print('New prompt:', tsk_info.prompt)

    def affectedTaskCallback(self, input : TextTask.TaskDescription):
        print("From ", input.parent.getName(), " to ", self.getName())
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
 
    def removeLinkToTask(self):
        # print(self.getName(), 'remove links to task')
        self.prompt = ""
        # self.update()
        self.freezeTask()
        super().removeLinkToTask()
        self.saveJsonToFile(self.msg_list)

    def whenParentRemoved(self):
        super().whenParentRemoved()
        self.removeLinkToTask()

class ListenerTask(LinkedTask):
    def __init__(self, task_info: TextTask.TaskDescription, type='Listener') -> None:
        super().__init__(task_info, type)    
        # sres, sparam = self.getParamStruct('listener', True)
        # if not sres:
        #     self.setParamStruct({
        #                     "type":"listener",
        #                     "actions":[]
        #                     })
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

    def update(self, input: TextTask.TaskDescription = None):
        out = super().update(input)
        return out

    def updateIternal(self, input: TextTask.TaskDescription = None):
        # print('Update Internal')
        if not self.is_freeze:
            self.updateCollectedMsgList(self.checkParentsMsg())
        return super().updateIternal(input)
 
    def checkInputInternal(self, input = None):
        pass


    def updateLinkedPrompts(self, input : TextTask.TaskDescription):
        for tsk_info in self.by_ext_affected_list:
            if input.id == tsk_info.id:
                # print('Upd by ', input.parent.getName())
                hash = txt.compute_sha256_hash(input.prompt)
                if tsk_info.type != hash:
                    tsk_info.enabled = input.enabled
                    tsk_info.prompt = input.prompt
                    tsk_info.params = input.params
                    tsk_info.type = hash
                return

    def getRichPrompt(self) -> str:
        # print('Get rich prompt', self.getName())
        lres, lparam = self.getParamStruct("listener")
        # if lres:
        #     if lparam['hash'] != "":
        #         return self.prompt
        prompt = ""
        params = []
        updated = False
        for tsk_info in self.by_ext_affected_list:
            # print('Upd listener from',tsk_info.parent.getName())
            if 'combine' in lparam:
                if lparam['combine'] == 'single':
                    if tsk_info.enabled:
                        prompt = tsk_info.prompt
                        params.extend(tsk_info.params)
                        tsk_info.enabled = False
                        updated = True
                        break
            else:
                prompt += tsk_info.prompt
                params.extend(tsk_info.params)
        if not updated:
            return self.prompt
        if lres:
            curr_hash = lparam['hash']
            if lparam['input'] == 'prompt':
                input_hash = txt.compute_sha256_hash(prompt)
                # print('Check hash')
                if curr_hash != input_hash:
                    print(self.getName(),'get prompt:', len(prompt))
                    if 'output' in lparam:
                        if lparam['output'] == 'prompt':
                            self.prompt = prompt
                        elif lparam['output'] == 'param':
                            lparam['data'] = prompt
                    else:
                        self.prompt = prompt
                    lparam['hash'] = input_hash
            elif lparam['input'] == 'params':
                input_hash = txt.compute_sha256_hash(json.dumps(params))
                if curr_hash != input_hash:
                    self.prompt = prompt
                    lparam['hash'] = input_hash
                    for param in params:
                        self.setParamStruct(param)
            self.setParamStruct(lparam)
        return self.prompt
    
    def forceCleanChat(self):
        self.prompt = ""
        lres, lparam = self.getParamStruct("listener")
        if lres:
            lparam['hash'] = ""
            if lparam['input'] == 'params':
                params = []
                for tsk_info in self.by_ext_affected_list:
                    params.extend(tsk_info.params)
                for param in params:
                    if 'type' in param:
                        self.rmParamStructByName(param['type'])
        return super().forceCleanChat()

    def createLinkToTask(self, task) -> TextTask.TaskDescription:
        lres, lparam = self.getParamStruct("listener")
        if not lres:
            self.setParamStruct({
              "type": "listener",
                "input": "prompt",
                "output":"prompt",
                "hash": "",
                "combine": "single"
            })
        return super().createLinkToTask(task)
    
    def getInLinkInfo(self, trg):
        lres, lparam = self.getParamStruct("listener")
        if lres and 'onedit' in lparam:
            if lparam['onedit'] == 'collect':
                if 'garland_opt' in lparam:
                    return {'out': trg, 'in': self, 'dir': 'out','option':'move'}
        return super().getInLinkInfo(trg)
    
    def getTrgLinkInfo(self, trg):
        lres, lparam = self.getParamStruct("listener")
        if lres and 'onedit' in lparam:
            if lparam['onedit'] == 'collect':
                if 'garland_opt' in lparam:
                    if lparam['garland_opt'] == 'insert_move':
                        return True, {'out': trg, 'in': self, 'dir': 'in','option':'move'}
                return True, {'out': trg, 'in': self, 'dir': 'in'}
            elif lparam['onedit'] == 'garland':
                oparam = {'out': trg, 'in': self, 'dir':'out',
                                   'insert':True,
                                   'option':'std',
                                   'type': self.getType(),
                                   'tag': self.prompt_tag,
                                   'prompt':'',
                                   'parent': self.parent
                                   }
                if 'garland_opt' in lparam:
                    if lparam['garland_opt'] == 'insert_sub':
                        oparam['insert'] = True
                        oparam['option'] = 'sub'
                    elif lparam['garland_opt'] == 'insert_move':
                        oparam['insert'] = True
                        oparam['option'] = 'move'
                elif 'garland_actions' in lparam:
                    oparam['actions'] = self.findKeyParam(lparam['garland_actions'])
                return True, oparam


        return super().getTrgLinkInfo(trg)
    

    def stdProcessUnFreeze(self, input=None):        
        if self.checkBlock():
            self.is_freeze = True
            return
        lres, lparam = self.getParamStruct("listener")

        if lres and 'onupdate' in lparam:
            if lparam['onupdate'] == 'chck_link_chld':
                self.unfreezeByCheckingLinkedAndChildren()
            elif lparam['onupdate'] == 'none':
                super().stdProcessUnFreeze(input)
        else:
            self.unfreezeByCheckingLinkedAndChildren()

    def unfreezeByCheckingLinkedAndChildren(self):
        if self.parent and self.parent.is_freeze:
            self.freezeTask()
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
                self.is_freeze = False
            else:
                pass

        else:
            for tsk_info in self.by_ext_affected_list:
                if not tsk_info.enabled:
                    print("Freeze from children")
                    self.freezeTask()
                    return
 