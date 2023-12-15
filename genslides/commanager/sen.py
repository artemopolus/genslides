from genslides.task.base import TaskManager, BaseTask
from genslides.utils.savedata import SaveData
from genslides.utils.archivator import Archivator
from genslides.commanager.jun import Manager
from genslides.commanager.group import Actioner

from genslides.utils.reqhelper import RequestHelper
from genslides.utils.testrequest import TestRequester
from genslides.utils.searcher import GoogleApiSearcher

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
    def __init__(self, manager : Manager = None, path = 'saved') -> None:
        mypath = "projects/"
        self.ext_proj_names = []
        ex_path = os.path.join(path,'ext')
        if os.path.exists(ex_path):
            fldrs = [f for f in listdir(ex_path) if os.path.isdir(os.path.join(ex_path, f))]
            self.ext_proj_names = fldrs
        if not os.path.exists(mypath):
            os.makedirs(mypath)
        self.mypath = mypath
        task_man = TaskManager()
        self.savedpath = task_man.getPath()
        self.manager = manager
        self.manager.initInfo(self.loadExtProject)
        self.manager.loadTasksList()

        self.actioner = Actioner(manager)
        # saver = SaveData()
        # saver.removeFiles()
        self.current_project_name = self.manager.getParam("current_project_name")
        if self.current_project_name is None:
            self.current_project_name = 'Unnamed'
        self.updateSessionName()
        self.actioner.clearTmp()

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
        self.manager.initInfo(self.loadExtProject)

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
    
    
    def loadExtProject(self, filename, manager : Manager) -> bool:
        mypath = 'tools'
        if filename + '.7z' in [f for f in listdir(mypath) if isfile(join(mypath, f))]:
            ext_pr_name = 'pr' + str(len(self.ext_proj_names))
            trg = os.path.join(manager.getPath(),'ext', ext_pr_name) +'/'
            if Archivator.extractFiles(mypath, filename, trg):
                self.ext_proj_names.append(ext_pr_name)
                print('Append project',filename,'task to', trg)
                return True, ext_pr_name
        return False, ''
    
    
    def save(self, name):
        self.current_project_name = name
        self.manager.setParam("current_project_name",self.current_project_name)

        # Archivator.saveOnlyFiles(self.savedpath, self.mypath, name)
        Archivator.saveAll(self.savedpath, self.mypath, name)

        return gr.Dropdown.update( choices= self.loadList(), interactive=True)

   
    
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
    
    def makeTaskAction(self, prompt, type1, creation_type, creation_tag, param = {}, save_action = True):
        return self.actioner.makeTaskAction(prompt, type1, creation_type, creation_tag, param , save_action)
        # return self.manager.getCurrTaskPrompts()
 

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
    
    def goToNextBranchEnd(self):
        return self.actioner.manager.goToNextBranchEnd()
    
    def goToNextBranch(self):
        return self.actioner.manager.goToNextBranch()
    
    def goToNextTree(self):
        return self.actioner.manager.goToNextTree()
    
    def goToNextChild(self):
        return self.actioner.manager.goToNextChild()
        # return self.makeTaskAction("","","GoToNextChild","")

    def goToParent(self):
        return self.actioner.manager.goToParent()
        # return self.makeTaskAction("","","GoToParent","")
   
    def switchRole(self, role, prompt):
        task = self.actioner.manager.curr_task
        print('Set role[', role, ']for',task.getName())
        self.makeTaskAction(task.getLastMsgContent(), "Request", "Edit", role)
        return self.actioner.manager.getCurrTaskPrompts(prompt)
  
 
    def appendNewParamToTask(self, param_name):
        return self.makeTaskAction('','','AppendNewParam','', {'name':param_name})
    
    def setTaskKeyValue(self, param_name, key, slt_value, mnl_value):
        return self.makeTaskAction('','','SetParamValue','', {'name':param_name,'key':key,'select':slt_value,'manual':mnl_value})
    
    def getMainCommandList(self):
        return self.manager.getMainCommandList()

    def getSecdCommandList(self):
        return self.manager.getSecdCommandList()
    
   

    def newExtProject(self, filename, prompt):
        return self.makeTaskAction(prompt,"New","NewExtProject","")
    def appendExtProject(self, filename, prompt):
        return self.makeTaskAction(prompt,"SubTask","SubExtProject","")
    

    def initPrivManager(self):
        self.makeTaskAction("","","InitPrivManager","", {'actions':[],'repeat':3})
        return self.actioner.getTmpManagerInfo()
    
    def loadPrivManager(self, name):
        self.makeTaskAction("","","InitSavdManager","", {'task': name})
        return self.actioner.getTmpManagerInfo()
   
    def stopPrivManager(self):
        self.makeTaskAction("","","StopPrivManager","")
        return self.actioner.getTmpManagerInfo()
  
    def rmvePrivManager(self):
        self.makeTaskAction("","","RmvePrivManager","")
        return self.actioner.getTmpManagerInfo()
    
    def getPrivManager(self):
        return self.actioner.getTmpManagerInfo()

    def exeActions(self):
        # Закомментированной командой производится запись команды в список команд менеджера
        # self.makeTaskAction("","","ExecuteManager","")
        # Для исполнения команд нужна отдельная команда, чтобы не переводить это все в цикл
        self.actioner.exeCurManager()
        # Альтернатива
        # self.makeTaskAction("","","ExecuteManager","",{},save_action=False)
        return self.actioner.getTmpManagerInfo()

    def editParamPrivManager(self, param):
        self.makeTaskAction("","","EditPrivManager","",param)
        return self.actioner.getTmpManagerInfo()

    def actionTypeChanging(self, action):
        print('Action switch to=', action)
        if action == 'New':
            return "", gr.Button(value='Request'), gr.Button(value='Response', interactive=False), gr.Button(value='Custom',interactive=True), gr.Radio(interactive=False)
        elif action == 'SubTask' or action == 'Insert':
            return "", gr.Button(value='Request'), gr.Button(value='Response', interactive=True), gr.Button(value='Custom',interactive=True), gr.Radio(interactive=False)
        elif action == 'Edit' or action == 'EditCopy' or action.startswith('EdCp'):
            print('Get text from',self.actioner.manager.curr_task.getName(),'(',self.actioner.manager.getName(),')')
            _,role,_ = self.actioner.manager.curr_task.getMsgInfo()
            return self.actioner.manager.getCurTaskLstMsgRaw(), gr.Button(value='Apply'), gr.Button(value='',interactive=False), gr.Button(value='',interactive=False), gr.Radio(interactive=True,value=role)

    def getActionsList(self) -> list:
        actions = self.actioner.manager.info['actions']
        out = []
        for act in actions:
            name = ':'.join([str(act['id']),act['action'],act['type']])
            out.append(name)
        return gr.CheckboxGroup(choices=out, interactive=True,value=None)
    
    def moveActionUp(self, names: list):
        for name in names:
            pack = name.split(':')
            actions = self.actioner.manager.info['actions']
            print(pack)
            for idx in range(len(actions)):
                print(pack[0],'check',actions[idx]['id'])
                if pack[0] == str(actions[idx]['id']) and idx > 0:
                    actions.insert(idx - 1, actions.pop(idx))
        self.fixActionsIdx()
        return self.getActionsList()
    
    def fixActionsIdx(self):
        actions = self.actioner.manager.info['actions']
        for idx in range(len(actions)):
            actions[idx]['id'] = idx

    def delAction(self, names: list):
        for name in names:
            pack = name.split(':')
            actions = self.actioner.manager.info['actions']
            for idx in range(len(actions)):
                if pack[0] == str(actions[idx]['id']) and idx > 0:
                    actions.pop(idx)

        self.fixActionsIdx()
        return self.getActionsList()
    
    def saveAction(self):
        self.actioner.manager.saveInfo()
        return self.getActionsList()
    
    def setManagerStartTask(self, name: str):
        print('set Manager start task to',name)
        all_mans = [self.actioner.std_manager]
        all_mans.extend(self.actioner.tmp_managers)
        all_mans.remove(self.actioner.manager)
        all_tasks = []
        for man in all_mans:
            all_tasks.extend([t.getName() for t in man.task_list])
        print('Available task:', all_tasks)
        if name in all_tasks:
            print('set name')
            self.actioner.manager.info['task'] = name
        return self.actioner.getTmpManagerInfo()
    
    def setCurrAsManagerStartTask(self):
        name = self.actioner.manager.curr_task.getName()
        return self.setManagerStartTask(name)
    
    def backToStartTask(self):
        manager = self.actioner.manager
        task = manager.getTaskByName(manager.getName())
        manager.curr_task = task
        return self.actioner.manager.getCurrTaskPrompts()

    def setCurrentExtTaskOptions(self, names : list):
        self.makeTaskAction("","","SetCurrentExtTaskOptions","", {'names': names})
        return self.actioner.getTmpManagerInfo()
    
    def getAvailableActionsList(self):
        return [t['action'] for t in self.actioner.getActionList()]
    
    def getAvailableActionTemplate(self, action_name : str):
        for action in self.actioner.getActionList():
            if action['action'] == action_name:
                return json.dumps(action['param'], indent=1)
        return '{\n}'
    
    def addActionToCurrentManager(self, action: str, param : str):
        self.actioner.manager.addActions(action=action, param=json.loads(param))
        return self.getActionsList()

