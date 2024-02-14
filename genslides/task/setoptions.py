from genslides.task.base import TaskDescription, BaseTask
from genslides.task.writetofile import WriteToFileTask

import json, regex
import genslides.utils.finder as finder


class SetOptionsTask(WriteToFileTask):
    def __init__(self, task_info: TaskDescription, type="SetOptions") -> None:
        super().__init__(task_info, type)
    
    def checkLoadCondition(self, msg_trgs, msg_list) -> bool:
        return True

    def isInputTask(self):
        return False
    
    def getLastMsgAndParent(self):
        return False, [], self.parent

    def getLastMsgContentRaw(self):
        return json.dumps(self.params, indent=1)

    def getLastMsgContent(self):
        return json.dumps(self.params, indent=1)
    
    def executeResponse(self):
        try:
            self.params = json.loads(self.prompt)
        except Exception as e:
            print("Can\'t load parameters for",self.getName(),':',e)

    def updateAncestorParamStructValue(self):
        for param in self.params:
            if "type" in param and "updateable" in param:
                try:
                    src_value = None
                    print("Get updateable",param)
                    if param['updateable'] == 'const':
                        src_value = param['src']
                    elif param['updateable'] == 'get':
                        src = param["src"].split(":")
                        src_task = self.getAncestorByName(src[0])
                        if src[1] == finder.getMsgTag():
                            if len(src) > 3:
                                if src[2] == "json":
                                    pattern = regex.compile(r'\{(?:[^{}]|(?R))*\}')
                                    text = src_task.findKeyParam( src_task.getLastMsgContent())
                                    json_list = pattern.findall(text)
                                    # print("Found pattern:", json_list)
                                    for json_val in json_list:
                                        try:
                                            jparam = json.loads(json_val)
                                            # print("Found json:",jparam)
                                            if src[3] in jparam:
                                                src_value = jparam[src[3]]
                                                break
                                        except:
                                            pass
                            else:
                                src_value = src_task.findKeyParam( src_task.getLastMsgContent())

                        elif len(src) > 2:
                            for sparam in src_task.params:
                                if "type" in sparam and sparam["type"] == src[1] and src[2] in sparam:
                                    src_value = sparam[src[2]]
                                    break
                        else:
                            pass
                    trg = param['trg'].split(':')
                    trg_task = self.getAncestorByName(trg[0])
                    print("Insert in[",trg_task.getName(),'] using', trg)
                    if len(trg) > 5:
                        for tparam in trg_task.params:
                            if trg[3] in tparam and tparam[trg[3]] == trg[4] and trg[-1] in tparam:
                                print('update param [',trg[2],'] struct with [', src_value,']')
                                trg_task.updateParamStruct(trg[2],trg[-1], src_value)
                                break
                    elif len(trg) > 2:
                        for tparam in trg_task.params:
                            print("p=",tparam)
                            if 'type' in tparam and tparam['type'] == trg[1] and trg[2] in tparam and src_value:
                                print('update param struct with', src_value)
                                trg_task.updateParamStruct(trg[1],trg[2], src_value)
                                break
                except:
                    print("Error on updateable")

    def updateIternal(self, input: TaskDescription = None):
        if not self.checkParentMsgList(update=True,remove=False):
            self.saveJsonToFile(self.msg_list)
        self.updateAncestorParamStructValue()


    def checkInput(self, input: TaskDescription = None):
        if input:
            self.prompt = input.prompt
            try:
                in_params = json.loads(self.prompt)
                if in_params != self.params:
                    # TODO: переписать замену параметров на обновление текущих параметров
                    self.params = in_params
                    print("Params changed update all")
                    self.forceCleanChildsChat()
            except Exception as e:
                print("Can't load parameters from",self.prompt,"due",e)

            for param in input.params:
                if 'name' in param and 'value' in param and 'prompt' in param:
                    self.updateParam(param["name"], param["value"],param["prompt"])

            if input.parent:
                # self.parent = input.parent
                # self.parent.addChild(self)
                self.setParent(input.parent)
                print("New parent=", self.parent)

 
            self.saveJsonToFile(self.msg_list)

    def update(self, input : TaskDescription = None):
        super().update(input)
        return self.getLastMsgContent(), self.getLastMsgRole(), ""
    
    def getMsgInfo(self):
        return json.dumps(self.params, indent=1),"user",""
 
    def getParamFromExtTask(self, param_name):
        # print('Try to get param from',self.getName())
        for param in self.params:
            for k,p in param.items():
                # print("k=",k,"p=",p)
                if param_name == k:
                    return True,self.parent, p

        return False, self.parent, None
 
    def getParamStructFromExtTask(self, param_name):
        # print("Search for", param_name,"in", self.getName())
        # res, val = self.getParamStruct(param_name)
        # return res, self.parent, val 
        # print('Params=', self.params)
        for param in self.params:
            if "type" in param and param["type"] == param_name:
                return True, self.parent, param
        return False, self.parent, None
      

    def getInfo(self, short = True) -> str:
        return self.getName()
 

class GeneratorTask(SetOptionsTask):
    def __init__(self, task_info: TaskDescription, type="Generator") -> None:
        super().__init__(task_info, type)
        self.setParamStruct({'type':'generator','target':'[[parent:msg_content]]','struct':'json','tag':'array','cmd_id':0,'cmd_type':'prompt'})
    
    def getExeCommands(self):
        res, pparam = self.getParamStruct('manager', True)
        if res:
            gres, gparam = self.getParamStruct('generator', True)
            if gres:
                res_acts = []
                if gparam['struct'] == 'json':
                    text = self.findKeyParam(gparam['target'])
                    iter_list = json.loads(text)
                    if gparam['tag'] in iter_list and isinstance(iter_list[gparam['tag']],list):
                        iterators = iter_list[gparam['tag']]
                        for i in iterators:
                            acts = pparam['actions'].copy()
                            for act in acts:
                                if act['id'] == gparam['cmd_id']:
                                    act[gparam['cmd_type']] = i
                            res_acts.append(act)
                        return True, pparam, res_acts
        return super().getExeCommands()
