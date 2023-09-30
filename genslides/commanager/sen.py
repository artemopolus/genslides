from genslides.task.base import TaskManager
from genslides.utils.savedata import SaveData
from genslides.commanager.jun import Manager

from os import listdir
from os.path import isfile, join


import os
import json
import gradio as gr
import graphviz
import pprint
import py7zr
import datetime


class Projecter:
    def __init__(self, manager : Manager = None) -> None:
        mypath = "projects/"
        if not os.path.exists(mypath):
            os.makedirs(mypath)
        self.mypath = mypath
        task_man = TaskManager()
        self.savedpath = task_man.getPath()
        self.manager = manager
        # saver = SaveData()
        # saver.removeFiles()
        self.current_project_name = self.manager.getParam("current_project_name")
        self.updateSessionName()

    def updateSessionName(self):
        self.session_name = self.current_project_name + "_" + datetime.datetime.now().strftime("%y%m%d_%H%M%S")
        print("Name of session=",self.session_name)
        self.manager.setParam("session_name",self.session_name)


    def getTaskJsonStr(self, id : str):
        out = self.manager.getTaskJsonStr()
        out['id'] = id
        out['name'] = self.current_project_name
        return out

    def loadList(self):
        mypath = self.mypath
        onlyfiles = [f.split('.')[0] for f in listdir(mypath) if isfile(join(mypath, f))]
        return onlyfiles
    
    def clearFiles(self):
        mypath = self.savedpath
        for f in listdir(mypath):
            f_path = join(mypath, f)
            if isfile(f_path):
                os.remove(f_path)

    def clear(self):
        self.clearFiles()
        self.manager.onStart() 

    def getEvaluetionResults(self, input):
        print("In:", input)
        saver = SaveData()
        saver.updateEstimation(input)


    def extractFiles(self, filename, path_to_extract):
        onlyfiles = [f for f in listdir(self.mypath) if isfile(join(self.mypath, f))]
        if filename + ".7z" not in onlyfiles:
            return ""
        with py7zr.SevenZipFile(self.mypath + filename + ".7z", 'r') as archive:
            archive.extractall(path=path_to_extract)


    def load(self, filename):
        if filename == "":
            return ""
        self.clearFiles()
        self.extractFiles(filename, self.savedpath)
        self.manager.onStart() 
        self.current_project_name = filename
        self.manager.setParam("current_project_name",self.current_project_name)
        self.updateSessionName()
        return filename
    
    def append(self, filename):
        if filename + '.7z' in [f for f in listdir(self.mypath) if isfile(join(self.mypath, f))]:
            trg = os.path.join(self.savedpath, filename) +'/'
            self.extractFiles(filename, trg)
            print('Append project',filename,'task to', trg)
            proj_file = 'proj.json'
            proj_path = os.path.join(self.savedpath, proj_file)
            if os.path.exists(proj_path):
                pass
            else:
                proj_obj = {"appended": [filename]}
                with open(proj_path, 'w') as f:
                    json.dump(proj_obj,f,indent=1) 

            self.manager.appendExtendProjectTasks(trg)           

    
    def save(self, name):
        self.current_project_name = name
        self.manager.setParam("current_project_name",self.current_project_name)

        mypath = self.savedpath
        onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
        first = True
        for file in onlyfiles:
            if first:
                with py7zr.SevenZipFile( self.mypath + name + ".7z", 'w') as archive:
                    archive.write(self.savedpath + file, arcname = file)
                first = False
            else:
                with py7zr.SevenZipFile( self.mypath + name + ".7z", 'a') as archive:
                    archive.write(self.savedpath + file, arcname = file)

        return gr.Dropdown.update( choices= self.loadList(), interactive=True)

