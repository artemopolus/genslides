import genslides.task.savetext as SvT
import os
import genslides.utils.loader as Ld

class EntryTask(SvT.SaveTextTask):
    def __init__(self, task_info : SvT.Txt.TaskDescription, type='Entry'):
        super().__init__(task_info, type)

    def list_files_and_directories(self,path, filetag = "File", dirtag= "Directory"):
        """Lists files and directories within a given path and prints their names."""
        out = f"In {dirtag} {os.path.basename(path)}:\n"
        for item in os.listdir(path):
            if os.path.isfile(os.path.join(path, item)):
                out += f" - {filetag}: {item}\n"
            elif os.path.isdir(os.path.join(path, item)):
                out += f" - {dirtag}: {item}\n"
        return out
    
    def listEntry(self, target_name: str, getdir = True, getfile = True):
        out = []
        eres, eparam = self.getParamStruct("entry", only_current=True)
        if eres:
            path = self.findKeyParam(eparam['path_to_read'])
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                item_pathcode = Ld.Loader.getManRePath(item_path, path, prefix=f"[[{target_name}:param:entry:path_to_read]]/")
                if os.path.isfile(item_path) and getfile:
                    out.append(item_pathcode)
                elif os.path.isdir(item_path) and getdir:
                    out.append(item_pathcode)
        return out
    
    def getRichPrompt(self):
        eres, eparam = self.getParamStruct("entry", only_current=True)
        if eres:
            path = self.findKeyParam(eparam['path_to_read'])
            # print(f"Target path: {path}")
            return self.list_files_and_directories(path, eparam['filetag'], eparam['dirtag'])
        return ""
    
    def updateIternal(self, input = None):
        self.appendMessage({"content":self.getRichPrompt(),"role":self.prompt_tag})
        self.saveAllParams()
        return super().updateIternal(input)
    
    def getTaskParamChoices(self, param={}):
        if 'target' in param and param['target'] == 'entry':
            if 'value' in param:
                if 'name_type' in param and param['name_type'] == 'parent':
                    target_name = 'parent_' + str(param['index']+1)
                else:
                    target_name = self.getName()
                if param['value'] == 'dir':
                    return True, self.listEntry(target_name, getdir=True, getfile=False)
                elif param['value'] == 'file':
                    return True, self.listEntry(target_name, getdir=False, getfile=True)
            return True, self.listEntry()
        return super().getTaskParamChoices(param)
    
    def getPathToRead(self):
        return self.getChoicesByParentTask({
            'target': 'entry',
            'value':'dir',
            'name_type':'parent'
        })
