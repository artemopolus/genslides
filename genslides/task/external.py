import genslides.task.request as RqTask
import genslides.utils.loader as Ld

class ExternalInput(RqTask.RequestTask):
    def __init__(self, task_info: RqTask.TaskDescription, type="ExternalInput") -> None:
        super().__init__(task_info, type)

    def setParent(self, parent):
        self.parent = parent

    def getParentPath(self):
        return ""

    def isRootParent(self):
        return True
    
    def isExternalInput( self ):
        return True
    
    def getJsonCmdGroup(self, group_name):
        eres, eparam = self.getParamStruct("externalinput")
        if eres:
            groups = eparam.get("command_dict","")
            jres, jobj, jreport = Ld.Loader.loadJsonFromTextStr( groups )
            if jres and isinstance( jobj, dict ):
                if group_name in jobj:
                    return jobj[group_name]
        return super().getJsonCmdGroup(group_name)
    
    def stdProcessUnFreeze(self, input=None):
        eres, eparam = self.getParamStruct("externalinput")
        if eres and "unfreeze" in eparam and eparam["unfreeze"] == "non_freezing":
            self.unfreezeTask()
            return
        if self.parent == None:
            self.freezeTask()
        else:
            super().stdProcessUnFreeze(input)

    def getLastMsgAndParent(self, hide_task = True, max_symbols = -1, param = {}, add_task_name = False):
        return False, [], self.parent
    
    def isUnconnectedExternalRoot(self):
        if self.getParent() != None:
            return False
        else:
            return True
        return super().isUnconnectedExternalRoot()
 