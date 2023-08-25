from genslides.task.base import TaskDescription
from genslides.task.writetofile import WriteToFileTask

import json
import os

class WriteJsonToFileTask(WriteToFileTask):
    def __init__(self, task_info: TaskDescription, type="WriteJsonToFile") -> None:
        super().__init__(task_info, type)


    def executeResponse(self):
        if self.parent == None or self.is_freeze:
            return
        prop = self.msg_list[-1]["content"]
        arr = prop.split("{",1)
        if len(arr) > 0:
            prop = "{" + arr[1]
            for i in range(len(prop)):
                val = len(prop) - 1 - i
                if prop[val] == "}":
                    prop = prop[:val] + "}"
                    break

        # print("Input str=", prop)
        try:
            prop_json = json.loads(prop,strict=False)
            print("json=",prop_json)
        except Exception as e:
            print("Json load error=",e)
            return
        # print("exe resp write json to file=", prop_json)
        try:
            if "filepath" in prop_json and "text" in prop_json:
                with open(prop_json["filepath"], 'w',encoding='utf8') as f:
                    f.write(prop_json["text"])
                param_name = "path_to_write"
                self.updateParam(param_name,prop_json["filepath"])
            elif "type" in prop_json:
                if prop_json['type'] == 'code' and 'code' in prop_json and 'name' in prop_json:
                    # path = "output\\scripts\\"
                    res, path = self.getParam("folder_to_write")
                    if res and os.path.exists(path):
                        path += "\\" + prop_json['name'].replace(" ", "")
                        print("Write by json in", path)
                        with open(path, 'w',encoding='utf8') as f:
                            f.write(prop_json["code"])
                    else:
                        print("Problem with path=",path)
                else:
                    print("Unknown struct")
            else:
                print("Unknown type")
        except Exception as e:
            print('Error=',e)
        self.saveJsonToFile(self.msg_list)


 
