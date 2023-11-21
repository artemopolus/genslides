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
        mypath = "projects/"
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

        self.path_to_projectfile = os.path.join('saved','project.json')
        if os.path.exists(self.path_to_projectfile):
            with open(self.path_to_projectfile,'r') as f:
                self.info = json.load(f)
        else:
            self.info = {'actions':[]}
            self.save()

    def save(self):
        with open(self.path_to_projectfile,'w') as f:
            json.dump(self.info, indent=1)

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
        mypath = 'tools'
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
        self.current_project_name = name
        self.manager.setParam("current_project_name",self.current_project_name)

        # Archivator.saveOnlyFiles(self.savedpath, self.mypath, name)
        Archivator.saveAll(self.savedpath, self.mypath, name)

        return gr.Dropdown.update( choices= self.loadList(), interactive=True)

    def copyChildChains(self, edited_prompt = '',swith_to_type = '', apply_link = False, remove_old_link = False):
        print(10*"----------")
        print('Copy child chains')
        print(10*"----------")
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
                task = branch['branch'][j]
                prompt=task.getLastMsgContent() 
                prompt_tag=task.getLastMsgRole()
                trg_type = task.getType()
                if j == 0:
                    if i != 0:
                        parent = tasks_chains[branch['i_par']]['created'][-1]
                    branch['created'] = []
                    if i == 0:
                        if len(edited_prompt) > 0:
                            parent = self.manager.curr_task.parent
                            prompt = edited_prompt
                        if len(swith_to_type) > 0:
                            trg_type = swith_to_type
                else:
                    parent = self.manager.curr_task
                print('branch',i,'task',j,'par',parent.getName() if parent else "No parent")
                if trg_type == 'ExtProject':
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
                    self.manager.createOrAddTask(prompt, trg_type, prompt_tag, parent, [])

                if apply_link:                
                    in_tasks_list = task.getAffectingOnTask()
                    for in_task in in_tasks_list:
                        self.manager.makeLink(in_task, self.manager.curr_task)
                    out_tasks_list = task.getAffectedTasks()
                    for out_task in out_tasks_list:
                        self.manager.makeLink( self.manager.curr_task, out_task)

                if remove_old_link:
                    task.removeLinkToTask()
                        
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
        mypath = 'tools\\'
        return [f.split('.')[0] for f in listdir(mypath) if isfile(join(mypath, f))]
    
    def getFullCmdList(self):
        a = self.getCustomCmdList()
        p = self.getStdCmdList()
        a.extend(p)
        return a


    def makeCustomAction(self, prompt, selected_action, custom_action):
        if custom_action in self.getStdCmdList():
            return self.makeTaskAction(prompt, custom_action, selected_action, "assistant")
        elif custom_action in self.getCustomCmdList():
            if selected_action == "New":
                self.newExtProject(custom_action, prompt)
            elif selected_action == "SubTask":
                self.appendExtProject(custom_action, prompt)
        elif custom_action == 'MakeGarland':
            self.manager.createCollectTreeOnSelectedTasks(selected_action)
        return self.manager.getCurrTaskPrompts()
    
    def makeResponseAction(self, selected_action):
        return self.makeTaskAction("", "Response",selected_action, "assistant")
    
    def makeRequestAction(self, prompt, selected_action, selected_tag):
        print('Make',selected_action,'Request')
        if selected_action == "New" or selected_action == "SubTask" or selected_action == "Insert":
            return self.makeTaskAction(prompt, "Request", selected_action, "user")
        if selected_action == "Edit":
            return self.makeTaskAction(prompt, "Request", selected_action, selected_tag)
        # # if selected_action == "EditCopy":
        #     return self.copyChildChains(edited_prompt=prompt)
        if selected_action == "EdCp1":
            return self.copyChildChains(edited_prompt=prompt, apply_link= True, remove_old_link=True)
        if selected_action == "EdCp2":
            return self.copyChildChains(edited_prompt=prompt, apply_link= True, remove_old_link=False)
        if selected_action == "EdCp3":
            return self.copyChildChains(edited_prompt=prompt, apply_link= False, remove_old_link=True)
        if selected_action == "EdCp4":
            return self.copyChildChains(edited_prompt=prompt, apply_link= False, remove_old_link=False)

    def createCollectTreeOnSelectedTasks(self, action_type):
        return self.manager.createCollectTreeOnSelectedTasks(action_type)
    

    def addActions(self, action = '', prompt = '', tag = '', act_type = ''):
        id = len(self.info)
        self.info['actions'].append({'id': id,'action':action,'prompt':prompt,'tag':tag,'type':act_type })


    
    def makeTaskAction(self, prompt, type, creation_type, creation_tag):
        if creation_type in self.getMainCommandList() or creation_type in self.vars_param:
            return self.manager.makeTaskActionBase(prompt, type, creation_type, creation_tag)
        elif creation_type in self.getSecdCommandList():
            return self.manager.makeTaskActionPro(prompt, type, creation_type, creation_tag)
        elif creation_type == "MoveCurrTaskUP":
            return self.manager.moveTaskUP(self.manager.curr_task)
        return self.manager.getCurrTaskPrompts()
 

    def makeActionParent(self):
        return self.makeTaskAction("","","Parent","")
    def makeActionUnParent(self):
        return self.makeTaskAction("","","Unparent","")
    def makeActionLink(self):
        return self.makeTaskAction("","","Link","")
    def makeActionUnLink(self):
        return self.makeTaskAction("","","Unlink","")
    def deleteActionTask(self):
        return self.makeTaskAction("","","Delete","")
    def extractActionTask(self):
        return self.makeTaskAction("","","Remove","")
    def removeActionBranch(self):
        return self.makeTaskAction("","","RemoveBranch","")
    def removeActionTree(self):
        return self.makeTaskAction("","","RemoveTree","")
 
    def appendNewParamToTask(self, param_name):
        return self.manager.appendNewParamToTask(param_name)
    
    def setTaskKeyValue(self, param_name, key, slt_value, mnl_value):
        return self.manager.setTaskKeyValue(param_name, key, slt_value, mnl_value)
    
    
 