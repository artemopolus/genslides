from genslides.task.base import TaskDescription
from genslides.task.collect import CollectTask
from genslides.task.base import TaskManager

import json
from os import listdir
from os.path import isfile, join
import pprint


class GroupTask(CollectTask):
    def __init__(self, task_info: TaskDescription, type="Group") -> None:
        super().__init__(task_info, type)
        # print("group=",self.msg_list)

        self.saveJsonToFile(self.msg_list)

    def getResponseFromFile(self, msg_list, remove_last = True):
        print("Get response from file:")
        task_man = TaskManager()
        mypath = task_man.getPath()
        onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
        trg_file = self.filename + ".json"
        # for file in onlyfiles:
        if trg_file in onlyfiles:
            file = trg_file
            if file.startswith(self.getType()):
                path = mypath + file
                try:
                    print(path)
                    with open(path, 'r') as f:
                        rq = json.load(f)
                    if 'chat' in rq:
                        msg_trgs = rq['chat'].copy()
                        if remove_last:
                            msg_trgs.pop()
                        if True:
                            print(10*"====", "YEEEES")
                            self.path = path
                            self.setName(file.split('.')[0])
                            if 'params' in rq:
                                self.params = rq['params']
                            print("My new name is ", self.name)
                            return rq['chat']
                except json.JSONDecodeError:
                    pass
        return []
 


    def getRichPrompt(self) -> str:
        text = ""
        for task in self.by_ext_affected_list:
            text += task.prompt +"\n"
        return text

    def updateCollectedMsgList(self, trg_list : list):
        # print("update not frozen=", self.getName())
        # print(pprint.pformat(trg_list))
        if self.parent:
            trg_list = self.parent.msg_list.copy()
        for info in self.by_ext_affected_list:
            for msg in info.parent.msg_list:
                trg_list.append( msg )
        
        if self.msg_list != trg_list:
            self.msg_list = trg_list.copy()
            self.saveJsonToFile(self.msg_list)

    def checkParentsMsg(self):
        trg_list = self.parent.msg_list.copy()
        cur_list = self.msg_list.copy()
        # print(len(self.msg_list))
        # print("summ=",cur_list == trg_list, "[",len(cur_list),"==", len(trg_list),"]")
        # cut = cur_list.pop()
        for info in self.by_ext_affected_list:
            for msg in info.parent.msg_list:
                trg_list.append( msg )
        
        # print("Diff\n==================>>>>>>>>>>>\n", pprint.pformat( [i for i in cur_list if i not in trg_list]))
        # print(self.msg_list == trg_list)
        # for i in range(0,min([len(cur_list), len(trg_list)])):
        #     print(i,":",cur_list[i] == trg_list[i])
        # print("summ=",cur_list == trg_list, "[",len(cur_list),"==", len(trg_list),"]")

        # print("==================>>>>>>>>>>>", pprint.pformat( trg_list))
        # print("==================>>>>>>>>>>>", pprint.pformat( cur_list))

        if cur_list != trg_list:
            self.msg_list.clear()
            self.msg_list = trg_list.copy()
            print(len(self.msg_list))
            self.saveJsonToFile(self.msg_list)
            print("Freeeze from collect")
            self.freezeTask()
        return self.msg_list

