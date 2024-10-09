import genslides.task.text as TextTask
import genslides.task_tools.records as rd

class LinkedTask(TextTask.TextTask):
    def __init__(self, task_info: TextTask.TaskDescription, type='Linked') -> None:
        super().__init__(task_info, type)

    def checkInput(self, input: TextTask.TaskDescription = None):
        super().checkInput(input)
        if input:
            if self.parent:
                trg_list = self.checkParentsMsg()
            else:
                trg_list = []
            self.updateCollectedMsgList(trg_list)

    def updateCollectedMsgList(self, trg_list : list):
        # print("update collected msg list")
        last = {"content" : self.getRichPrompt(), "role" : self.prompt_tag}
        trg_list.append(last)
        self.setMsgList( trg_list.copy())
        self.saveJsonToFile(self.msg_list)

    def getRichPrompt(self) -> str:
        # TODO: Перенести сюда заполнение шаблона
        res, param = self.getParamStruct('linkedfrom')
        text = ""
        if res:
            names = param['tasks']
            checkers = [t.getName() for t in self.getAffectingOnTask()]
            # print('=================>>>>>>>>>>>>Check', names, '==',checkers)
            # print(set(names) ==set(checkers))
            # for name in names:
                # print('Check',name,':',name in checkers)
            if set(names).difference(set(checkers)) == set():
                # print('Yes')
                for t in names:
                    for intask in self.by_ext_affected_list:
                        if intask.parent.getName() == t:
                            text += intask.prompt + '\n'
            else:
                print('No')
            return text
        eres, eparam = self.getParamStruct(self.getType(), only_current=True)
        for task in self.by_ext_affected_list:
            # print("Copy data from", task.parent.getName())
            try:
                if eres and eparam['input'] == 'records':
                    res, param = task.parent.getParamStruct(param_name='records', only_current=True)
                    if res:
                        text += rd.getRecordsRow(param, eparam)
                elif eres and eparam['input'] == 'request':
                    text += eparam['header'] + task.prompt + eparam['footer']    
                else:
                    text += task.prompt
            except Exception as e:
                text += task.prompt

        # print('Result:', text)
        return text

    def createLinkToTask(self, task) -> TextTask.TaskDescription:
        id = len(self.by_ext_affected_list)
        # print("Create link to ", task.getName(),"id=", id)
        out = TextTask.TaskDescription(method=self.affectedTaskCallback, id=id, parent=task , target=self)
        self.by_ext_affected_list.append(out)
        
        task.setLinkToTask(out)
        return super().createLinkToTask(task) 

    def updateLinkedPrompts(self, input : TextTask.TaskDescription):
        for tsk_info in self.by_ext_affected_list:
            if input.id == tsk_info.id:
                
                tsk_info.prompt = input.prompt
                tsk_info.enabled = input.enabled
                # print("Task[", tsk_info.id,"].enabled=",tsk_info.enabled)
                # print('New prompt:', tsk_info.prompt)

    def affectedTaskCallback(self, input : TextTask.TaskDescription):
        # print("From ", input.parent.getName(), " to ", self.getName())
        if input and input.stepped:
            found = False
            for cl in self.callback_link:
                if cl["pt"] == input.parent:
                    cl["used"] = False
                    found = True
                    break
            if not found:
                self.callback_link.append({"pt":input.parent,"used": False})
                found = True
            if found:
                self.resetTreeQueue()

        self.updateLinkedPrompts(input=input)

        out = super().affectedTaskCallback(input)
        self.stdProcessUnFreeze()
        # if input and input.stepped:
        #     pass
        #     # info = TaskDescription(prompt=self.getLastMsgContent(), prompt_tag=self.getLastMsgRole(),stepped=input.stepped)
        #     # self.update(info)
        # else:
        #     self.update()
 
    def removeLinkToTask(self):
        self.prompt = ""
        # self.update()
        self.freezeTask()
        super().removeLinkToTask()
        self.saveJsonToFile(self.msg_list)

    def whenParentRemoved(self):
        super().whenParentRemoved()
        self.removeLinkToTask()

    
 