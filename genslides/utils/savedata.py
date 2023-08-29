import json
import os
from os import listdir
from os.path import isfile, join


class SaveData:
    def __init__(self) -> None:
        path_to_config = "config\\base.json"
        self.loaded = False
        with open(path_to_config, 'r') as config:
            values = json.load(config)
            if "session_name" in values:
                self.name = values["session_name"]
                self.loaded = True

        self.session_path = "saved\\session\\"
        self.archive_path = "saved\\archive\\"

    def save(self, name, data):
        filename = self.session_path
        filename += self.name + "_" + name
        self.saveInternal(filename, data)

    def saveInternal(self, filename, data):
        print("Save tmp data in",filename)
        with open(filename,"w") as f:
            f.write(data)

    def makePack(self, message, chat, param):
        pack = {"msg_lst": chat}
        pack["message"] = message
        pack["options"] = param["options"]
        pack["estimation"] = False
        return pack
    
    def updateEstimation(self, checked_message):
        mypath = self.session_path
        onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
        for filename in onlyfiles:
            found = False
            full_filename = self.session_path + filename
            with open (full_filename, "r") as f:
                values = json.load(f)
                for msg in checked_message:
                    if "message" in values and values["message"] == msg:
                        values["estimation"] = True
                        found = True
            if found:
                 self.saveInternal(full_filename, json.dumps(values, indent=1))
                
            
    
    def getMessages(self):
        mypath = self.session_path
        onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
        out = []
        for file in onlyfiles:
            with open (self.session_path + file, "r") as f:
                values = json.load(f)
                if "message" in values:
                    out.append(values["message"])
        return out
 

    def moveFiles(self):
        mypath = self.session_path
        onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
        for file in onlyfiles:
            os.rename(self.session_path + file, self.archive_path + file)
            # os.remove(self.session_path + file)

    def removeFiles(self):
        mypath = self.session_path
        onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
        for file in onlyfiles:
            os.remove(self.session_path + file)


