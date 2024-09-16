from genslides.task.base import TaskDescription
from genslides.task.writetofileparam import WriteToFileParamTask
import json
import genslides.task_tools.records as rd
import genslides.utils.writer as wr
import genslides.utils.loader as ld
import genslides.utils.filemanager as fm

class WriteBranchTask(WriteToFileParamTask):
    def __init__(self, task_info: TaskDescription, type="WriteBranch") -> None:
        super().__init__(task_info, type)

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

            elif t_input == 'records' and self.manager.allowUpdateInternalArrayParam():
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

    def checkAnotherOptions(self) -> bool:
        param_name = "write_branch"
        res, pparam = self.getParamStruct(param_name)
        if res:
            op = 'always_update'
            if op in pparam and pparam[op]:
                return True
        return False

