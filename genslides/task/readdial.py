from genslides.task.base import TaskDescription, BaseTask
from genslides.task.text import TextTask
from genslides.task.readfile import ReadFileTask
import os
import json
import genslides.task_tools.records as rd
import genslides.utils.loader as ld
from os import listdir
from os.path import isfile, join

class ReadBranchTask(TextTask):
    def __init__(self, task_info: TaskDescription, type="ReadBranch") -> None:
        self.update_read_branch = False
        super().__init__(task_info, type)
        self.msg_list = []
        msg_list_from_file = self.getResponseFromFile([])
        self.setMsgList(msg_list_from_file)
        self.readBranch()
        self.saveJsonToFile(self.msg_list)
        self.readbranchmsg_idx = 0

    def copyParentMsg(self):
        self.msg_list = []

    def getRichPrompt(self) -> str:
        if self.parent:
            return self.parent.msg_list[-1]["content"]
        return self.prompt
    
    def updateIternal(self, input: TaskDescription = None):
        self.readBranch()
        return super().updateIternal(input)
    
    def readBranch(self):
        print(self.getName(), 'Get read branch chat')
        eres, eparam = self.getParamStruct("ReadBranch")
        if not eres:
            return []
        if 'update' in eparam and eparam['update'] == 'auto':
            self.setMsgList(self.getJsonDial(eparam))
        elif 'update' in eparam and eparam['update'] == 'manual' and self.update_read_branch:
            self.setMsgList(self.getJsonDial(eparam))
            self.update_read_branch = False
        elif 'update' not in eparam:
            self.setMsgList(self.getJsonDial(eparam))


    def executeResponse(self):
        # print("Exe response read dial=", self.getRichPrompt())
        self.readBranch()

    def getJsonDial(self, eparam):
        try:
            s_path = ld.Loader.getUniPath( self.findKeyParam( eparam['path_to_read'] ) )
            print("path_to_read =", s_path)
            with open(s_path, 'r') as f:
                rq = json.load(f)
                if isinstance(rq, list):
                    return rq
                elif isinstance(rq, dict):
                    if 'type' in rq and rq['type'] == 'records':
                        if eparam['input'] == 'row':
                            content = rd.getRecordsRow(rq, eparam)
                            self.setParamStruct(eparam)
                            return [{"content" : content, "role" : self.prompt_tag}]
                        elif eparam['input'] == 'chat':
                            msgs = rd.getRecordsChat(rq, eparam)
                            self.setParamStruct(eparam)
                            return msgs

        except Exception as e:
            print("json error type=", e)
        return []


    def loadContent(self, s_path, msg_trgs) -> bool:
        return True, self.getJsonDial()

   
    def getParentForFinder(self):
        self.readbranchmsg_idx += 1
        return self

    def freeTaskByParentCode(self):
        self.readbranchmsg_idx = 0
        return super().freeTaskByParentCode()
    
    # def getMsgs(self, except_task=..., hide_task=True):
    #     return self.msg_list
    

    def getLastMsgContent(self):
        length = len(self.msg_list)
        if length > 0 and self.readbranchmsg_idx < length:
            return self.msg_list[length - 1 - self.readbranchmsg_idx]["content"]
        return ""

    def getResponseFromFile(self, msg_list, remove_last = True):
        mypath = self.manager.getPath()
        onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
        trg_file = self.filename + self.manager.getTaskExtention()
        if trg_file in onlyfiles:
            file = trg_file
            if file.startswith(self.getType()):
                path = os.path.join( mypath, file) 
                try:
                    with open(path, 'r') as f:
                        rq = json.load(f)
                    if 'chat' in rq:
                        msg_trgs = rq['chat'].copy()
                        self.path = path
                        self.setName( file.split('.')[0])
                        if 'params' in rq:
                            self.params = rq['params']
                        return msg_trgs
                except json.JSONDecodeError:
                    pass
        return []

    def getLastMsgAndParent(self, hide_task = True) -> list[bool, list, BaseTask]:
        if hide_task:
            res, pparam = self.getParamStruct('hidden', only_current=True)
            if res and pparam['hidden']:
                return False, [], self.parent
        # можно получать не только последнее сообщение, но и группировать несколько сообщений по ролям
        val = self.msg_list.copy()
        return True, val, None 


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
        val = self.msg_list.copy()
        if self.parent != None:
            self.parent.setActiveBranch(self)
        return True, val, None

    def forceCleanChat(self):
        self.update_read_branch = True
        self.freezeTask()

    def internalUpdateParams(self):
        return super().internalUpdateParams()
