from genslides.task.base import TaskManager
from genslides.utils.savedata import SaveData
from genslides.utils.archivator import Archivator
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
import shutil


class Projecter:
    def __init__(self, manager : Manager = None) -> None:
        mypath = os.path.join("projects")
        self.ext_proj_names = []
        ex_path = os.path.join('saved','ext')
        if os.path.exists(ex_path):
            fldrs = [f for f in listdir(ex_path) if os.path.isdir(os.path.join(ex_path, f))]
            self.ext_proj_names = fldrs
        if not os.path.exists(mypath):
            os.makedirs(mypath)
        self.mypath = mypath
        task_man = TaskManager()
        self.savedpath = task_man.getPath()
        self.manager = manager
        self.manager.loadTasksList()
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
            else:
                shutil.rmtree(f_path)

    def clear(self):
        self.clearFiles()
        self.manager.onStart() 

    def getEvaluetionResults(self, input):
        print("In:", input)
        saver = SaveData()
        saver.updateEstimation(input)




    def load(self, filename):
        if filename == "":
            return ""
        self.clearFiles()
        print(self.savedpath)
        Archivator.extractFiles(self.mypath, filename, self.savedpath)
        self.manager.onStart() 
        self.manager.loadTasksList()
        self.current_project_name = filename
        self.manager.setParam("current_project_name",self.current_project_name)
        self.updateSessionName()
        return filename
    
    def newExtProject(self, filename, prompt):
        self.createExtProject(filename, prompt, None)
        return self.manager.getCurrTaskPrompts()
    
    def appendExtProject(self, filename, prompt):
        self.createExtProject(filename, prompt, self.manager.curr_task)
        return self.manager.getCurrTaskPrompts()
    
    def createExtProject(self, filename, prompt, parent) -> bool:
        # mypath = self.mypath
        mypath = os.path.join('tools')
        if filename + '.7z' in [f for f in listdir(mypath) if isfile(join(mypath, f))]:
            ext_pr_name = 'pr' + str(len(self.ext_proj_names))
            trg = os.path.join(self.savedpath,'ext', ext_pr_name) +'/'
            if Archivator.extractFiles(mypath, filename, trg):
                self.ext_proj_names.append(ext_pr_name)
            print('Append project',filename,'task to', trg)
            # self.manager.appendExtendProjectTasks(trg, ext_pr_name)
            cur = self.manager.curr_task
            # self.manager.makeTaskAction(ext_pr_name,"ExtProject","New","user")
            self.manager.createOrAddTask(prompt, 'ExtProject','user',parent,[{'type':'external','project':ext_pr_name,'filename':filename}])
            if cur != self.manager.curr_task and cur is not None:
                print('Successfully add external task')
                print('List of tasks:',[n.getName() for n in self.manager.task_list])
                return True
        return False

    
    def save(self, name):
        print('save project', name)
        self.current_project_name = name
        self.manager.setParam("current_project_name",self.current_project_name)

        # Archivator.saveOnlyFiles(self.savedpath, self.mypath, name)
        Archivator.saveAll(self.savedpath, self.mypath, name)

        return gr.Dropdown.update( choices= self.loadList(), interactive=True)

    def copyChildChains(self):
        tasks_chains = self.manager.curr_task.getChildChainList()
        print('Task chains:')
        i = 0
        for branch in tasks_chains:
            print(i,[task.getName() for task in branch['branch']], branch['done'], branch['idx'],  branch['parent'].getName() if branch['parent'] else "None", branch['i_par'])
            i+= 1
        parent = None
        for i in range(len(tasks_chains)):
            branch = tasks_chains[i]
            for j in range(len(branch['branch'])):
                if j == 0:
                    if i != 0:
                        parent = tasks_chains[branch['i_par']]['created'][-1]
                    branch['created'] = []
                else:
                    parent = self.manager.curr_task
                task = branch['branch'][j]
                prompt=task.getLastMsgContent() 
                prompt_tag=task.getLastMsgRole()
                print('branch',i,'task',j,'par',parent.getName() if parent else "No parent")
                if task.getType() == 'ExtProject':
                    res, param = task.getParamStruct('external')
                    if res:
                        prompt = param['prompt']
                        filename = param['filename']
                        if not self.createExtProject(filename, prompt, parent):
                            print('Can not create')
                            return self.manager.getCurrTaskPrompts()
                    else:
                        print('No options')
                        return self.manager.getCurrTaskPrompts()
                else:
                    self.manager.createOrAddTask(prompt, task.getType(),prompt_tag, parent, None)
                branch['created'].append(self.manager.curr_task)

        
 
        # i = 0
        # next_idx = [0]
        # st_parent = None
        # while (i < 1000):
        #     for idx in next_idx:
        #         branch = tasks_chains[idx]
        #         for j in range(len(branch['branch'])):
        #             if j == 0:
        #                 parent = st_parent
        #             else:
        #                 parent = self.curr_task
        #             task = branch['branch'][j]
        #             self.curr_task.getla
        #             prompt=self.curr_task.getLastMsgContent() 
        #             prompt_tag=self.curr_task.getLastMsgRole()
        #             self.createOrAddTask(prompt, task.getType(),prompt_tag, parent, None)
        #         next_idx = branch['idx']
        #         st_parent = self.curr_task
        #     i+=1
        return self.manager.getCurrTaskPrompts()
    
    def getStdCmdList(self)->list:
        # comm = self.manager.getMainCommandList()
        # comm.extend(self.manager.getSecdCommandList())
        # comm.remove("New")
        # comm.remove("SubTask")
        # comm.remove("Edit")
        comm = [t for t in self.manager.helper.getNames()]
        comm.remove("Request")
        comm.remove("Response")
        return comm

    def getCustomCmdList(self) -> list:
        mypath = os.path.join('tools')
        return [f.split('.')[0] for f in listdir(mypath) if isfile(join(mypath, f))]
    
    def getFullCmdList(self):
        a = self.getCustomCmdList()
        p = self.getStdCmdList()
        a.extend(p)
        return a


    def makeCustomAction(self, prompt, selected_action, custom_action):
        if custom_action in self.getStdCmdList():
            return self.manager.makeTaskAction(prompt, custom_action, selected_action, "assistant")
        elif custom_action in self.getCustomCmdList():
            if selected_action == "New":
                self.newExtProject(custom_action, prompt)
            elif selected_action == "SubTask":
                self.appendExtProject(custom_action, prompt)
        return self.manager.getCurrTaskPrompts()
 