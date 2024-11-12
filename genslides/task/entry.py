import genslides.task.savetext as SvT
import os, sys

class EntryTask(SvT.SaveTextTask):
    def __init__(self, task_info : SvT.TaskDescription, type='Entry'):
        super().__init__(task_info, type)

    def list_files_and_directories(self,path, filetag = "File", dirtag= "Directory"):
        """Lists files and directories within a given path and prints their names."""
        out = ""
        for item in os.listdir(path):
            if os.path.isfile(os.path.join(path, item)):
                out += f"{filetag}: {item}\n"
            elif os.path.isdir(os.path.join(path, item)):
                out += (f"{dirtag}: {item}\n")
        return out
    
    def listEntry(self, getdir = True, getfile = True):
        out = []
        eres, eparam = self.getParamStruct("entry", only_current=True)
        if eres:
            path = self.findKeyParam(eparam['path_to_read'])
            for item in os.listdir(path):
                if os.path.isfile(os.path.join(path, item)) and getfile:
                    out.append(item)
                elif os.path.isdir(os.path.join(path, item)) and getdir:
                    out.append(item)
        return out
    
    def getRichPrompt(self):
        eres, eparam = self.getParamStruct("entry", only_current=True)
        if eres:
            return self.list_files_and_directories(self.findKeyParam(eparam['path_to_read']), eparam['filetag'], eparam['dirtag'])
        return ""
    
    def updateIternal(self, input = None):
        self.appendMessage({"content":self.getRichPrompt(),"role":self.prompt_tag})
        return super().updateIternal(input)
    
    def getTaskParamChoices(self, param={}):
        if 'target' in param and param['target'] == 'entry':
            if 'value' in param:
                if param['value'] == 'dir':
                    return True, self.listEntry(getdir=True, getfile=False)
                elif param['value'] == 'file':
                    return True, self.listEntry(getdir=False, getfile=True)
            return True, self.listEntry()
        return super().getTaskParamChoices(param)
    
    def getPathToRead(self):
        return self.getChoicesByParentTask({
            'target': 'entry',
            'value':'dir'
        })
