from genslides.task.base import TaskDescription, BaseTask
from genslides.task.readfile import ReadFileTask
from genslides.utils.loader import Loader

import os, json
from os import listdir
from os.path import isfile, join

from genslides.utils.readfileman import ReadFileMan

class ReadFileParamTask(ReadFileTask):
    def __init__(self, task_info: TaskDescription, type="ReadFileParam") -> None:
        super().__init__(task_info, type)


    def readContentInternal(self):
        print(self.getName(), 'Read content from file by params')
        param_name = "read_folder"
        res, read_folder = self.getParam(param_name)
        
        if res and read_folder:
            res, pparam = self.getParamStruct(param_name)
            print("RF:", pparam)
            try:
                path = pparam["path_to_folder"]
                need_to_clean = pparam["clean_after"]
                onlyfiles = [f for f in listdir(path) if isfile(join(path, f))]
                text = ""
                for filename in onlyfiles:
                    filepath = path + filename

                    with open(filepath, 'r', encoding='utf-8') as f:
                        print("Read from file", filepath)
                        text += f.read() + "\n"
                    if need_to_clean:
                        os.remove(filepath)
                return True, text

            except Exception as e:
                print("Can\'t read params to read folder", e)
        param_name = "path_to_read"
        res, s_path = self.getParam(param_name)
        s_path = self.findKeyParam(s_path)
        # print('Target path:', s_path)
        if not os.path.exists(s_path):
            pres, paths = Loader.stringToPathList(s_path)
            # print('Paths:', paths)
            if pres and len(paths) > 0:
                text = ""
                rres, pparam = self.getParamStruct(param_name)
                if rres and 'header' in pparam:
                    text = self.findKeyParam( pparam['header'] )
                for t_path in paths:
                    print('Read file by path:', t_path)
                    header = 'Content of file by path ' + t_path +'\n'
                    text += ReadFileMan.readWithHeader(t_path, header)
                return True, text
            else:
                print("Can\'t read files using paths:" + s_path)
                if res:
                    rres, pparam = self.getParamStruct(param_name)
                    if rres and "read_dial" in pparam and pparam["read_dial"]:
                        self.msg_list = []
                return False, "Can\'t read files using paths:" + s_path
        elif res:
            # print('Get param')
            rres, pparam = self.getParamStruct(param_name)
            if rres:
                # print('Found param struct')
                if "role" in pparam:
                    self.prompt_tag = pparam["role"]
                else:
                    self.prompt_tag = "user"
                if "read_dial" in pparam and pparam["read_dial"] and os.path.isfile(s_path):
                    with open(s_path, 'r') as f:
                        try:
                            rq = json.load(f)
                            if "del_msgs" in pparam and isinstance(pparam["del_msgs"], int) :
                                if pparam['del_msgs'] < 0 and pparam["del_msgs"] > -len(rq):
                                    print('Remove from end=',pparam['del_msgs'])
                                    self.msg_list = rq[:(len(rq) + pparam["del_msgs"])]
                                elif pparam['del_msgs'] > 0 and pparam['del_msgs'] < len(rq):
                                    print('Remove from start=',pparam['del_msgs'])
                                    self.msg_list = rq[pparam['del_msgs'] :]
                                else:
                                    self.msg_list = rq
                                # print("Input msgs:", self.msg_list)
                            else:
                                self.msg_list = rq
                        except ValueError as e:
                            print("json error type=", type(e))
                            self.msg_list = []
                        # print(self.getName(),"read from[", s_path,"] dial with msg[",len(self.msg_list),'] out [',len(rq),']')
    
                    return False, ""
                elif "read_part" in pparam and pparam["read_part"] and "start_part" in pparam and "max_part" in pparam:
                    pres, text = ReadFileMan.readPartitial(s_path,int(pparam["max_part"]))
                    if pres:
                        return pres,text
                    # if os.path.isfile(s_path):
                    #     with open(s_path, 'r',encoding='utf-8') as f:
                    #         text = f.read()
                    #     start = int(pparam["max_part"])
                    #     stop = start + int(pparam["max_part"])
                    #     if len(text) > stop*8:
                    #         med = int((len(text) - stop)/2)
                    #         return True, "This is parts of file:\n\n" + text[start:stop] + "...\n\n..." + text[med:med + stop]  + "...\n\n..." + text[len(text) - stop :]
                    #     if len(text) > stop*4:
                    #         return True, "This is parts of file:\n\n" + text[start:stop] + "...\n\n..." + text[len(text) - stop :]
                    #     if len(text) > stop:
                    #         return True, "This is part of file:\n\n" + text[start:stop]
                    #     if 'delete' in pparam and pparam['delete']:
                    #         os.remove(s_path)
                    #         print('File bt path',s_path,'is removed')

                    #     return True, text
                        

        if res and os.path.isfile(s_path):
            with open(s_path, 'r', encoding='utf-8') as f:
                text = f.read()
                return True, text
        return False, "No file found"


    def loadContent(self, s_path, msg_trgs):
        res, text = self.readContentInternal()
        if res:
            msg_trgs[-1]["content"] = text
        return res, text



    def executeResponse(self):
        res, text = self.readContentInternal()
        if res:
            self.msg_list = self.parent.msg_list.copy()
            self.msg_list.append({
                "role": self.prompt_tag,
                "content": text
            })

    def getMsgInfo(self):
        param_name = "path_to_read"
        res, path = self.getParam(param_name)
        value = "None"
        if res:
            value = path
        if len(self.msg_list):
            out = self.msg_list[len(self.msg_list) - 1]
            return value, out["role"],out["content"]
        return value,"user",""
 
    def getLastMsgAndParent(self) -> (bool, list, BaseTask):
        val = []
        rres, pparam = self.getParamStruct("path_to_read")
        if rres and "read_dial" in pparam and pparam["read_dial"]:
            for msg in self.msg_list:
                val.append({"role":msg["role"],"content":self.findKeyParam(msg["content"])})
            return True, val, None
        else:
            val = [{"role":self.getLastMsgRole(), "content": self.findKeyParam(self.getLastMsgContent())}]
            return True, val, self.parent

    def updateIternal(self, input : TaskDescription = None):
        # TODO: Это просто переопределение функции обновления для Response, она была дополнена свойством, что при указании, что читается диалог, всегда происходило чтение вне зависимости от совпадают ли родительские сообщения с сохраненными
        res, stopped = self.getParam("stopped")
        if res and stopped:
            print("Stopped=", self.getName())
            return "",self.prompt_tag,""
        
        if self.is_freeze and self.parent:
            print("frozen=",self.getName())
            if not self.parent.is_freeze:
                self.is_freeze = False
                tmp_msg_list = self.getRawParentMsgs()
                # print(pprint.pformat(tmp_msg_list))
                msg_list_from_file = self.getResponseFromFile(tmp_msg_list)
                if len(msg_list_from_file):
                    print("I loaded")
                    self.msg_list = msg_list_from_file

            else:
                # super().update(input)
                return "","user",""

        if len(self.msg_list) == 0:
            print('Empty msg list')
            self.executeResponse()
            self.saveJsonToFile(self.msg_list)
        else:
            print('Not empty msg list')
            sres, sparam = self.getParamStruct(self.getType())
            exe_always = False
            if sres and 'do_always' in sparam and sparam['do_always']:
                exe_always = True

            rres, pparam = self.getParamStruct('path_to_read')
            if rres and "read_dial" in pparam and pparam["read_dial"]:
                self.executeResponse()
                self.saveJsonToFile(self.msg_list)
            elif not self.checkParentMsgList(update=True, save_curr=False) or exe_always:
                self.executeResponse()
                self.saveJsonToFile(self.msg_list)
            else:
                print("Messages are same")
                pass
 