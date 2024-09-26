from genslides.task.base import BaseTask, TaskDescription
from genslides.task.writetofileparam import WriteToFileParamTask
import json
import genslides.task_tools.records as rd
import genslides.utils.writer as wr
import genslides.utils.loader as ld
import genslides.utils.filemanager as fm

class WriteBranchTask(WriteToFileParamTask):
    def __init__(self, task_info: TaskDescription, type="WriteBranch") -> None:
        super().__init__(task_info, type)

    def getLastMsgContentForRawDial(self):
        content = ""
        res, param = self.getParamStruct(param_name='write_branch')
        if res:
            try:
                s_path = ld.Loader.getUniPath( self.findKeyParam( param['path_to_write'] ) )
                content += "Path to file: " + s_path + "\n"
                with open(s_path, 'r') as f:
                    rq = json.load(f)
                    if rq["type"] == "records":
                        content += "Records count: " + str(len(rq["data"])) + "\n"
                        min_chat_len = 100
                        max_chat_len = 0
                        for pack in rq["data"]:
                            min_chat_len = min(min_chat_len,len(pack["chat"]))
                            max_chat_len = max(max_chat_len, len(pack["chat"]))
                        if min_chat_len > max_chat_len:
                            min_chat_len = max_chat_len
                        content += "Min msgs in chat: " + str(min_chat_len) +"\n"
                        content += "Max msgs in chat: " + str(max_chat_len) +"\n"
            except Exception as e:
                content += "Error: "+ str(e)
        else:
            content += "Error: no parameters"

        return content
        

    def executeResponse(self):
        res, param = self.getParamStruct(param_name='write_branch')
        if not res:
            return
        try:
            path = ld.Loader.getUniPath( self.findKeyParam( param['path_to_write'] ) )
            t_input = param['input']
            content = None

            if t_input == 'msgs':
                content = self.getMsgs()
                wr.writeJsonToFile(path, content)

            elif self.checkRecordsOption(param):
                if fm.checkExistPath(path):
                    with open(path, 'r',encoding='utf8') as f:
                        content = json.load(f)
                    
                    if 'type' in content and content['type'] == 'records':
                        chat = self.getTasksContent()
                        # print(self.getName(),'append content',chat)
                        rres, naparam = rd.appendDataForRecord(content, chat)
                        # if not rres:          
                            # naparam = rd.createRecordParam(self.getTasksContent())
                    else:
                        naparam = rd.createRecordParam(self.getTasksContent())
                else:
                    naparam = rd.createRecordParam(self.getTasksContent())

                wr.writeJsonToFile(path, naparam)

        except Exception as e:
            print(self.getName(), 'got err:', e)

    def checkRecordsOption(self, param):
        if 'check_manager' in param:
            if param['check_manager']:
                pass
            else:
                return param['input'] == 'records'
        return param['input'] == 'records' and self.manager.allowUpdateInternalArrayParam()

    def checkAnotherOptions(self) -> bool:
        param_name = "write_branch"
        res, pparam = self.getParamStruct(param_name)
        if res:
            op = 'always_update'
            if op in pparam and pparam[op]:
                return True
        return False

    def clearRecordParam(self):
        try:
            res, param = self.getParamStruct(param_name='write_branch')
            s_path = ld.Loader.getUniPath( self.findKeyParam( param['path_to_write'] ) )
            with open(s_path, 'r') as f:
                rq = json.load(f)
                naparam = rd.clearRecordData(rq)
            wr.writeJsonToFile(s_path, naparam)
        except:
            print("Error for clean records")

        return super().clearRecordParam()
    