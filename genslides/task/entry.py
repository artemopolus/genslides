import genslides.task.savetext as SvT
import os
import json
import genslides.utils.loader as Ld

class EntryTask(SvT.SaveTextTask):
    def __init__(self, task_info : SvT.Txt.TaskDescription, type='Entry'):
        super().__init__(task_info, type)
    
    def list_files_and_directories(self, path, filetag="File", dirtag="Directory", output="std", type_out="all", file_extensions=""):
        """Lists files and directories within a given path, with options for output format and item types and file extension filtering."""
        path = Ld.Loader.getUniPath(path)
        items = []

        if type_out == "all_files_re":
            for root, _, files in os.walk(path):
                for file in files:
                    items.append(os.path.join(root, file))
        elif type_out == "file":
            items = [os.path.join(path,item) for item in os.listdir(path) if os.path.isfile(os.path.join(path, item))]
        elif type_out == "dir":
            items = [os.path.join(path,item) for item in os.listdir(path) if os.path.isdir(os.path.join(path, item))]
        elif type_out == "all":
            items = [os.path.join(path,item) for item in os.listdir(path)]
        else:
            return "Invalid type_out specified."

        #Second stage filtering by file extensions
        if file_extensions and type_out in ["all", "file", "all_files_re"]:
            extensions = [ext.strip().lower() for ext in file_extensions.split(',')]  #Normalize extensions
            items = [item for item in items if os.path.splitext(item)[1].lower() in extensions]


        if output == "list":
            return ";".join(items)

        elif output == "json":
            json_items = []
            for idx, item in enumerate(items):
                json_items.append({"content":Ld.Loader.getUniPath(item), "idx": idx, "chck": False})
            return json.dumps(json_items, indent=2, ensure_ascii=False)

        elif output == "std":
            out = f"In {dirtag} {os.path.basename(path)}:\n"
            for item in items:
                if os.path.isfile(item):
                    out += f" - {filetag}: {item}\n"
                elif os.path.isdir(item):
                    out += f" - {dirtag}: {item}\n"
            return out

        else:
            return "Invalid output format specified."
   
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
            try:
                return self.list_files_and_directories(path, eparam['filetag'], eparam['dirtag'], eparam['output'], eparam['type_out'], eparam['ext'])
            except Exception as e:
                print('Lisiting error:',e)
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
