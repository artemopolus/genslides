from genslides.task.base import BaseTask, TaskDescription
from genslides.task.response import ResponseTask
from genslides.utils.readfileman import ReadFileMan
from genslides.utils.loader import Loader

import genslides.utils.writer as wr
import genslides.utils.filemanager as fm

import os
from os.path import isfile, join
from os import listdir
import subprocess

class RunScriptTask(ResponseTask):
    def __init__(self, task_info: TaskDescription, type="RunScript") -> None:
        super().__init__(task_info, type)
        self.execute_success = False

    def executeResponse(self):
        # print('[EXE] run script task')
        res, pparam = self.getParamStruct("script")
        if not res:
            return
        if 'parent_task_cmd' in pparam and pparam['parent_task_cmd'] != '':
            file = self.findKeyParam(pparam['parent_task_cmd'])
            workspace = self.findKeyParam(pparam["cwd"])
            workspace = Loader.getUniPath(workspace)
            fm.createFolder(workspace)
            # print("Run script", file,'in', workspace)
            self.updateUpdationInfo(f"Run script:\n{file}\n in \n{workspace}")

            result = subprocess.run(file, capture_output=True, text=True, cwd=workspace, shell=True)
            self.execute_success = True
            pparam['script_command'] = file
            pparam['script_cwd'] = workspace
            pparam['return'] = result.returncode
            pparam['error'] = result.stderr
            pparam['out'] = result.stdout
            self.updateParam2( pparam )
        res, pparam = self.getParamStruct("script")
        if res:
            data = self.findKeyParam(pparam['format'])
            self.appendMessage({"role": self.prompt_tag, "content": data})
            self.prompt = data
        else:
            print("No data is getted from")

        
    def updateIternal(self, input : TaskDescription = None):
        # Это просто переопределение функции обновления для Response, она была дополнена свойством, что при указании, что читается диалог, всегда происходило чтение вне зависимости от совпадают ли родительские сообщения с сохраненными
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

        res, pparam = self.getParamStruct("script")
        if res:
            if "onupdate" in pparam and pparam["onupdate"] == "check" \
                and self.checkParentMsgList(update=True, save_curr=False):
                    pass
            else:
                self.executeResponse()
        else:
            self.executeResponse()
        self.saveJsonToFile(self.msg_list)

    def forceCleanChat(self):
        res, pparam = self.getParamStruct("script")
        if res and "onupdate" in pparam and pparam["onupdate"] == "check":
            cres, cparam = self.getParamStruct("check")
            if cres:
                self.updateParamStruct("check","hash","")
        return super().forceCleanChat()
    
    def getLastMsgAndParentRaw(self, idx : int) -> list[bool, list, BaseTask]:
        ores,oval,opar = super().getLastMsgAndParentRaw(idx)
        pres, pparam = self.getParamStruct("script")
        script_text = ""
        if pres and 'parent_task_cmd' in pparam and pparam['parent_task_cmd'] != '':
            src_path_trgs_tmp = self.findKeyParam(pparam['parent_task_cmd'])
            # path_trgs_tmp = self.findKeyParam(src_path_trgs_tmp)
            path_trgs_tmp = src_path_trgs_tmp
            # print('init:', path_trgs_tmp)
            if path_trgs_tmp.rfind(';') == -1:
                path_tmp = path_trgs_tmp.split(';')
            else:
                path_tmp = [path_trgs_tmp]
            for proc in path_tmp:
                args = proc.split(' ')
                if len(args) > 1:
                    script_text += args[1] + '\n\n'
                    script_text += '```python\n' + ReadFileMan.readStandart(args[1]) + '```\n'
        if len(oval) > 0:
            oval[0]['content'] = script_text + oval[0]['content']
        return ores, oval, opar
 

class SaveScriptRunTask(RunScriptTask):
    def __init__(self, task_info: TaskDescription, type="SaveScriptRun") -> None:
        super().__init__(task_info, type)
        # sres, sparam = self.getParamStruct('savescriptrun_def', True)
        # if not sres:
        #     self.setParamStruct({
        #                      'type':'savescriptrun_def',
        #                      'script_type':'python',
        #                      'path_to_write': '[[manager:path:spc]]/script/test.py',
        #                      'script_content':'[[parent_3:code]]',
        #                      'args':'[[parent:msg_content]]'
        #                     })

    def executeResponse(self):
        sres, sparam = self.getParamStruct('savescriptrun')
        done = False
        data = ""
        if not sres:
            sres, sparam = self.getParamStruct('savescriptrun_def', True)
            if not sres:
                return
        try:
            scriptpath = Loader.getUniPath( self.findKeyParam( sparam['path_to_write'] ))
            script_text = self.findKeyParam( sparam['script_content'] )
            l = min(16, len(script_text))
            # print('Save script:\n', script_text[0:l])
            wr.writeToFile(scriptpath, script_text)
            if sparam['script_type'] == 'python':
                path_to_python = Loader.getUniPath( self.findKeyParam(sparam['python_path']) )
                if os.path.exists(scriptpath):
                    workspace = Loader.getUniPath( self.findKeyParam(sparam['cwd']))
                    args = self.findKeyParam(sparam['args'])
                    trg_proc = ' '.join([path_to_python, scriptpath, args])
                    self.updateUpdationInfo(f"Run script:\n{ trg_proc}\nin {workspace}")
                    result = subprocess.run(trg_proc, capture_output=True, text=True, cwd=workspace, shell=True)
                    if result.returncode:
                        data +=  result.stdout + "\n"
                        data += sparam['on_error'] + "\n```\n" + result.stderr + "\n```\n"
                    else:
                        done = True
                        data += sparam['on_success'] + result.stdout + "\n"


        except Exception as e:
            self.updateUpdationInfo(f"Run script with:\n {sparam}\n result with error:\n {e}")
        self.execute_success = done

        if len(data) > 0:
            pass
        else:
            self.updateUpdationInfo("No data to present")
        self.appendMessage({"role": self.prompt_tag, "content": data})
