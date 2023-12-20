import json
import os
from os import listdir
from os.path import isfile, join
import datetime
import time

def getTimeForSaving() -> str:
    return datetime.time.strftime("%Y-%m-%d %H:%M:%S")

def setTimeForSaving(time : str)->datetime:
    return datetime.datetime.strptime(time, "%Y-%m-%d %H:%M:%S")


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

    def save(self, data):
        filename = self.session_path + self.name
        self.saveInternal(filename, data)

    def saveInternal(self, filename, data):
        filename += ".json"
        print("Save",data["name"],"data in",filename,"at", data["time"])
        try:
            with open(filename,"r") as f:
                j = json.load(f)
            j.append(data)
        except:
            j = [data]
        with open(filename,"w") as f:
            json.dump(j, f, indent=1)

    def makePack(self, name, message,chat, chat_raw, targets, options = ""):
        pack = {"chat": chat}
        pack["name"] = name
        pack["message"] = message
        pack["msg_lst"] = chat_raw
        pack["targets"] = targets
        pack["options"] = options
        pack["time"] = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
        pack["estimation"] = False
        pack["evaluated"] = False
        return pack
    
    def updateEstimation(self, checked_message):
        filename = self.session_path + self.name +".json"
        out = []
        try:
            with open(filename,"r") as f:
                j = json.load(f)
                for pack in j:
                    if "evaluated" in pack and pack["message"] in checked_message:
                        pack["estimation"] = True
                    pack["evaluated"] = True
        except Exception as e:
            pass
 
        return out
                
            
    
    def getMessages(self):
        filename = self.session_path + self.name +".json"
        out = []
        try:
            with open(filename,"r") as f:
                j = json.load(f)
                for pack in j:
                    if "evaluated" in pack and not pack["evaluated"]:
                        out.append(pack["message"])
        except Exception as e:
            pass
 
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


