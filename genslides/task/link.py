import genslides.task.text as TextTask
import genslides.task_tools.records as rd
import genslides.task_tools.text as txt
import json
import genslides.utils.loader as Ld

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
                self.updateUpdationInfo("Freeze on check parent msg\n")
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
        self.updateUpdationInfo(f"Update from {input.parent.getName()}\n")
        # print("From ", input.parent.getName(), " to ", self.getName())
        # if input and input.stepped:
        #     found = False
        #     for cl in self.callback_link:
        #         if cl["pt"] == input.parent:
        #             cl["used"] = False
        #             found = True
        #             break
        #     if not found:
        #         self.callback_link.append({"pt":input.parent,"used": False})
        #         found = True
        #     if found:
        #         print('Reset tree Q')
                # self.resetTreeQueue()

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
    
    def allowUpdateCollectedMsg( self ):
        lres, lparam = self.getParamStruct("listener")
        if lres and "update_frozen" in lparam and lparam["update_frozen"]:
            return True
        if not self.is_freeze or input != None:
            return True
        return False

    def updateIternal(self, input: TextTask.TaskDescription = None):
        # print('Update Internal')
        if self.allowUpdateCollectedMsg():
            self.updateCollectedMsgList([])
        return super().updateIternal(input)
 
    def checkInputInternal(self, input = None):
        pass


    def updateLinkedPrompts(self, input : TextTask.TaskDescription):
        self.updateUpdationInfo(f"Update linked prompts")
        # lres, lparam = self.getParamStruct("listener")
        # if lres and 'onlink' in lparam:
        #     if lparam['onlink'] == 'none':
        #         pass
        #     elif lparam['onlink'] == 'check':
        #         parent_hash = self.calculateMsgsHash()
        #         if input.parent.is_freeze:
        #             return
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
        self.updateUpdationInfo("Get prompt\n")
        # print('Get rich prompt', self.getName())
        lres, lparam = self.getParamStruct("listener")
        if not lres:
            return self.prompt

        # if lres:
        #     if lparam['hash'] != "":
        #         return self.prompt
        prompt = ""
        if lparam['combine'] == 'json_list':
            prompts_data = []
        elif lparam['combine'] == 'json_append':
            jres, jobj = Ld.Loader.loadJsonFromText(self.prompt)
            if jres:
                prompts_data = jobj
            else:
                prompts_data = []
        elif lparam['combine'] == 'json_update':
            prompts_data = {}
        elif lparam['combine'] == 'json_dict':
            prompts_data = {}
        elif lparam['combine'].endswith('append'):
            if self.prompt == self.findKeyParam(lparam['init_prompt']):
                prompt = ""
            else:
                prompt = self.prompt
        params = []
        updated = False
        # if lres and 'init_prompt' in lparam:
        #     self.prompt = self.findKeyParam(lparam['init_prompt'])
        check_links = False
        if 'onlink' not in lparam:
            check_links = True
        else:
            if lparam['onlink'] == 'std':
                check_links = True
            elif lparam['onlink'] == 'check':
                parent_hash, text_hash = self.calculateMsgsHash()
                if 'msgs_hash' not in lparam:
                    check_links = True
                elif parent_hash != lparam['msgs_hash']:
                    self.updateUpdationInfo("Parent hash is updated\n")
                    check_links = True
                elif parent_hash == lparam['msgs_hash']:
                    self.updateUpdationInfo("Parent hash is same\n")
                else:
                    self.updateUpdationInfo("Unknown\n")
                lparam['msgs_hash'] = parent_hash
            else:
                self.updateUpdationInfo("Unknown reaction on linking\n")
        if check_links:
            prefix = lparam.get("prefix","")
            suffix = lparam.get("suffix","")
            trg_multi_on = lparam.get("trg_multi_on", False)
            link_dict_keys = []
            for tsk_info in self.by_ext_affected_list:
                self.updateUpdationInfo(f"Upd listener from {tsk_info.parent.getName()}")
                if 'combine' in lparam:
                    if lparam['combine'].startswith ('single'):
                        if tsk_info.enabled:
                            prompt += prefix + tsk_info.prompt + suffix
                            params.extend(tsk_info.params)
                            tsk_info.enabled = False
                            updated = True
                            break
                    elif lparam['combine'].startswith ('multi'):
                        if tsk_info.enabled:
                            if trg_multi_on:
                                trg_multi_tasks_names = txt.convertCommaSeparatedToList( lparam.get("trg_multi_tasks_names",""))
                                if tsk_info.parent.getName() in trg_multi_tasks_names:
                                    prompt += prefix + tsk_info.prompt + suffix
                                    updated = True
                                    self.updateUpdationInfo(f"Trg multi ALLOW: {tsk_info.parent.getName()}")
                                else:
                                    self.updateUpdationInfo(f"Trg multi decline: {tsk_info.parent.getName()}")
                                tsk_info.enabled = False
                            else:
                                prompt += prefix + tsk_info.prompt + suffix
                                tsk_info.enabled = False
                                updated = True
                    elif lparam['combine'].startswith("json"):
                        if tsk_info.enabled:
                            if lparam['combine'] == 'json_update':
                                jres, jobj = Ld.Loader.loadJsonFromText(tsk_info.prompt)
                                if jres:
                                    prompts_data.update( jobj)
                                else:
                                    self.updateUpdationInfo("Not valid for json_update")
                            elif lparam['combine'] == 'json_append':
                                jres, jobj = Ld.Loader.loadJsonFromText(tsk_info.prompt)
                                if jres:
                                    if isinstance(jobj, list) and isinstance(prompts_data, list):
                                        if tsk_info.parent != None:
                                            self.updateUpdationInfo(f"Extend list by {tsk_info.parent.getName()}")
                                        prompts_data.extend(jobj)
                                    else:
                                        prompts_data.append( jobj)
                                else:
                                    self.updateUpdationInfo("Not valid for json_append")
                            elif isinstance(tsk_info.params, list):
                                fres, forced_type = self.getParamValueByKey(tsk_info.params,'tag','forced_content_type')
                                kres, key = self.getParamValueByKey(tsk_info.params,'tag','key')
                                if fres and kres and forced_type != "any":
                                    self.updateUpdationInfo(f"Forced type[{key}]: {forced_type}")
                                    if forced_type == "prompt":
                                        if lparam['combine'] == 'json_list':
                                            link_dict_keys.append(key)
                                            prompts_data.append({key: tsk_info.prompt})
                                        elif lparam['combine'] == 'json_dict':
                                            link_dict_keys.append(key)
                                            prompts_data.update({key: tsk_info.prompt})
                                    elif forced_type == "json":
                                        jres, jobj, jreport = Ld.Loader.loadJsonFromTextStr(tsk_info.prompt)
                                        keys_info = ",".join([k for k, v in jobj.items()])
                                        self.updateUpdationInfo(f"Update json with {keys_info}")
                                        if jres:
                                            if lparam['combine'] == 'json_list':
                                                prompts_data.append(jobj)
                                            elif lparam['combine'] == 'json_dict':
                                                prompts_data.update(jobj)
                                        else:
                                            self.updateUpdationInfo(jreport)
                                    elif forced_type == "key_json":
                                        jres, jobj, jreport = Ld.Loader.loadJsonFromTextStr(tsk_info.prompt)
                                        if jres:
                                            if lparam['combine'] == 'json_list':
                                                link_dict_keys.append(key)
                                                prompts_data.append({key: jobj})
                                            elif lparam['combine'] == 'json_dict':
                                                link_dict_keys.append(key)
                                                prompts_data.update({key: jobj})
                                        else:
                                            self.updateUpdationInfo(jreport)
                                    else:
                                        self.updateUpdationInfo("Unknown forced type")
                                elif lparam['combine'] == 'json_list':
                                    jres, jobj = Ld.Loader.loadJsonFromText(tsk_info.prompt)
                                    if jres:
                                        prompts_data.append(jobj)
                                    else:
                                        kres, key = self.getParamValueByKey(tsk_info.params,'tag','key')
                                        if kres:
                                            prompts_data.append({key: tsk_info.prompt})
                                        else:
                                            prompts_data.append(tsk_info.prompt)
                                elif lparam['combine'] == 'json_dict':
                                    self.updateUpdationInfo("Json dict")
                                    jres, jobj, jreport = Ld.Loader.loadJsonFromTextStr(tsk_info.prompt)
                                    if jres and isinstance( jobj, dict):
                                            for k, v in jobj.items():
                                                link_dict_keys.append( k )
                                            keys_info = ",".join([k for k, v in jobj.items()])
                                            self.updateUpdationInfo(f"Update dict with {keys_info}")
                                            prompts_data.update(jobj)
                                    elif jres and isinstance( jobj, list):
                                        kres, key = self.getParamValueByKey(tsk_info.params,'tag','key')
                                        if kres:
                                            prompts_data.update({key: jobj})
                                            link_dict_keys.append(key)
                                            self.updateUpdationInfo(f"Update list for {key}")
                                        else:
                                            self.updateUpdationInfo(f"No key for list")
                                    else:
                                        if not jres:
                                            self.updateUpdationInfo(jreport)
                                        else:
                                            self.updateUpdationInfo("Is not dict or list")
                                        kres, key = self.getParamValueByKey(tsk_info.params,'tag','key')
                                        if kres:
                                            self.updateUpdationInfo(f"Update prompt for {key}")
                                            prompts_data.update({key: tsk_info.prompt})
                                            link_dict_keys.append(key)
                                        else:
                                            self.updateUpdationInfo(f"No key for prompt")
                                else:
                                    self.updateUpdationInfo("Is not dict or list or prompt")

                            tsk_info.enabled = False
                            updated = True
                    else:
                        self.updateUpdationInfo("Is not json or multi or single")
                else:
                    prompt += prefix + tsk_info.prompt + suffix
                    params.extend(tsk_info.params)
                    updated = True
        else:
            self.updateUpdationInfo("Checks not pass\n")
        lparam["json_dict_link_keys"] = ",".join(link_dict_keys)
        if not updated:
            # if lres and 'init_prompt' in lparam:
                # self.prompt = self.findKeyParam(lparam['init_prompt'])
            self.updateUpdationInfo("No updates from linked\n")
            clear_nonupdated = lparam.get("clear_nonupdated", False)
            if clear_nonupdated:
                return ""
            else:
                return self.prompt
        if lres:
            if lparam['combine'].startswith("json"):
                prompt = Ld.Loader.convJsonToText(prompts_data)
            curr_hash = lparam['hash']
            if lparam['input'] == 'prompt':
                input_hash = txt.compute_sha256_hash(prompt)
                # print('Check hash')
                if curr_hash != input_hash:
                    self.updateUpdationInfo(f"get prompt: {len(prompt)} s")
                    if 'output' in lparam:
                        if lparam['output'] == 'prompt':
                            self.updateUpdationInfo(f"Update prompt with new{len(prompt)}\n")
                            self.prompt = prompt
                        elif lparam['output'] == 'param':
                            lparam['data'] = prompt
                    else:
                        self.prompt = prompt
                    lparam['hash'] = input_hash
            elif lparam['input'] == 'params':
                input_hash = txt.compute_sha256_hash(json.dumps(params))
                if curr_hash != input_hash:
                    self.prompt = "" 
                    lparam['hash'] = input_hash
                    for param in params:
                        self.setParamStruct(param)
            self.setParamStruct(lparam)
        return self.prompt
    
    def resetLinkedUpdation(self):
        for tsk_info in self.by_ext_affected_list:
            tsk_info.enabled = False

    
    def forceCleanChat(self):
        self.prompt = ""
        lres, lparam = self.getParamStruct("listener")
        if lres:
            if 'init_prompt' in lparam:
                self.prompt = self.findKeyParam(lparam['init_prompt'])
            lparam['hash'] = ""
            self.resetLinkedUpdation()
            if lparam['input'] == 'params':
                params = []
                for tsk_info in self.by_ext_affected_list:
                    params.extend(tsk_info.params)
                for param in params:
                    if 'type' in param:
                        self.rmParamStructByName(param['type'])
            self.updateCollectedMsgList([])
        return super().forceCleanChat()

    def createLinkToTask(self, task) -> TextTask.TaskDescription:
        lres, lparam = self.getParamStruct("listener")
        if not lres:
            self.setParamStruct({
              "type": "listener",
                "input": "prompt",
                "output":"prompt",
                "hash": "",
                "combine": "single",
                "onedit":"",
                "onupdate":"",
                "onlink":"none"
            })
        return super().createLinkToTask(task)
    
    def getInLinkInfo(self, trg):
        lres, lparam = self.getParamStruct("listener")
        if lres and 'onedit' in lparam:
            if lparam['onedit'] == 'collect':
                if 'garland_opt' in lparam:
                    return {'out': trg, 'in': self, 'dir': 'out','option':'move'}
        return super().getInLinkInfo(trg)
    
    def isLinkForCopy(self):
        lres, lparam = self.getParamStruct("listener")
        if lres and 'onedit' in lparam:
            if lparam['onedit'] == 'collect':
                return True
            elif lparam['onedit'] == 'garland':
                return False
        return super().isLinkForCopy()
    
    def getTrgLinkInfo(self, trg):
        lres, lparam = self.getParamStruct("listener")
        if lres and 'onedit' in lparam:
            if lparam['onedit'] == 'collect':
                oparam = {'out': trg, 'in': self, 'dir': 'in','prompt':''}
            elif lparam['onedit'] == 'garland':
                oparam = {'out': trg, 'in': self, 'dir':'in',
                                   'insert':True,
                                   'option':'std',
                                   'type': self.getType(),
                                   'tag': self.prompt_tag,
                                   'prompt':'',
                                   'parent': self.parent
                                   }
            if 'garland_opt' in lparam:
                if lparam['garland_opt'].startswith('insert_'):
                    oparam['insert'] = True
                    oparam['option'] = lparam['garland_opt'][7:]
            elif 'garland_actions' in lparam:
                oparam['actions'] = self.findKeyParam(lparam['garland_actions'])
            return True, oparam


        return super().getTrgLinkInfo(trg)
    
    def blockLinked(self):
        lres, lparam = self.getParamStruct("listener")
        if lres and 'onupdate' in lparam and lparam['onupdate'] in ['none']:
            if self.block_on:
                self.unBlockChildren()
            return
        return super().blockLinked()

    def stdProcessUnFreeze(self, input=None):    
        self.updateUpdationInfo("Std process unfreeze\n")    
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
                    self.updateUpdationInfo(f"Freeze from links")
                    self.freezeTask()
                    return
                
    def getConvertedType(self, convertions_list):
        for conv in convertions_list:
            if self.checkType(conv.get("src", "")):
                lres, lparam = self.getParamStruct("listener")
                if lres and 'input' in lparam and lparam['input'] == 'params':
                    return "SetOptions"
                return conv.get("trg", self.getType())
        return self.getType()
    
    def checkParameterForCopyAllParams(self, param):
        if 'type' in param and param['type'] == 'listener':
            return True
        return super().checkParameterForCopyAllParams(param)

    def getTaskReport(self, report):
        for task in self.getGarlandPart():
            report = task.getTask(report)
        return report
