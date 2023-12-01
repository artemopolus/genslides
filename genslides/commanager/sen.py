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
        loaded = False
        if os.path.exists(self.path_to_projectfile):
            try:
                with open(self.path_to_projectfile,'r') as f:
                    self.info = json.load(f)
                    loaded = True
            except:
                pass
        if not loaded:
            self.info = {'actions':[]}
            self.saveInfo()

    def saveInfo(self):
        with open(self.path_to_projectfile,'w') as f:
            json.dump(obj=self.info, fp=f, indent=1)

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

    def copyChildChains(self, edited_prompt = '',swith_to_type = '', apply_link = False, remove_old_link = False, copy = False):
        print(10*"----------")
        print('Copy child chains')
        print(10*"----------")
        link_array, start_node = self.copyChildChainTask(edited_prompt, swith_to_type)
        print(link_array)
        idx = 0
        while(idx < 1000):
            link_array_new = []
            for link in link_array:
                task = link['task']
                holders = link['holders']
                garlandparts = link['garlandparts']
                print(task.getName())
                print('holders', [t.getName() for t in holders])
                print('garlandparts', [t.getName() for t in garlandparts])
                if apply_link:                
                    for holder in holders:
                        if remove_old_link:
                            self.manager.curr_task = holder
                            self.manager.makeTaskActionBase("","","Unlink","")
                            holder.removeLinkToTask()
                            # self.manager.makeLink( task, holder)
                        if copy:
                            print('================================================Copy')
                            self.manager.curr_task = holder
                            new_la, new_sn = self.copyChildChainTask(task.getLastMsgContent(), forced_parent=True)
                            print(holder)
                            print(new_sn)
                            for l in new_la:
                                if new_sn == l['task']:
                                    new_la.remove(l)
                            link_array_new.extend( new_la )
                            print(link_array_new)
                            self.manager.makeLink( new_sn, task )

                    for part in garlandparts:
                        self.manager.makeLink( task, part )
                        
            if len(link_array_new) == 0:
                break
            link_array = link_array_new
            idx += 1

        return self.manager.getCurrTaskPrompts()
    
    def copyChildChainTask(self, edited_prompt = '',swith_to_type = '', forced_parent = False):
        print('Copy child chain tasks')
        tasks_chains = self.manager.curr_task.getChildChainList()
        print('Task chains:')
        i = 0
        for branch in tasks_chains:
            print(i,[task.getName() for task in branch['branch']], branch['done'], branch['idx'],  branch['parent'].getName() if branch['parent'] else "None", branch['i_par'])
            i+= 1
        parent = None

        link_array = []
        start = None

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
                        if len(edited_prompt) > 0 or forced_parent:
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

                if i == 0 and j == 0:
                    start = self.manager.curr_task
                if len(task.getHoldGarlands()) or len(task.getGarlandPart()):
                    link_array.append({'task':self.manager.curr_task,
                                   'holders': task.getHoldGarlands(), 
                                   'garlandparts': task.getGarlandPart()})

                        
                branch['created'].append(self.manager.curr_task)
        return link_array, start

    
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
                return self.makeTaskAction(prompt, custom_action, "NewExtProject", "")
            elif selected_action == "SubTask":
                return self.makeTaskAction(prompt, custom_action, "SubExtProject", "")
        elif custom_action == 'Garland':
            self.makeTaskAction('', custom_action, selected_action, '')
        return self.manager.getCurrTaskPrompts()
    
    def makeResponseAction(self, selected_action):
        return self.makeTaskAction("", "Response",selected_action, "assistant")
    
    def makeRequestAction(self, prompt, selected_action, selected_tag):
        print('Make',selected_action,'Request')
        if selected_action == "New" or selected_action == "SubTask" or selected_action == "Insert":
            return self.makeTaskAction(prompt, "Request", selected_action, "user")
        elif selected_action == "Edit":
            return self.makeTaskAction(prompt, "Request", selected_action, selected_tag)
        else:
            return self.makeTaskAction(prompt, "", selected_action, selected_tag)
        # # if selected_action == "EditCopy":
        #     return self.copyChildChains(edited_prompt=prompt)

    def createCollectTreeOnSelectedTasks(self, action_type):
        return self.manager.createTreeOnSelectedTasks(action_type,"Collect")
    
    def createShootTreeOnSelectedTasks(self, action_type):
        return self.manager.createTreeOnSelectedTasks(action_type,"GroupCollect")

    def addActions(self, action = '', prompt = '', tag = '', act_type = '', param = {}, manager = None):
        id = len(self.info['actions'])
        action = {'id': id,'action':action,'prompt':prompt,'tag':tag,'type':act_type, 'param': param }
        if not manager:
            manager = self.manager

        action['current'] = self.manager.curr_task.getName() if self.manager.curr_task else None
        action['slct'] = self.manager.slct_task.getName() if self.manager.slct_task else None
        action['selected'] = [t.getName() for t in self.manager.selected_tasks]


        self.info['actions'].append(action)
        self.saveInfo()


    
    def makeTaskAction(self, prompt, type1, creation_type, creation_tag, param = {}):
        self.addActions(action = creation_type, prompt = prompt, act_type = type1, param = param, manager = self.manager)
        if type1 == "Garland":
            return self.manager.createCollectTreeOnSelectedTasks(creation_type)
        elif creation_type == "NewExtProject":
            return self.newExtProject(type1, prompt)
        elif creation_type == "SubExtProject":
            return self.appendExtProject(type1, prompt)
        elif creation_type in self.getMainCommandList() or creation_type in self.manager.vars_param:
            return self.manager.makeTaskActionBase(prompt, type1, creation_type, creation_tag)
        elif creation_type in self.getSecdCommandList():
            return self.manager.makeTaskActionPro(prompt, type1, creation_type, creation_tag)
        elif creation_type == "MoveCurrTaskUP":
            return self.manager.moveTaskUP(self.manager.curr_task)
        elif creation_type == "EdCp1":
            return self.copyChildChains(edited_prompt=prompt, apply_link= True, remove_old_link=True)
        elif creation_type == "EdCp2":
            return self.copyChildChains(edited_prompt=prompt, apply_link= True, remove_old_link=False)
        elif creation_type == "EdCp3":
            return self.copyChildChains(edited_prompt=prompt, apply_link= False, remove_old_link=False)
        elif creation_type == "EdCp4":
            return self.copyChildChains(edited_prompt=prompt, apply_link= True, copy=True)
        elif creation_type == "AppendNewParam":
            return self.manager.appendNewParamToTask(param['name'])
        elif creation_type == "SetParamValue":
            return self.manager.setTaskKeyValue(param['name'], param['key'], param['select'], param['manual'])
        

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
    def moveCurrentTaskUP(self):
        return self.makeTaskAction("","","MoveCurrTaskUP","")
 
    def appendNewParamToTask(self, param_name):
        return self.makeTaskAction('','','AppendNewParam','', {'name':param_name})
    
    def setTaskKeyValue(self, param_name, key, slt_value, mnl_value):
        return self.makeTaskAction('','','SetParamValue','', {'name':param_name,'key':key,'select':slt_value,'manual':mnl_value})
    
    def getMainCommandList(self):
        return self.manager.getMainCommandList()

    def getSecdCommandList(self):
        return self.manager.getSecdCommandList()
