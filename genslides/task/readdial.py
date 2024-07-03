from genslides.task.base import TaskDescription
from genslides.task.readfile import ReadFileTask
import os
import json
import genslides.task_tools.records as rd

class ReadBranchTask(ReadFileTask):
    def __init__(self, task_info: TaskDescription, type="ReadBranch") -> None:
        super().__init__(task_info, type)
        self.saveJsonToFile(self.msg_list)

    def copyParentMsg(self):
        self.msg_list = []

    def getRichPrompt(self) -> str:
        if self.parent:
            return self.parent.msg_list[-1]["content"]
        return self.prompt



    def executeResponse(self):
        # print("Exe response read dial=", self.getRichPrompt())
        if os.path.isfile(self.getRichPrompt()):
            param_name = "path_to_read"
            self.updateParam(param_name,self.getRichPrompt())


            self.msg_list = self.getJsonDial()

    def getJsonDial(self):
        eres, eparam = self.getParamStruct(self.getType(), only_current=True)
        try:
            s_path = eparam['path_to_read']
            with open(s_path, 'r') as f:
                print("path_to_read =", s_path)
                rq = json.load(f)
                if isinstance(rq, list):
                    return rq
                elif isinstance(rq, dict):
                    if 'type' in rq and rq['type'] == 'records':
                        if eparam['input'] == 'row':
                            return {"content" : rd.getRecordsRow(rq, eparam), "role" : self.prompt_tag}

        except ValueError as e:
            print("json error type=", type(e))
        return []


    def loadContent(self, s_path, msg_trgs) -> bool:
        if os.path.isfile(s_path):
            return True, self.getJsonDial(s_path)
        return False, msg_trgs



