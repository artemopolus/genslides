from genslides.task.text import TextTask
from genslides.task.base import TaskDescription
from genslides.task.collect import CollectTask

import json

class GroupCollectTask(CollectTask):
    def __init__(self, task_info: TaskDescription, type="GroupCollect") -> None:
        super().__init__(task_info, type)
        gres, gparam = self.getParamStruct('collecting', True)
        if not gres:
            self.setParamStruct({
                             'type':'collecting',
                             'revert' : False,
                             'tojson': False,
                             'base_json_tag': 'answer',
                             'list_tag':['point']
            })
 
    def update(self, input: TaskDescription = None):
        # print('Task',self.getName(),'is updated')
        return super().update(input)

    def updateLinkedPrompts(self, input : TaskDescription):
        # print("========================================================================update linked prompts")
        gres, gparam = self.getParamStruct('collecting', True)
        for tsk_info in self.by_ext_affected_list:
            if input.id == tsk_info.id:
                msgs = input.parent.getMsgs()
                text = ""
                if gres and 'tojson' in gparam and gparam['tojson']:
                    points = []
                    if gres and 'revert' in gparam and gparam['revert']:
                        for msg in reversed(msgs):
                            points.append({gparam['list_tag'][0]: msg['content']})
                    else:
                        for msg in msgs:
                            points.append({gparam['list_tag'][0]: msg['content']})

                    text = json.dumps({gparam['base_json_tag']: points}, indent=1)

                elif gres and 'revert' in gparam and gparam['revert']:
                    for msg in reversed(msgs):
                        text += msg['content']
                else:
                    for msg in msgs:
                        text += msg['content']
                    # print(msg)
                tsk_info.prompt = text
                tsk_info.enabled = input.enabled
                # if tsk_info.enabled:
                    # print('Input group msgs:',tsk_info.prompt)
                # print("\t\tEnabling",input.parent.getName(),"[", tsk_info.id,"]=",tsk_info.enabled)

        self.printLinkState()

