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
        if res:
            try:
                if 'parent_task_cmd' in pparam and pparam['parent_task_cmd'] != '':
                    src_path_trgs_tmp = self.findKeyParam(pparam['parent_task_cmd'])
                    # path_trgs_tmp = self.findKeyParam(src_path_trgs_tmp)
                    path_trgs_tmp = src_path_trgs_tmp
                    print('init:', path_trgs_tmp)
                    if path_trgs_tmp.rfind(';') == -1:
                        path_tmp = path_trgs_tmp.split(';')
                    else:
                        path_tmp = [path_trgs_tmp]
                    print('partask:',path_tmp)
                else:
                    path_trgs_tmp = pparam["path_to_trgs"]
                    if isinstance(path_trgs_tmp, str):
                        path_tmp = self.findKeyParam(pparam["path_to_trgs"] )
                    else:
                        path_tmp = path_trgs_tmp
                path_to_python = pparam["path_to_python"]
                need_to_remove = pparam["remove_script"]  
                phrase_script = self.findKeyParam( pparam["init_phrase"] )
                phrase_success = self.findKeyParam( pparam["on_success"] )
                if phrase_success == 'None':
                    phrase_success = ''
                phrase_error = self.findKeyParam( pparam["on_error"] )
                phrase_final = self.findKeyParam( pparam["on_final"] )
                workspace = self.findKeyParam(pparam["cwd"])
                workspace = Loader.getUniPath(workspace)
                fm.createFolder(workspace)


                str_path_to_output_files = self.findKeyParam(pparam["output_files"])

                targets_type = self.findKeyParam(pparam["targets_type"] )
                exe_type = self.findKeyParam(pparam["exe_type"] )

                if targets_type == 'args':
                    # print('Get args:', path_tmp)
                    if isinstance(path_tmp, list):
                        onlyfiles = path_tmp
                    else:
                        print('No args')
                        return
                elif targets_type == 'single':
                    if 'script_param' in pparam:
                        if exe_type == 'py' and 'path_to_python' in pparam:
                            target_script = ' '.join([pparam['path_to_python'],pparam['script_param']])
                            onlyfiles = [target_script]
                        else:
                            return
                    else:
                        print('No script param')
                        return
                else:
                    if exe_type == 'py':
                        if targets_type == 'folder':
                            onlyfiles1 = [f for f in listdir(path_tmp) if isfile(join(path_tmp, f))]
                        elif targets_type == 'files':
                            if isinstance(path_tmp, list):
                                onlyfiles1 = path_tmp
                            elif isinstance(path_tmp, str):
                                onlyfiles1 = path_tmp.split(',')
                            else:
                                print('Unknown files')
                                return
                        else:
                            print('Unknown target types')
                            return
                        onlyfiles = []
                        if os.path.exists(path_to_python):
                            for file in onlyfiles1:
                                if file.endswith(".py"):
                                    # script_path = os.path.join(path_tmp, file)
                                    script_path = file
                                    onlyfiles.append([path_to_python, script_path])


            except Exception as e:
                print("Error on script struct param=",e)
        else:
            print('No params')
            return    
        print("Trg proc=", onlyfiles)
        data = ""
        done = True
        if len(onlyfiles) == 0:
            done = False
        for file in onlyfiles:
            if phrase_script != 'None':
                data += phrase_script + str(file) + "\n"
            if isinstance(file, str):
                pfile = self.findKeyParam(file)
                if pfile[0] == "\"" and pfile[-1] == "\"":
                    pfile = pfile[1:-1]
                # print('path',pfile)
                options = pfile.split(" ")
                n_options = []
                for option in options:
                    apath = Loader.getUniPath(option)
                    if os.path.exists(apath):
                        n_options.append(apath)
                    else:
                        n_options.append(option)
                file = ' '.join(n_options)
            elif isinstance(file, list):
                n_file = []
                for opt in file:
                    n_file.append(self.findKeyParam(opt))
                file = n_file
            print("Run script", file,'in', workspace)
            result = subprocess.run(file, capture_output=True, text=True, cwd=workspace, shell=True)
            if result.returncode:
                done = False
                if phrase_error == "None":
                    data += result.stdout + "\n"
                else:
                    data += result.stdout + phrase_error + result.stderr + "\n"
            else:
                data += phrase_success + result.stdout + "\n"


            if str_path_to_output_files:
                tres, output_paths = Loader.stringToPathList(str_path_to_output_files)
                # print('Path to output:', output_paths, tres)
                if tres:
                    data += "\n\n\nHere below outputs of script:\n\n\n"
                    for p in output_paths:
                        # ppath=p.strip("\'")
                        tres, text = ReadFileMan.readPartitial(p,400)
                        data += text + "\n"
                else:
                    pass
                    # data += "No files on path" + str_path_to_output_files



            if need_to_remove:
                try:
                    os.remove(script_path)
                    print("Remove ", script_path)
                except:
                    print("Can't remove ", script_path)
                    pass
        self.execute_success = done

        if not done:
            data += phrase_final

        # print('Execute result=', self.execute_success)

        if len(data) > 0:
            # print('Script output len=', len(data))
            self.msg_list.append({"role": "user", "content": data})
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

        self.executeResponse()
        self.saveJsonToFile(self.msg_list)
    
    def getLastMsgAndParentRaw(self, idx : int) -> list[bool, list, BaseTask]:
        ores,oval,opar = super().getLastMsgAndParentRaw(idx)
        pres, pparam = self.getParamStruct("script")
        script_text = ""
        if pres and 'parent_task_cmd' in pparam and pparam['parent_task_cmd'] != '':
            src_path_trgs_tmp = self.findKeyParam(pparam['parent_task_cmd'])
            # path_trgs_tmp = self.findKeyParam(src_path_trgs_tmp)
            path_trgs_tmp = src_path_trgs_tmp
            print('init:', path_trgs_tmp)
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
            print('Save script:\n', script_text[0:l])
            wr.writeToFile(scriptpath, script_text)
            if sparam['script_type'] == 'python':
                path_to_python = Loader.getUniPath( self.findKeyParam(sparam['python_path']) )
                if os.path.exists(scriptpath):
                    workspace = Loader.getUniPath( self.findKeyParam(sparam['cwd']))
                    args = self.findKeyParam(sparam['args'])
                    trg_proc = ' '.join([path_to_python, scriptpath, args])
                    print("Run script:\n", trg_proc,'\nin', workspace)
                    result = subprocess.run(trg_proc, capture_output=True, text=True, cwd=workspace, shell=True)
                    if result.returncode:
                        data += sparam['on_error'] + result.stderr + "\n"
                    else:
                        done = True
                        data += sparam['on_success'] + result.stdout + "\n"


        except Exception as e:
            print('Task', self.getName(),'with param:\n', sparam,'\nerror:', e)
        self.execute_success = done

        if len(data) > 0:
            self.msg_list.append({"role": "user", "content": data})
        else:
            print(self.getName(), "no data to present")
