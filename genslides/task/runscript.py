from genslides.task.base import TaskDescription
from genslides.task.response import ResponseTask
from genslides.utils.readfileman import ReadFileMan
from genslides.utils.loader import Loader


import os
from os.path import isfile, join
from os import listdir
import subprocess

class RunScriptTask(ResponseTask):
    def __init__(self, task_info: TaskDescription, type="RunScript") -> None:
        super().__init__(task_info, type)
        self.execute_success = False

    def executeResponse(self):
        print('[EXE] run script task')
        res, pparam = self.getParamStruct("script")
        if res:
            try:
                path_tmp = self.findKeyParam(pparam["path_to_trgs"] )
                path_to_python = pparam["path_to_python"]
                need_to_remove = pparam["remove_script"]  
                phrase_script = self.findKeyParam( pparam["init_phrase"] )
                phrase_success = self.findKeyParam( pparam["on_success"] )
                phrase_error = self.findKeyParam( pparam["on_error"] )
                phrase_final = self.findKeyParam( pparam["on_final"] )

                str_path_to_output_files = self.findKeyParam(pparam["output_files"])

                targets_type = self.findKeyParam(pparam["targets_type"] )
                exe_type = self.findKeyParam(pparam["exe_type"] )

                if targets_type == 'args':
                    if isinstance(path_tmp, list):
                        onlyfiles = path_tmp
                    else:
                        print('No args')
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
        print("Trg files=", onlyfiles)
        data = ""
        done = True
        if len(onlyfiles) == 0:
            done = False
        for file in onlyfiles:
            data += phrase_script + str(file) + "\n"
            print("Run script", file)
            result = subprocess.run(file, capture_output=True, text=True)
            if result.returncode:
                done = False
                data += phrase_error + result.stderr + "\n"
            else:
                data += phrase_success + result.stdout + "\n"


            if str_path_to_output_files:
                tres, output_paths = Loader.stringToPathList(str_path_to_output_files)
                print('Path to output:', output_paths, tres)
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

        print('Execute result=', self.execute_success)

        if len(data) > 0:
            self.msg_list.append({"role": "user", "content": data})
        else:
            print("No data is getted from")
        
