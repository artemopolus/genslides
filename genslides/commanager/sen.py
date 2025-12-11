from genslides.task.base import TaskManager, BaseTask, TaskDescription
from genslides.utils.savedata import SaveData, getTimeForSaving
from genslides.utils.archivator import Archivator
from genslides.commanager.jun import Manager
from genslides.commanager.group import Actioner

from genslides.utils.reqhelper import RequestHelper
from genslides.utils.testrequest import TestRequester
from genslides.utils.searcher import GoogleApiSearcher
import genslides.utils.loader as Loader
import genslides.utils.finder as Finder
import genslides.utils.searcher as Searcher
import genslides.utils.filemanager as FileManager
import genslides.utils.readfileman as Reader
import genslides.utils.writer as Writer
import genslides.utils.ids as Ids

import genslides.task_tools.py_parser as pyparser
import genslides.commanager.com as Commander

import genslides.task_tools.text as TextTool
import genslides.task_tools.cmds as CommandTool

from os import listdir
from os.path import isfile, join


import os
import json
import gradio as gr
import datetime
import time

import pyperclip
import pathlib
from pathlib import Path
import matplotlib.pyplot as plt
import copy

class Projecter(Commander.Commander):
    def __init__(self, manager : Manager = None, path = 'saved') -> None:
        super().__init__(path = "session")
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


        self.tmp_actioner = None
        self.tmp_actioner_task = None

        # self.actioners_list : list[Actioner] = []


        self.resetManager(manager, load=False)
        # saver = SaveData()
        # saver.removeFiles()
        self.current_project_name = self.manager.getParam("current_project_name")
        if self.current_project_name is None:
            self.current_project_name = 'Unnamed'
        self.updateSessionName()
        self.actioner.clearTmp()

        self.exttreemanbudinfo = None
        self.tree3plaintext_tasks = []
        self.tree3plaintext_idx = 0

        self.exttreeact = []
        # self.session_names_list.append(trg_name)

        self.sec_actioner : Actioner = None

        self.trg_actioner : Actioner = None

        self.actions_info = []
        self.actions_source = ""


        self.params['workgraph'] = {"Request":5000,"Response":5000,"Default":10000,'on':True}
        self.params['stepgraph'] = {"Request":5000,"Response":5000,"Default":10000,'on':False}
        self.params['uat'] = {'uat_times': 1}
        self.params['instructions'] = [] 

        self.show_workgraph = True

    def getUAT_Times(self):
        return self.params['uat']['uat_times']
    
    def setUAT_Times(self, value):
        self.params['uat']['uat_times'] = value
        self.saveSession()
        return self.updateMainUIelements()


    def getRequestTaskSymVizCount(self):
        return self.params['workgraph']['Request']

    def getResponseTaskSymVizCount(self):
        return self.params['workgraph']['Response']
 
    def getDefaultTaskSymVizCount(self):
        return self.params['workgraph']['Default']

    def getStepRequestTaskSymVizCount(self):
        return self.params['stepgraph']['Request']

    def getStepResponseTaskSymVizCount(self):
        return self.params['stepgraph']['Response']
 
    def getStepDefaultTaskSymVizCount(self):
        return self.params['stepgraph']['Default']

    def setRequestTaskSymVizCount(self, number):
        self.params['workgraph']['Request'] = number
        self.saveSession()
        return self.updateMainUIelements()

    def setResponseTaskSymVizCount(self, number):
        self.params['workgraph']['Response'] = number
        self.saveSession()
        return self.updateMainUIelements()

    def setDefaultTaskSymVizCount(self, number):
        self.params['workgraph']['Default'] = number
        self.saveSession()
        return self.updateMainUIelements()


    def setStepRequestTaskSymVizCount(self, number):
        self.params['stepgraph']['Request'] = number
        self.saveSession()
        return self.updateMainUIelements()

    def setStepResponseTaskSymVizCount(self, number):
        self.params['stepgraph']['Response'] = number
        self.saveSession()
        return self.updateMainUIelements()
    
    def setStepDefaultTaskSymVizCount(self, number):
        self.params['stepgraph']['Default'] = number
        self.saveSession()
        return self.updateMainUIelements()
    
    def setStepTaskSymCount(self, value):
        self.params['stepgraph']['on'] = value
        self.saveSession()
        return self.updateMainUIelements()

   
    def getSessionNameList(self):
        names = self.session_names_list.copy()
        names.sort(key=self.getModificationTimeOfSession, reverse=True)
        return names
        # return self.session_names_list

    def getSessionName(self):
        session_names = self.getSessionNameList()
        return gr.Dropdown(choices=session_names, value=self.getCurrentSessionName(), interactive=True)
    
    def setNewSessionName(self, name):
        if name not in self.session_names_list:
            self.setCurrentSessionMame( name )
            self.session_names_list.append(name)
            self.saveSession()
        return  (
            self.getCurrentSessionName(),
            self.getSessionName()
            )
    
    def getSessionNameFromList(self, name):
        if name in self.session_names_list:
            print(f"Load session \"{name}\"")
            self.setCurrentSessionMame( name )
            self.loadSession()
        else:
            print(f"Can\'t find {name} in {self.session_names_list}")
        
        return self.updateTreeAndAll()
    


    def loadManager(self):
        self.resetManager(self.actioner.std_manager)
        if len(self.actioner.std_manager.task_list) == 0:
            return self.createNewTree()
        return self.updateMainUIelements()
    
    def loadManagerByPath(self, path : str):
        print('Load manager by path',path)
        man_path = Loader.Loader.getUniPath(path)
        self.actioner.std_manager.setPath(man_path)
        self.resetManager(manager = self.actioner.std_manager, path = man_path)
        if len(self.actioner.std_manager.task_list) == 0:
            self.createNewTree()
        print('Load manager from browser is complete')
        man = self.actioner.std_manager
        python_path = Finder.findByKey("[[project:RunScript:python]]", man, man.curr_task, man.helper)
        fld = Finder.findByKey("[[manager:path:fld]]", man, man.curr_task, man.helper)
        spc = Finder.findByKey("[[manager:path:spc]]", man, man.curr_task, man.helper)
        # print("Vars for manager")
        # print(f"Python path: { Loader.Loader.getUniPath( python_path )}")
        # print(f"Manager folder: {Loader.Loader.getUniPath( fld )}")
        # print(f"Manager space: { Loader.Loader.getUniPath( spc )}")
   
    def loadManagerFromBrowser(self):
        man_path = Loader.Loader.getDirPathFromSystem()
        self.loadManagerByPath(path=man_path)
        return self.updateMainUIelements()

    def resetManager(self, manager : Manager, fast = True, load = True, path = 'saved'):
        if self.actioner is None:
            self.actioner = Actioner(manager)
        else:
            self.actioner.reset()
        self.actioner.setPath(path)
        self.manager = self.actioner.std_manager
        # print('Manager start tasks list:',len(self.manager.task_list))
        self.manager.onStart()
        # print('Manager after reset tasks list:',len(self.manager.task_list))
        self.manager.initInfo(self.loadExtProject, path = self.actioner.getPath())
        if load:
            self.manager.disableOutput2()
            self.manager.loadTasksList(fast)
            self.manager.enableOutput2()
            self.actioner.loadTmpManagers()

 

# сохранение сессионных имен необходимо связать только с проектером сеном, а не с менеджером
    def updateSessionName(self):
        self.setCurrentSessionMame( self.current_project_name + "_" + datetime.datetime.now().strftime("%y%m%d_%H%M%S"))
        # print("Name of session=",self.session_name_curr)
        self.manager.setParam("session_name",self.getCurrentSessionName())


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
        FileManager.deleteFiles(mypath)

    def clear(self):
        self.clearFiles()
        self.resetManager(self.manager, fast=False, load=False)

    def reload(self):
        self.resetManager(self.manager, fast=False, load=True)



    def getEvaluetionResults(self, input):
        print("In:", input)
        saver = SaveData()
        saver.updateEstimation(input)




   
    def appendProjectTasks(self):
        ppath = Loader.Loader.getFilePathFromSystemRaw()
        project_path = Loader.Loader.getUniPath(ppath.parent)
        filename = str(ppath.stem)
        tmp_manager = Manager(RequestHelper(), TestRequester(), GoogleApiSearcher())
        tmp_path = os.path.join(self.actioner.getPath(),'tmp', filename)
        print('Open file',filename,'from',project_path,'to',tmp_path)
        tmp_manager.initInfo(method = self.actioner.loadExtProject, task=None, path = tmp_path  )
        Archivator.extractFiles(project_path, filename, tmp_manager.getPath())
        self.actioner.tmp_managers.append(tmp_manager)
        tmp_manager.loadTasksList()
        # Переименовываем задачи, если нужно
        print('New task list:',[t.getName() for t in tmp_manager.task_list])
        print('Cur task list:',[t.getName() for t in self.actioner.std_manager.task_list])
        names = [t.getName() for t in self.actioner.std_manager.task_list]
        idx = 0
        for task in tmp_manager.task_list:
            trg = task.getName()
            if trg in names:
                print('Found same name',trg)
                n_name = task.getType() + str(idx)
                idx += 1
                while (n_name in names):
                    n_name = task.getType() + str(idx)
                    idx += 1
                print('New id is',idx)
                task.resaveWithID(idx)
        for task in tmp_manager.task_list:
            task.saveAllParams()
        # Копируем все в одну папку
        self.actioner.removeTmpManager(tmp_manager, self.actioner.std_manager, copy=True)


    
    
    def loadExtProject(self, filename, manager : Manager) -> bool:
        mypath = 'tools'
        if filename + '.7z' in [f for f in listdir(mypath) if isfile(join(mypath, f))]:
            res, trg = FileManager.createUniqueDir(manager.getPath(), 'ext','pr')
            if res:
                if Archivator.extractFiles(mypath, filename, Loader.Loader.getUniPath( trg)):
                    ext_pr_name = trg.stem
                    self.ext_proj_names.append(ext_pr_name)
                    print('Append project',filename,'task to', trg)
                    return True, ext_pr_name
        return False, ''
    
    def saveToTmp(self):
        out = []
        self.actioner.setManager(self.actioner.std_manager)
        man = self.actioner.getCurrentManager()
        self.actioner.saveManToTmp(man, suffix="reserved")
        out.append(self.actioner.getPath())
        act_paths = self.actioner.getRelatedActionersPaths([])
        for path in act_paths:
            act = self.getActionerByPath(path)
            if act != None:
                out.append(path)
                act.setManager(act.std_manager)
                act.saveManToTmp(act.getCurrentManager(), suffix="reserved")
        return f"Save:\n" + "\n".join(out)
    
    def load(self):
        self.actioner.setManager(self.actioner.std_manager)
        man = self.actioner.getCurrentManager()
        path = man.getPath()
        path = Loader.Loader.getUniPath(path)
        print('Load files to',path)
        project_path = Loader.Loader.getUniPath(self.mypath)
        ppath = Loader.Loader.getFilePathFromSystemRaw()
        # ppath = Loader.Loader.getFilePathArrayFromSysten(self.actioner.getCurrentManager().getPath())
        project_path = Loader.Loader.getUniPath(ppath.parent)
        filename = str(ppath.stem)

        FileManager.deleteFiles(man.getPath())
        self.loadInternal(project_path, filename, path)
        return self.updateTaskManagerUI()
 
    def loadFromTmp(self):
        print(f"========Start load from temporary file")
        act_paths = self.actioner.getRelatedActionersPaths([])
        self.loadCurrentActionerFromTmp()
        start_act = self.actioner
        for path in act_paths:
            act = self.getActionerByPath(path)
            if act != None:
                self.actioner = act
                self.loadCurrentActionerFromTmp()
        self.actioner = start_act
        return self.updateTaskManagerUI()
    
    def loadCurrentActionerFromTmp( self ):
        print(f"Load from temporary {self.actioner.getPath()}")
        self.actioner.setManager(self.actioner.std_manager)
        man = self.actioner.getCurrentManager()
        folder = Finder.findByKey("[[manager:path:fld]]", man, man.curr_task, man.helper )
        filename = Finder.findByKey("[[manager:path:spc:name]]", man, man.curr_task, man.helper )
        fld_path = Loader.Loader.getUniPath( FileManager.addFolderToPath(folder, ["tt_temp"]))
        path = Loader.Loader.getUniPath( Finder.findByKey("[[manager:path:spc]]", man, man.curr_task, man.helper ) )


        # self.clearFiles()
        # man.beforeRemove()

        project_path = fld_path

        filename += "_reserved"
        

        FileManager.deleteFiles(man.getPath())
        self.loadInternal(project_path, filename, path)
    
    def loadInternal( self, project_path, filename, path ):
        Archivator.extractFiles(project_path, filename, path)
        self.resetManager(self.actioner.getCurrentManager(), path=self.actioner.getPath())

    def save(self):
        # self.current_project_name = name
        # self.actioner.std_manager.setParam("current_project_name",self.current_project_name)

        self.actioner.setManager(self.actioner.std_manager)
        print('Save man', self.actioner.getCurrentManager().getName(),'(Temp)' if self.actioner.getCurrentManager() != self.actioner.std_manager else '(Main)')
        path = self.actioner.getCurrentManager().getPath()
        path = Loader.Loader.getUniPath(path)
        trg_path = Loader.Loader.getUniPath( Loader.Loader.getFilePathToSave7zArchive() )
        Archivator.saveAllbyPath(data_path=path, trgfile_path=trg_path)
        return "Save"
    
    def saveTmpMan(self):
        if self.actioner.getCurrentManager() == self.actioner.std_manager:
            return
        print(f"Save {self.actioner.getCurrentManager().getName()} tmp manager")
        path = Loader.Loader.getUniPath(self.actioner.getCurrentManager().getPath())
        trg_path = Loader.Loader.getUniPath( Loader.Loader.getFilePathToSave7zArchive())
        Archivator.saveAllbyPath(data_path=path, trgfile_path=trg_path)
       

   
    
    def getStdCmdList(self, full = False)->list:
        # comm = self.manager.getMainCommandList()
        # comm.extend(self.manager.getSecdCommandList())
        # comm.remove("New")
        # comm.remove("SubTask")
        # comm.remove("Edit")
        comm = [t for t in self.manager.helper.getNames()]
        if not full:
            comm.remove("Request")
            comm.remove("Response")
        return comm

    def getCustomCmdList(self) -> list:
        mypath = 'tools'
        return [f.split('.')[0] for f in listdir(mypath) if isfile(join(mypath, f))]
    
    def getFullCmdList(self, full = False) -> list[str]:
        a = self.getCustomCmdList()
        p = self.getStdCmdList(full=full)
        a.extend(p)
        return a

    def makeCustomAction(self, prompt, selected_action, custom_action):
        # print('Make custom action:', selected_action, custom_action, 'with prompt:\n', prompt)
        if custom_action in self.getStdCmdList():
            self.makeTaskAction(prompt, custom_action, selected_action, "assistant")
        elif custom_action in self.getCustomCmdList():
            if selected_action == "New":
                return self.makeTaskAction(prompt, custom_action, "NewExtProject", "")
            elif selected_action == "SubTask":
                return self.makeTaskAction(prompt, custom_action, "SubExtProject", "")
            elif selected_action == "Insert":
                return self.makeTaskAction(prompt, custom_action, "InsExtProject", "")
        elif custom_action == 'Garland':
            self.makeTaskAction('', custom_action, selected_action, '')
        return self.updateMainUIelements()
    
    def makeResponseAction(self, prompt, selected_action, selected_tag, checks):
        if selected_action == 'Edit':
            return self.makeTaskAction(prompt, "Request","Divide", selected_tag, param=self.setEditChecks(checks))
        else:
            return self.makeTaskAction("", "Response",selected_action, "assistant")
    
    def getParamListForEdit(self):
        return ['copy_editbranch', #Копировать ветвь
                'resp2req','coll2req','read2req','run2req', #конвертировать задачи этого типа в другой
                'in','out','link','av_cp', #Параметры ветвления
                # 'step','chckresp',
                'sel2par', # Копировать и ветвиться от выбранной задачи
                'ignrlist',
                'wishlist', #
                'upd_cp', #Обновить ветки, которые скопирован ранее через Edit
                'onlymulti', #Копировать только мультивыбранные задачи
                'reqSraw', #Конвертировать ссылки в сообщениях при копировании
                'forcecopyresp', #Насильно вставлять промпт в Response,
                'check_man', #проверять менеджера,
                'dont' #нечего не делать просто сохранить 
                ]
    
    def setEditChecks(self, checks):
        return self.setEditChecksByManager(checks, self.actioner.getCurrentManager())

    def setEditChecksByManager(self, checks, manager : Manager):
        return manager.getEditChecks( checks )
    
    def makeRequestAction(self, prompt, selected_action, selected_tag, checks):
        # print('Make',selected_action,'Request\n', prompt)
        act_type = ""
        param = {}
        if selected_action == "New" or selected_action == "SubTask" or selected_action == "Insert":
            act_type = "Request"
            selected_tag = "user"
            return self.makeTaskAction(prompt=prompt,type1= act_type,creation_type= selected_action,creation_tag= selected_tag, param=param)
        elif selected_action == "Edit":
            act_type = "Request"
        if len(checks) > 0:
            param = self.setEditChecks(checks=checks)
        # print('Action param=', param)
        return self.makeTaskAction(prompt=prompt,type1= act_type,creation_type= selected_action,creation_tag= selected_tag, param=param)

    def createGarlandOnSelectedTasks(self, action_type):
        self.actioner.getCurrentManager().createTreeOnSelectedTasks(action_type,'Garland')
        return self.updateMainUIelements()

    def createCollectTreeOnSelectedTasks(self, action_type):
        self.actioner.getCurrentManager().createTreeOnSelectedTasks(action_type,"Collect")
        return self.updateMainUIelements()
    
    def createShootTreeOnSelectedTasks(self, action_type):
        self.actioner.getCurrentManager().createTreeOnSelectedTasks(action_type,"Listener")
        return self.updateMainUIelements()
    
    def makeTaskAction(self, prompt, type1, creation_type, creation_tag, param = {}, save_action = True):
        self.actioner.makeTaskAction(prompt, type1, creation_type, creation_tag, param , save_action)
        return self.updateMainUIelements()
 

    def makeActionParent(self):
        man = self.actioner.getCurrentManager()
        if len(man.selected_tasks) == 0:
            return self.updateMainUIelements()
        else:
            param = {'select': man.getSelectedTask().getName()}
        return self.makeTaskAction("","","Parent","", param)
    
    def reparentCurTaskChildsUP(self):
        man = self.actioner.getCurrentManager()
        new_parent = man.curr_task.getParent()
        if new_parent != None:
            man.addTaskToSelectList(new_parent)
            for child in man.curr_task.getChilds():
                man.curr_task = child
                self.makeActionParent()
            man.curr_task = new_parent
        return self.updateMainUIelements()

    def swicthCurTaskUP(self):
        man = self.actioner.getCurrentManager()
        task_B = man.curr_task.getParent()
        if task_B != None:
            task_A = task_B.getParent()
            task_C = man.curr_task
            if task_C != None:
                man.addTaskToSelectList(task_A)
                man.curr_task = task_C
                self.makeActionParent()
                man.addTaskToSelectList(task_C)
                man.curr_task =task_B 
                self.makeActionParent()
                man.curr_task = task_C
        return self.updateMainUIelements()


    
    def makeActionChild(self):
        man = self.actioner.getCurrentManager()
        if len(man.selected_tasks) == 0:
            return self.updateMainUIelements()
        else:
            param = {'curr': man.getSelectedTask().getName()}
        return self.makeTaskAction("","","Parent","", param)
    
    def makeMultiSelectedAsChilds(self):
        man = self.actioner.getCurrentManager()
        target = man.getCurrentTask()
        for task in man.getMultiSelectedTasks():
            param = {'curr': task.getName()}
            man.setCurrentTask(target)
            self.makeTaskAction("","","Parent","", param)
        return self.updateMainUIelements()


    def makeActionUnParent(self):
        return self.makeTaskAction("","","Unparent","")
    
    def breakLinkToChildren(self):
        man = self.actioner.getCurrentManager()
        trg = man.getCurrentTask()
        par = trg.getParent()
        linkedtasks = trg.getHoldGarlands()
        for idx, task in enumerate( linkedtasks ):
            if idx != 0:
                _,role,_ = task.getMsgInfo()
                prompt = self.actioner.getCurrentManager().getCurTaskLstMsgRaw()
                man.setCurrentTask( par )
                selected_action = "SubTask"
                act_type = "Request"
                self.makeTaskAction(prompt=prompt,type1= act_type,creation_type= selected_action,creation_tag= role)
                created = man.getCurrentTask()
                man.setCurrentTask( task )
                self.makeTaskAction("","","Unlink","")
                man.setCurrentTask( created )
                param = {'curr': task.getName()}
                self.makeTaskAction("","","Link","", param)
        return self.updateMainUIelements()

    

    def makeActionLink(self):
        man = self.actioner.getCurrentManager()
        if len(man.selected_tasks) == 0:
            return self.updateMainUIelements()
        else:
            param = {'select': man.getSelectedTask().getName()}
        return self.makeTaskAction("","","Link","", param)
 
    def makeActionRevertLink(self):
        man = self.actioner.getCurrentManager()
        if len(man.selected_tasks) == 0:
            return self.updateMainUIelements()
        else:
            param = {'curr': man.getSelectedTask().getName()}
        return self.makeTaskAction("","","Link","", param)
    

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
    def moveCurrentTaskDownPrefferedToMultiChild ( self ):
        return self.makeTaskAction("","","MoveCurrTaskDown","")
    
    def uniteTask(self):
        man = self.actioner.getCurrentManager()
        task = man.curr_task
        par = task.getParent()
        if par is not None:
            man.curr_task = par
            text = par.getLastMsgContentRaw()
            self.makeTaskAction("","","Remove","")
            text += task.getLastMsgContentRaw()
            man.curr_task = task
            selected_tag = task.getLastMsgRole()
            self.makeTaskAction(text, "Request", "Edit", selected_tag, [])
        return self.updateMainUIelements()

    
    def goToNextBranchEnd(self):
        self.actioner.getCurrentManager().goToNextBranchEnd()
        return self.updateMainUIelements()
    
    def getComparisonTypes(self):
        return ['Selected','MultiSelect','Buds']
    
    def getBudMsgs(self, select_type):
        buds_chat = []
        iterate_array = []
        if select_type == 'Buds':
            iterate_array = self.actioner.getCurrentManager().getBranchEndTasksList()
        elif select_type == 'MultiSelect':
            iterate_array = self.actioner.getCurrentManager().getMultiSelectedTasks()
        elif select_type == 'Selected':
            iterate_array = [self.actioner.getCurrentManager().getSelectedTask()]
        for idx, bud in enumerate(iterate_array):
            name = bud.getName()
            res, contents, _ = bud.getLastMsgAndParent()
            if res:
                content = contents.pop()
                content['content'] = name + '\n\n---\n\n' + content['content']
                if idx % 2:
                    content['role'] = 'user'
                else:
                    content['role'] = 'assistant'

                buds_chat.append(content)

        res, contents, _ = self.actioner.getCurrentManager().getCurrentTask().getLastMsgAndParent()
        curr_chat = [ contents.pop()]
        
        return [self.actioner.getCurrentManager().convertMsgsToChat(curr_chat), 
                    self.actioner.getCurrentManager().convertMsgsToChat(buds_chat)]

    def getCopyBranch(self, id_branch):
        print('Get copy id:', id_branch)
        out = [self.actioner.getCurrentManager().getChatRecord(id_branch)]
        out.extend( list( self.getCopyBranchesInfo()))
        return out
    
    def getCopyBranchRow(self, id_task):
        print('Get copy row by id:', id_task)
        out = [self.actioner.getCurrentManager().getChatRecordRow(id_task)]
        out.extend(list(self.getCopyBranchesInfo()))
        return out
    
    def getCopyBranchesInfo(self):
        data = self.actioner.getCurrentManager().curr_task.getChatRecords()
        data_len = len(data)
        data_chatlen = 0
        data_info  = 'Copyed num: ' + str(data_len) + '\n'
        if len(data):
            data_chatlen = len(data[0]['chat'])
            data_info += 'Branch len: ' + str(data_chatlen)
        return (data_info, 
                gr.Slider(minimum=0, maximum=data_len - 1 if data_len > 0 else 0, step=1),
                gr.Slider(minimum=0, maximum=data_chatlen - 1 if data_chatlen > 0 else 0, step=1)
                )
    def makeTaskRecordable(self):
        self.actioner.getCurrentManager().curr_task.setRecordsParam()
        return self.updateMainUIelements()
    
    def clearTaskRecords( self ):
        self.actioner.getCurrentManager().curr_task.clearRecordParam()
        return self.updateMainUIelements()
    
    def getRecordBranchTasks( self, actioner_path ):
        out = []
        act = self.getActionerFromLoadedOrTask( actioner_path)
        if act:
            for task in act.getCurrentManager().task_list:
                if task.checkType("WriteBranch"):
                    out.append(task.getName())
        return gr.CheckboxGroup(label="Write Branch Tasks",choices=out,value=out), gr.Button(value="Clear Branch Tasks",interactive=True)

    def clearRecordBranchTasks( self, act_path : str, names : list[str]):
        act = self.getActionerFromLoadedOrTask( act_path)
        if act:
            for name in names:
                task = act.getCurrentManager().getTaskByName( name)
                if task:
                    task.clearRecordParam()
        return gr.CheckboxGroup(label="None", choices=[],value=None), gr.Button(value="None", interactive=False)

    
    def goToNextBranch(self):
        self.actioner.getCurrentManager().goToNextBranch()
        return self.updateMainUIelements()
    
    def goToPrevBranch(self):
        self.actioner.getCurrentManager().goToNextBranch(revert=True)
        return self.updateMainUIelements()

    
    def goToBranchFork(self):
        man = self.actioner.getCurrentManager()
        _, trg = man.getBranchUpFork(start_task=man.getCurrentTask())
        man.curr_task = trg
        return self.updateMainUIelements()
    
    def goToCurrTaskBud(self):
        man = self.actioner.getCurrentManager()
        man.setCurrentTask(man.goToTaskBud(man.getCurrentTask()))
        return self.updateMainUIelements()

    
    def createNewTree(self):
        self.makeTaskAction("","SetOptions","New","user",{})
        self.actioner.getCurrentManager().updateTreeArr()
        return self.updateTreeAndAll()
    
    def goToNextTree(self):
        # print('Go to next tree')
        # if self.actioner.getCurrentManager() != self.actioner.std_manager:
        #     self.actioner.getCurrentManager().sortTreeOrder(check_list=True)
        # else:
        #     self.actioner.getCurrentManager().sortTreeOrder(True)
        self.actioner.getCurrentManager().goToNextTree()
        return self.updateTreeAndAll()
    
    def goBackByLink(self):
        man = self.actioner.getCurrentManager()
        man.goBackByLink()
        # return self.updateMainUIelements()
        return self.updateTreeAndAll()
    
    def goToNextChild(self):
        self.actioner.getCurrentManager().goToNextChild()
        return self.updateMainUIelements()
        # return self.makeTaskAction("","","GoToNextChild","")

    def goToParent(self):
        self.actioner.getCurrentManager().goToParent()
        return self.updateMainUIelements()
        # return self.makeTaskAction("","","GoToParent","")

    def goToHalfBranch(self):
        cur = self.actioner.getCurrentManager().curr_task
        tasks = cur.getAllParents()
        idx = int(len(tasks)/2)
        self.actioner.getCurrentManager().curr_task = tasks[idx]
        return self.updateMainUIelements()
    
    def moveToNextChild(self):
        self.actioner.getCurrentManager().goToNextChild()
        return self.updateMainUIelements()
    
    def moveToParent(self):
        # self.actioner.getCurrentManager().curr_task.resetQueue()
        self.actioner.getCurrentManager().goToParent()
        return self.updateMainUIelements()
    
    def moveToNextBranch(self):
        man = self.actioner.getCurrentManager()
        man.goToNextBranch()
        if man.curr_task.parent != None:
            trg = man.curr_task.parent
            man.curr_task = trg
        return self.updateMainUIelements()

    def switchRole(self, role, prompt):
        task = self.actioner.getCurrentManager().curr_task
        print('Set role[', role, ']for',task.getName())
        self.makeTaskAction(task.getLastMsgContent(), "Request", "Edit", role)
        return self.updateUIelements(prompt=prompt)
  
 
    def appendNewParamToTask(self, param_name):
        self.makeTaskAction('','','AppendNewParam','', {'name':param_name})
        return self.updateMainUIelements()
    
    
    def removeParamFromTask(self, param_name):
        self.makeTaskAction('','','RemoveTaskParam','', {'name':param_name})
        return self.updateMainUIelements()
    
    def setTaskKeyValue(self, param_name, key, mnl_value):
        if mnl_value.isdigit():
            if mnl_value.rfind('.') == -1:
                mnl_value = int(mnl_value)
            else:
                mnl_value = float(mnl_value)
        if key == 'path_to_trgs':
            val_arr = mnl_value.split(';')
            mnl_value = val_arr
        if mnl_value == 'False':
            mnl_value = False
        elif mnl_value == 'True':
            mnl_value = True
        # print('Set task key value:','|'.join([param_name,key,str(mnl_value)]))
        self.makeTaskAction('','','SetParamValue','', {'name':param_name,'key':key,'manual':mnl_value})
        return self.updateMainUIelements()
    
    def setSelectOptionToValue(self, name, key, option):
        if isinstance(option, bool):
            return option, ""
        return option, option
    
    def addTaskNewKeyValue(self, param_name, key, value):
        # print('Set task key value:','|'.join([param_name,key,str(value)]))
        self.makeTaskAction('','','SetParamValue','', {'name':param_name,'key':key,'select':value,'manual':''})
        return self.updateTaskManagerUI()
    
    def getMainCommandList(self):
        return self.manager.getMainCommandList()

    def getSecdCommandList(self):
        return self.manager.getSecdCommandList()
    

    def newExtProject(self, filename, prompt):
        self.makeTaskAction(prompt,"New","NewExtProject","")
        return self.updateTaskManagerUI()

    def appendExtProject(self, filename, prompt):
        self.makeTaskAction(prompt,"SubTask","SubExtProject","")
        return self.updateTaskManagerUI()
    
    def getPrivMangerDefaultInfo(self, mannametype, custommanname, exttaskstype, copytaskstype):
        man = self.actioner.getCurrentManager()
        param_json = {'actions':[],'repeat':3,'task_names':[t.getName() for t in man.multiselect_tasks]}
        if mannametype == 'Current':
            param_json['name'] = man.curr_task.getName()
        elif mannametype == 'Selected':
            param_json['name'] = man.getSelectedTask().getName()
        elif mannametype == '1st MultiS' and len(man.getMultiSelectedTasks()):
            param_json['name'] = man.getMultiSelectedTasks()[0].getName()
        elif mannametype == 'Custom':
            param_json['name'] = custommanname
        
        if exttaskstype == 'Current':
            param_json['task_names'] = [man.curr_task.getName()]
        elif exttaskstype == 'Selected':
            param_json['task_names'] = [man.getSelectedTask().getName()]
        elif exttaskstype == 'Multis':
            param_json['task_names'] = [t.getName() for t in man.getMultiSelectedTasks()]

        if copytaskstype == 'None':
            pass
        elif copytaskstype == 'Multis':
            param_json['move_tasks'] = [t.getName() for t in man.getMultiSelectedTasks()]
        
        if len(param_json['task_names']) > 0:
            return param_json, gr.Button(interactive=True)
        else:
            return {}, gr.Button(interactive=False)

    def initPrivManagerByInfo(self, params):
        print ('Init tmp manager by info')
        copytasks = []
        act = self.actioner
        man = act.getCurrentManager()
        if man != act.std_manager:
            print ('Can init only from Base')
            return self.updateTaskManagerUI()
        if 'move_tasks'  in params:
            copytasks = [man.getTaskByName(name) for name in params['move_tasks']]
            del params['move_tasks']
        self.makeTaskAction("","","InitPrivManager","", params)
        man.clearMultiSelectedTasksList()
        if len(copytasks) and man != act.getCurrentManager():
            act.std_manager.clearMultiSelectedTasksList()
            act.moveTaskFromManagerToAnother(tasks=copytasks, 
                                                        cur_man=act.std_manager,
                                                        next_man=act.getCurrentManager()
                                                        )

        return self.updateTaskManagerUI()

    def initPrivManager(self):
        print("Init empty private manager")
        man = self.actioner.getCurrentManager()
        tags = []
        for task in man.multiselect_tasks:
            code = task.getName()
            tags.append(code)
        if len(tags) == 0:
            print('No multiselected task for manager')
            return self.updateTaskManagerUI()
        self.makeTaskAction("","","InitPrivManager","", {'actions':[],'repeat':3, 'task_names':tags})
        return self.updateTaskManagerUI()
    
    def loadTmpManager(self, name):
        self.actioner.selectManagerByName(name)
        return self.updateTaskManagerUI()
    
   
    def getActionerSources(self):
        trgs = [t.getPath() for t in self.getActionersList()]
        out, out_paths = self.actioner.getCurManInExtTreeTasks()
        trgs.extend(out)
        return (
                gr.Dropdown(choices=trgs, 
    value=self.actioner.getPath() if self.actioner != None else None, interactive=True),
                gr.CheckboxGroup(choices=trgs, value=None)

        )
    
    def getActionerPathsList(self):
        output_choices = []
        output_value = None
        for act in self.getActionersList():
            path = act.getPath()
            name = FileManager.getFileName( path )
            value = [
                f"{name} : ({path})",
                path
            ]
            output_choices.append(value)
            if act == self.actioner:
                output_value = value
        return gr.Radio(choices=output_choices, 
    value=output_value, interactive=True)

    # TODO: сделать запоминание команд, чтобы перемещаться между акционерами?
    # Запускать отклонять update
    # Перемещение между задачами

    def selectActionerFromTask( self ):
        task = self.actioner.getCurrentManager().getCurrentTask()
        if task != None:
            res, path_to_act, task_name = task.getExternalActionerTask()
            if res:
                for act in self.getActionersList():
                    if path_to_act == act.getPath():
                        trg = act.getCurrentManager().getTaskByName( task_name )
                        if trg != None:
                            self.actioner = act
                            act.getCurrentManager().setCurrentTask( trg )
                            return self.updateTreeAndAll()
        return self.updateTreeAndAll()
    
    def getRelatedActionersToCurrent( self ):
        current_path = self.actioner.getPath()
        paths = []
        
        for act in self.getActionersList():
            for task in act.getCurrentManager().getTasks():
                res, path_to_act, task_name = task.getExternalActionerTask()
                if res and path_to_act == current_path and act.getPath() not in paths:
                    paths.append(act.getPath())
        return paths
    
    def getControledActionersByCurrent( self ):
        paths = []
        act = self.actioner
        for task in act.getCurrentManager().getTasks():
                res, path_to_act, task_name = task.getExternalActionerTask()
                if res and path_to_act not in paths:
                    paths.append(path_to_act)
        return paths
        
    
    def selectActionerByPath(self, path):
        if isinstance(path, str):
            for act in self.actioners_list:
                if act['act'].getPath() == path:
                    self.actioner = act['act']
        return self.updateTreeAndAll()
    
    def getModificationTimeOfSession(self, name : str ):
        path = FileManager.addFolderToPath(self.getPathToSession(),[name + ".json"])
        session_data = Reader.ReadFileMan.readJson(path)
        return "" if "modified" not in session_data else session_data["modified"]

    def readSessionInfo( self, name : str ):
        path = FileManager.addFolderToPath(self.getPathToSession(),[name + ".json"])
        session_data = Reader.ReadFileMan.readJson(path)
        text = ""
        if 'modified' in session_data:
            text += "Last modification: " + session_data["modified"] + "\n"
        if 'actioners' in session_data:
            text +='\n\n'.join( [str(idx) + ") " + info['act_path'] for idx, info in enumerate(session_data['actioners'] ) ] )
        return text

  


    def addCurrentExtTreeTaskActioner(self):
        man = self.actioner.getCurrentManager()
        task = man.curr_task
        self.addExtTreeTaskActioner(task)
        return self.updateTaskManagerUI()
    
    def loadInstructionDicitionaryByBrowsing(self):
        path = Loader.Loader.getFilePathFromSystem()
        print('Load manager by path',path)
        if 'instructions' in self.params:
            if path not in self.params['instructions']:
                self.params['instructions'].append(path)
        else:
            self.params['instructions'] = [path]
        self.saveSession()

    def getGroupsForInstructions(self):
        out = []
        if 'instructions' in self.params:
            for path in self.params['instructions']:
                insructions = Reader.ReadFileMan.readJson(Loader.Loader.getUniPath(path))
                try:
                    for group in insructions['instructions']:
                        out.append(group['group'])
                except:
                    pass
        return gr.Dropdown(choices=out, value=None)

    def getProposalsFromInstructions(self, group_name):
        text_info = 'Examples from task\n'
        examples = self.getProposalsFromTask()
        if 'instructions' in self.params:
            for path in self.params['instructions']:
                insructions = Reader.ReadFileMan.readJson(Loader.Loader.getUniPath(path))
                try:
                    for group in insructions['instructions']:
                        if group['group'] == group_name:
                            examples.extend([ (v,v) for  v in group['collection']])
                            text_info += group['description'] + '\n'
                            break
                except:
                    pass
        return gr.CheckboxGroup(choices=examples, info=text_info, value=None)

    def loadActionerByBrowsing(self):
        path = Loader.Loader.getDirPathFromSystem()
        print(f"Load manager by path\'{path}\'")
        if path == "[[manager:path:sub_0]]/.":
            print("Abort.")
            return self.updateTaskManagerUI()
        man_path = Loader.Loader.getUniPath(path)
        for act in self.getActionersList():
            if man_path == act.getPath():
                print(f"Found actioner ({man_path})")
                return self.updateTaskManagerUI()
        self.loadActionerByPath(man_path)
        return self.updateTaskManagerUI()
    
    def loadActionerFromExtTreeTask( self ):
        act_paths = []
        loaded_act_paths = [a.getPath() for a in self.getActionersList()]
        for act in self.getActionersList():
            paths = act.getLoadedActionerPath([])

            for path in paths:
                print(f"Check {path}")
                if path not in loaded_act_paths:
                    act_paths.append( path )
        print(f"Need to load actioners:\n{act_paths}")
        for path in act_paths:
            self.loadActionerByPath( path )
        return self.updateTaskManagerUI()
    
    def loadActionerWithTemplate(self, template_path : str, projectfile_path : str, save_path : str):
        # Archivator.extractFiles(templates_path, template_name, save_path)
        Archivator.extract7zFileToFolder( template_path, save_path)
        actioner = self.createActioner({'exttreetask_path':save_path,'load':True,'available_actioners':self.getActionersList})
        self.addActionerTolist(actioner)
        man = self.actioner.getCurrentManager()
        if len(man.getTasks()) == 0:
            self.createNewTree()

        projectfile = Reader.ReadFileMan.readJson(projectfile_path)
        target_tag = "targets"
        packdata_tag = "function_info"
        command_json = [
            {"action":"getTaskByTag","kwargs":{"tags":"insert,autogenerate"}},
            {"action":"insertingAction","kwargs":{"prompt":"[[TEXT]]"}}
            ]
        command_str = json.dumps(command_json)
        if isinstance(projectfile, dict) and target_tag in projectfile and isinstance(projectfile[target_tag], list):
            for pack in projectfile[target_tag]:
                packdata = pack.get(packdata_tag, "")
                pack_cmd = command_str.replace("[[TEXT]]", json.dumps(packdata)[1:-1])
                print(pack_cmd)
                actioner.getJsonCmd(pack_cmd)
        else:
            print(f"Error reading project file: {projectfile_path}")
        return self.updateTaskManagerUI()


    def loadActionerByPath(self, man_path : str):
        actioner = self.createActioner({'exttreetask_path':man_path,'load':True,'available_actioners':self.getActionersList})
        self.addActionerTolist(actioner)
        man = self.actioner.std_manager
        if len(man.task_list) == 0:
            self.createNewTree()
        print('Load manager from browser is complete')
        # python_path = Finder.findByKey("[[project:RunScript:python]]", man, man.curr_task, man.helper)
        # fld = Finder.findByKey("[[manager:path:fld]]", man, man.curr_task, man.helper)
        # spc = Finder.findByKey("[[manager:path:spc]]", man, man.curr_task, man.helper)
        # print("Vars for manager")
        # print(f"Python path: { Loader.Loader.getUniPath( python_path )}")
        # print(f"Manager folder: {Loader.Loader.getUniPath( fld )}")
        # print(f"Manager space: { Loader.Loader.getUniPath( spc )}")
   


    def switchToExtTaskManager(self):
        print('Switch to ext task manager')
        man = self.actioner.getCurrentManager()
        task = man.curr_task
        return self.switchToTargetInExtTreeTask(task)
    
    def switchToTargetInExtTreeTask(self, task : BaseTask):
        task_actioner = task.getActioner()
        if task_actioner != None and self.tmp_actioner == None:
            self.tmp_actioner_task = task
            self.tmp_actioner = self.actioner
            self.actioner = task_actioner
            self.actioner.loadStdManagerTasks()
            print('Switch on actioner of', task.getName())
            print('Path:', self.actioner.getPath())
            print('Man:', self.actioner.getCurrentManager().getName())
            # print('Tasks:',[t.getName() for t in self.actioner.getCurrentManager().task_list])
        return self.updateTaskManagerUI()
    
    def loadAllExtTreeTask(self):
        actioners = self.getActionersList()
        self.actioner.autoUpdateExtTreeTaskActs(actioners)
                
    
    def backToDefaultActioner(self):
        if self.tmp_actioner != None:
            self.actioner = self.tmp_actioner
            self.tmp_actioner = None
            self.tmp_actioner_task = None
        return self.updateTaskManagerUI()
    
    def activateExtTask(self):
        self.switchToExtTaskManager()
        return self.backToDefaultActioner()
 
    
    def initSavdManagerToCur(self,name):
        self.makeTaskAction("","","InitSavdManagerToCur","", {'task': name})
        return self.getUItmpmanagers()
 
    
    def loadPrivManager(self, name):
        self.makeTaskAction("","","InitSavdManager","", {'task': name})
        return self.getUItmpmanagers()
    
    def savePrivManToTask(self):
        self.makeTaskAction("","","SavePrivManToTask","")
        return self.getUItmpmanagers()
   
    def stopPrivManager(self):
        self.makeTaskAction("","","StopPrivManager","")
        self.actioner.getCurrentManager().fixTasks()
        return self.updateTaskManagerUI()
  
    def rmvePrivManager(self):
        self.makeTaskAction("","","RmvePrivManager","")
        self.actioner.getCurrentManager().fixTasks()
        return self.updateTaskManagerUI()
    
    def getPrivManager(self):
        return self.getUItmpmanagers()

    def exeActions(self):
        # Закомментированной командой производится запись команды в список команд менеджера
        # self.makeTaskAction("","","ExecuteManager","")
        # Для исполнения команд нужна отдельная команда, чтобы не переводить это все в цикл
        self.actioner.exeActions()
        # Альтернатива
        # self.makeTaskAction("","","ExecuteManager","",{},save_action=False)
        return self.updateTaskManagerUI()
    
    def exeSmplScript(self):
        self.actioner.exeCurManagerSmpl()
        return self.getUItmpmanagers()

    def editParamPrivManager(self, param):
        self.makeTaskAction("","","EditPrivManager","",param)
        return self.getUItmpmanagers()
    
    def changeVizType(self, action, vizualisation):
        out = gr.Code(value='', language=None)
        if action == 'Edit':
            out = gr.Code(value=self.actioner.getCurrentManager().getCurTaskLstMsgRaw(), language=None)
            if vizualisation != 'None':
                out =  gr.Code(value=self.actioner.getCurrentManager().getCurTaskLstMsgRaw(),language=vizualisation)
        return out

    def onExamplesClick(self, text, prompt):
        # print('Click', text)

        return prompt + "\n\n[[---]]\n\n".join(text)
    
    def getProposalsFromTask(self):
        examples = []
        trg = self.actioner.getCurrentManager().getCurrentTask()
        eres, eparam = trg.getParamStruct("choices", only_current=True)
        if not eres:
            return examples
        
        split_type = eparam.get("split_type","")
        sort_key = eparam.get("sortby","idx")
        if split_type == "key_comma":
            tasks = trg.getAllParents()
            pairs = []
            keys = []
            for task in tasks:
                split_words = task.findKeyParam(eparam['source'])
                jres, infos = Loader.Loader.loadJsonFromText( split_words )
                if jres:
                    pairs.extend( infos )
                if 'keys' in eparam:
                    inkeys = eparam['keys'].split(',')
                    for key in inkeys:
                        if key not in keys:
                            keys.append( key)

            try:
                sorted_pairs = sorted(pairs, key=lambda x: int(x[sort_key]))
            except:
                sorted_pairs = pairs
            if len(keys) == 0:
                keys = ['txt']
            for idx_pair, pair in enumerate(sorted_pairs):
                content = ""
                for key in keys:
                    if key in pair:
                        if isinstance(pair[key], str):
                            content += " " + pair[key]
                        else:
                            content += " " + str(pair[key])
                example_idx = idx_pair if sort_key not in pair else pair[sort_key]
                examples.append((f"{example_idx}. \"{content}\"", content))
        elif split_type == "smpl_comma":
            data = trg.findKeyParam(eparam["source"])
            keys =  data.split(",")
            for idx_key, key in enumerate(keys):
                content = key
                examples.append((f"{idx_key}. \"{content}\"", content))
        elif split_type == "key_dict_list":
            data = trg.findKeyParam(eparam["source"])
            inkeys = eparam.get("keys","")
            keys = [trg.findKeyParam(k) for k in inkeys.split(",")]
            jres, infos = Loader.Loader.loadJsonFromText( data )
            if jres and len(keys) and isinstance( infos, list ):
                try:
                    sorted_pairs = sorted(infos, key=lambda x: int(x[sort_key]))
                except:
                    sorted_pairs = pairs
                for idx_info, info in enumerate(infos):
                    content = ""
                    for key in keys:
                        if key in info:
                            if isinstance(pair[key], str):
                               content += " " + pair[key]
                            else:
                               content += " " + Loader.Loader.convJsonToText(info[key])
                example_idx = idx_info if sort_key not in info else info[sort_key]
                examples.append((f"{example_idx}. \"{content}\"", content))
        return examples

    def actionTypeChanging(self, action, prompt):
        # print('Action switch to=', action)
        # highlighttext = []
        task = self.actioner.getCurrentManager().getCurrentTask()
        examples = self.getProposalsFromTask()
        if action == 'New':
            return [prompt, 
                    gr.Button(value='Request'), 
                    gr.Button(value='Response', interactive=False), 
                    gr.Button(value='Custom',interactive=True), 
                    gr.Radio(interactive=False),
                    gr.CheckboxGroup(choices=[]),
                    gr.CheckboxGroup(choices=examples)
            ]
        elif action == 'SubTask' or action == 'Insert':
            return [prompt, 
                    gr.Button(value='Request'), 
                    gr.Button(value='Response', interactive=True), 
                    gr.Button(value='Custom',interactive=True), 
                    gr.Radio(interactive=False),
                    gr.CheckboxGroup(choices=[]),
                    gr.CheckboxGroup(choices=examples)
            ]
        elif action == 'Edit' or action == 'EditCopy' or action.startswith('EdCp'):
            # print('Get text from',task.getName(),'(',self.actioner.getCurrentManager().getName(),')')
            _,role,_ = task.getMsgInfo()
            # out = gr.Code(value=self.actioner.getCurrentManager().getCurTaskLstMsgRaw(), language=None)
            out = gr.Textbox(value=self.actioner.getCurrentManager().getCurTaskLstMsgRaw())
            # if vizualisation != 'None':
                # out =  gr.Code(value=self.actioner.getCurrentManager().getCurTaskLstMsgRaw(),language=vizualisation)
            return [out, 
                    gr.Button(value='Apply'), 
                    gr.Button(value='Divide',interactive=True), 
                    gr.Button(value='',interactive=False), 
                    gr.Radio(interactive=True,value=role),
                    gr.CheckboxGroup(choices=self.getParamListForEdit(), interactive=True),
                    gr.CheckboxGroup(choices=examples)
            ]
        
    def getTextInfo(self, notgood, bad):
        param = {'notgood': notgood, 'bad':bad}
        pairs, log, vector = self.actioner.getCurrentManager().curr_task.getTextInfo(param)
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.plot(vector, label='Prob')
        ax.plot([0,len(vector)], [notgood, notgood], label='notgood',color = 'yellow')
        ax.plot([0,len(vector)], [bad, bad], label='bad',color = 'red')

        plt.xlabel('Index of token')
        plt.ylabel('Probability')
        plt.title('Comparison of Vectors')
        plt.legend()
        return pairs, log, fig
    
    def getWordTokenPairs(self):
        man = self.actioner.getCurrentManager()
        pairs = man.curr_task.getWordTokenPairs()
        todraw = []
        for pair in pairs:
            todraw.append([pair['token'],'token'])
            todraw.append([ str(pair['bytes']) ,'bytes'])
        return todraw
    
    def getTasksWithActions(self):
        names = self.actioner.getTasksWithActions()
        return gr.CheckboxGroup(choices=names, value=names)
    
    def exeTasksByName(self, names):
        self.actioner.exeTasksByName(names)
        return self.updateMainUIelements()

    
    def getActionsInfoByTask(self):
        res, self.actions_info = self.actioner.getCurrentManager().getCurrentTask().getAutoCommand()
        self.actions_source = "Task"
        return self.getActionsList()

    def getActionsInfoByManager(self):
        self.actions_info = self.actioner.getCurrentManager().info['actions']
        self.actions_source = "Manager"
        return self.getActionsList()

    def getActionsList(self) -> list:
        actions = self.actions_info
        out = []
        for act in actions:
            name = ':'.join([str(act['id']),act['action'],act['type']])
            out.append(name)
        return gr.CheckboxGroup(choices=out, interactive=True,value=None)
    
    def getActionInfo(self, names : list):
        print('Get action info from', names)
        text = ''
        out = []
        for name in names:
            pack = name.split(':')
            actions = self.actions_info
            for idx, action in enumerate(actions):
                if pack[0] == str(actions[idx]['id']):
                    out.append(action)
        text = json.dumps(out, indent=1, ensure_ascii=False)
        return text
 
    def saveActionsToCurrTask(self, names: list):
        param = []
        for name in names:
            pack = name.split(':')
            actions = self.actions_info
            for idx, action in enumerate(actions):
                if pack[0] == str(actions[idx]['id']):
                    param.append(action)
                    break
        self.actioner.getCurrentManager().getCurrentTask().setAutoCommand("", param)
        self.getActionsInfoByTask()
        self.fixActionsIdx()
        return self.getActionsList()
    
    def moveActionUp(self, names: list):
        for name in names:
            pack = name.split(':')
            actions = self.actions_info
            print(pack)
            for idx, action in enumerate(actions):
                print(pack[0],'check',actions[idx]['id'])
                if pack[0] == str(actions[idx]['id']) and idx > 0:
                    actions.insert(idx - 1, actions.pop(idx))
        self.fixActionsIdx()
        return self.getActionsList()
    
    def fixActionsIdx(self):
        actions = self.actions_info
        actions = self.actioner.getCurrentManager().info['actions']
        for idx, action in enumerate(actions):
            actions[idx]['id'] = idx

    def delAction(self, names: list):
        for name in names:
            pack = name.split(':')
            actions = self.actions_info
            for idx, action in enumerate(actions):
                if pack[0] == str(actions[idx]['id']) and idx > 0:
                    actions.pop(idx)
                    break

        self.fixActionsIdx()
        return self.getActionsList()
    
    def clearAction(self):
        self.actions_info = []
        return self.getActionsList()
    
    def saveAction(self):
        if self.actions_source == "Manager":
            self.actioner.getCurrentManager().saveInfo()
        elif self.actions_source == "Task":
            self.actioner.getCurrentManager().getCurrentTask().setAutoCommand("", self.actions_info)
        return self.getActionsList()
    

    
    def setManagerStartTask(self, name: str):
        print('set Manager start task to',name)
        all_mans = [self.actioner.std_manager]
        all_mans.extend(self.actioner.tmp_managers)
        all_mans.remove(self.actioner.getCurrentManager())
        all_tasks = []
        for man in all_mans:
            all_tasks.extend([t.getName() for t in man.task_list])
        print('Available task:', all_tasks)
        if name in all_tasks:
            print('set name')
            self.actioner.getCurrentManager().info['task'] = name
        return self.getUItmpmanagers()
    
    def setCurrAsManagerStartTask(self):
        name = self.actioner.getCurrentManager().curr_task.getName()
        return self.setManagerStartTask(name)
    
    def backToStartTask(self):
        manager = self.actioner.getCurrentManager()
        task = manager.getTaskByName(manager.getName())
        manager.curr_task = task
        return self.updateMainUIelements()

    def setCurrentExtTaskOptions(self, names : list):
        self.makeTaskAction("","","SetCurrentExtTaskOptions","", {'names': names})
        return self.getUItmpmanagers()

    def resetAllExtTaskOptions(self):
        self.makeTaskAction("","","ResetAllExtTaskOptions","", {})
        return self.getUItmpmanagers()
    
    def getAvailableActionsList(self):
        return [t['action'] for t in self.actioner.getActionList()]
    
    def getAvailableActionTemplate(self, action_name : str):
        for action in self.actioner.getActionList():
            if action['action'] == action_name:
                return json.dumps(action['param'], indent=1)
        return '{\n}'
    
    def addActionToCurrentManager(self, action: str, param : str):
        self.actioner.getCurrentManager().addActions(action=action, param=json.loads(param))
        return self.getActionsList()

    def copyChainStepped(self):
        print('Copy chain stepped')
        # tasks_chains = self.actioner.getCurrentManager().curr_task.getTasksFullLinks({'in':True, 'out':True,'link':True})
        # self.actioner.getCurrentManager().copyTasksByInfo(tasks_chains=tasks_chains,edited_prompt='test', change_prompt=True, trg_type_t='', src_type_t='')
        self.actioner.getCurrentManager().copyTasksByInfoStep()
        return self.updateMainUIelements()

    def setTreeName(self, name : str):
        self.actioner.getCurrentManager().curr_task.setBranchSummary(name)
        return self.updateMainUIelements()

    def goToTreeByName(self, name):
        self.actioner.goToTreeByName(name)
        return self.updateTreeAndAll()

    def resetUpdate(self):
        self.actioner.resetUpdate()
        return self.updateMainUIelements()
       
    def update(self):
        dt1 = time.time()       
        self.actioner.update()
        chain = self.actioner.getProcessedChain()
        dt2 = time.time() 
        delta = dt2 - dt1
        print(f"Update {chain[0]}->{chain[1]} duration: {delta:.6f} s. Next: {chain[2]}")
        return self.updateMainUIelements() + (chain[0], chain[1], chain[2])
    
    def updateActionersIds( self ):
        for actioner in self.getActionersList():
            actioner.getCurrentManager().setUpdateSessionId(Ids.generateKey())
        
    def updateAll(self, check = False, max_idx = 10000):
        print('Update All trees stepped')
        self.actioner.getCurrentManager().disableOutput2()
        self.updateActionersIds()
        self.actioner.updateAll(force_check=check, max_update_idx=max_idx)
        self.actioner.getCurrentManager().enableOutput2()
        return self.updateMainUIelements()
    
    def updateAllnTimes(self, n, check = False):
        print('Update All trees stepped',n,'times')
        self.updateActionersIds()
        dt1 = time.time()       
        self.actioner.updateAllnTimes(n, check)
        dt2 = time.time() 
        delta = dt2 - dt1
        print(f"Update duration: {delta:.6f} s. ")
        return self.updateMainUIelements()
    
    def onMsgDiffCallback(self, info):
        print('Msg diff callback:\n', info)
        self.actioner.force_update_stop = True
        self.actioner.stopUpdate()

    def updateAllnTimesCheckDiff(self, n, check = False):
        print(f"Update All trees stepped{n}times while check diffs")
        for task in self.actioner.getCurrentManager().getTasks():
            task.registerOnMsgDiffCallback( self.onMsgDiffCallback )
        self.actioner.updateAllnTimes(n, check)

        for task in self.actioner.getCurrentManager().getTasks():
            task.unRegisterOnMsgDiffCallback( self.onMsgDiffCallback)
        self.actioner.force_update_stop = False
        return self.updateMainUIelements()

   
    def updateCurrentTree(self):
        self.actioner.getCurrentManager().disableOutput2()
        self.actioner.updateCurrentTree()
        self.actioner.getCurrentManager().enableOutput2()
        return self.updateMainUIelements()

   
    def updateAllUntillCurrTask(self, force_check = False, update_id = False):
        self.actioner.getCurrentManager().disableOutput2()
        if update_id:
            self.updateActionersIds()
        self.actioner.updateAllUntillCurrTask(force_check=force_check)
        self.actioner.getCurrentManager().enableOutput2()
        return self.updateMainUIelements()
    
    def updateChildTasks(self, force_check = False):
        self.actioner.updateChildTasks(force_check)
        return self.updateMainUIelements()
        
    def updateMultiSelectedTasks(self, force_check = False):
        man = self.actioner.getCurrentManager()
        act = self.actioner
        start_task = man.curr_task
        if force_check:
            targets = [t for t in man.multiselect_tasks if t in man.task_list]
        else:
            targets = man.multiselect_tasks
        start_task.resetTreeQueue()
        idx = 0
        act.update_state = 'step'
        act.setStartParamsForUpdate(man, start_task)
        while(idx < 1000):
            if act.update_state == 'done' or act.update_state == 'next tree' or man.curr_task not in targets:
                break
            act.update()
            idx += 1
        print('Frozen tasks cnt:', man.getFrozenTasksCount())
        man.curr_task = start_task
        return self.updateMainUIelements()
    
    def updateFromFork(self, force_check = False):
        self.actioner.updateFromFork(force_check)
        return self.updateMainUIelements()
        
 
   
    def setBranchEndName(self, summary):
        self.actioner.getCurrentManager().setBranchEndName(summary)
        return self.updateMainUIelements()

    
    def setCurrTaskByBranchEndName(self, name):
        self.actioner.setCurrTaskByBranchEndName( name)
        return self.updateMainUIelements()
    
    def cleanCurrTask(self):
        man = self.actioner.getCurrentManager()
        man.curr_task.forceCleanChat()
        return self.updateMainUIelements()


    def relinkToCurrTaskByName(self, name):
        return self.makeTaskAction('','','RelinkToCurrTask','', {'name':name})
    
    def selectRelatedChain(self):
        man = self.actioner.getCurrentManager()
        taskchainnames = man.getRelatedTaskChains(man.curr_task.getName(), man.getPath())
        for name in taskchainnames:
            man.addTaskToMultiSelected(man.getTaskByName(name))
        # return self.actioner.getRelationTasksChain()
        return self.updateMainUIelements()
    
    def selectNearestTasks(self):
        man = self.actioner.getCurrentManager()
        tasks = man.curr_task.getHoldGarlands()
        tasks.extend(man.curr_task.getGarlandPart())
        for task in tasks:
                man.addTaskToMultiSelected(task)
        return self.updateMainUIelements()
    
    def selectGarlandHolders(self):
        man = self.actioner.getCurrentManager()
        tree = man.getCurrentTask().getTree()
        multi = []
        for task in tree:
            holders = task.getGarlandPart()
            for holder in holders:
                new_tasks = holder.getAllParents(2)
                multi.extend(new_tasks)
        for task in multi:
            man.addTaskToMultiSelected(task)
        return self.updateMainUIelements()
    
    def multiselectFrozenTasks(self):
        man = self.actioner.getCurrentManager()
        for task in man.getTasks():
            if task.isFrozen() and not task.block_on:
                man.addTaskToMultiSelected(task)
        return self.updateMainUIelements()
    
    def multiselectMsgDiffTasks( self ):
        man = self.actioner.getCurrentManager()
        for task in man.getTasks():
            if not task.checkParentMsgList( update=False ):
                man.addTaskToMultiSelected(task)
        return self.updateMainUIelements()

    def applyAutoCommandsToMulti(self):
        self.actioner.createTmpManagerForCommandExe()
        return self.updateTaskManagerUI()

    def saveManagerActionToCurrentTask(self, type_name):
        self.actioner.saveActionsToCurrTaskAutoCommand(type_name=type_name)
        return self.updateTaskManagerUI()

       
    
    def deselectRealtedChain(self):
        self.actioner.getCurrentManager().multiselect_tasks = []
        return self.updateMainUIelements()
    
    def appendTaskToChain(self):
        man = self.actioner.getCurrentManager()
        man.addTaskToMultiSelected(man.curr_task)
        return self.updateMainUIelements()
    
    def selectMultiByType(self, typename):
        man = self.actioner.getCurrentManager()
        for task in man.getTasks():
            if task.checkType(typename):
                man.addTaskToMultiSelected(task)
        return self.updateMainUIelements()
  
    def removeTaskFromChain(self):
        man = self.actioner.getCurrentManager()
        if man.curr_task in man.multiselect_tasks:
            man.multiselect_tasks.remove(man.curr_task)
        return self.updateMainUIelements()
    
    def appendTreeToChain(self):
        man = self.actioner.getCurrentManager()
        tasks = man.curr_task.getTree()
        for task in tasks:
                man.addTaskToMultiSelected(task)
        return self.updateMainUIelements()
    
    def removeTreeFromChain(self):
        man = self.actioner.getCurrentManager()
        tasks = man.curr_task.getTree()
        for task in tasks:
            if task in man.multiselect_tasks:
                man.multiselect_tasks.remove(task)
        return self.updateMainUIelements()
   
    def appendBranchPartToChain(self):
        man = self.actioner.getCurrentManager()
        tasks = man.curr_task.getAllChildChains()
        for task in tasks:
                man.addTaskToMultiSelected(task)
        tasks = man.curr_task.getAllParents()
        while(len(tasks)):
            task = tasks.pop(-1)
            if len(task.getChilds()) > 1 or task.isRootParent():
                return self.updateMainUIelements()
            man.addTaskToMultiSelected(task)
        return self.updateMainUIelements()

    def removeBranchPartFromChain(self):
        man = self.actioner.getCurrentManager()
        tasks = man.curr_task.getAllChildChains()
        for task in tasks:
            if task in man.multiselect_tasks:
                man.multiselect_tasks.remove(task)
        tasks = man.curr_task.getAllParents()
        while(len(tasks)):
            task = tasks.pop(-1)
            if len(task.getChilds()) > 1 or task.isRootParent():
                return self.updateMainUIelements()
            if task in man.multiselect_tasks:
                man.multiselect_tasks.remove(task)
        return self.updateMainUIelements()


    def appendBranchtoChain(self):
        man = self.actioner.getCurrentManager()
        buds = man.curr_task.getAllBuds()
        bud = buds.pop()
        tasks = bud.getAllParents()
        for task in tasks:
                man.addTaskToMultiSelected(task)
        return self.updateMainUIelements()
 
    def removeBranchFromChain(self):
        man = self.actioner.getCurrentManager()
        buds = man.curr_task.getAllBuds()
        bud = buds.pop()
        tasks = bud.getAllParents()
        for task in tasks:
            if task in man.multiselect_tasks:
                man.multiselect_tasks.remove(task)
        return self.updateMainUIelements()
   
    def appendChildsToChain(self):
        man = self.actioner.getCurrentManager()
        tasks = man.curr_task.getAllChildChains()
        for task in tasks:
                man.addTaskToMultiSelected(task)
        return self.updateMainUIelements()
 
    def removeChildsFromChain(self):
        man = self.actioner.getCurrentManager()
        tasks = man.curr_task.getAllChildChains()
        for task in tasks:
            if task in man.multiselect_tasks:
                man.multiselect_tasks.remove(task)
        return self.updateMainUIelements()
    
    def removeParentsFromChain(self):
        man = self.actioner.getCurrentManager()
        tasks = man.curr_task.getAllParents()
        tasks.remove(man.curr_task)
        for task in tasks:
            if task in man.multiselect_tasks:
                man.multiselect_tasks.remove(task)
        return self.updateMainUIelements()

    def selectRowTasks(self):
        man = self.actioner.getCurrentManager()
        trg, child_idx = man.curr_task.getClosestBranching()
        tasks = trg.getChildSameRange(trg_idx=child_idx)
        for task in tasks:
            if task in man.task_list:
                man.addTaskToMultiSelected(task)
        return self.updateMainUIelements()
    
    def selectCopyBranch(self):
        man = self.actioner.getCurrentManager()
        tasks = man.getCopyBranch(man.curr_task)
        for task in tasks:
            if task in man.task_list:
                man.addTaskToMultiSelected(task)
        return self.updateMainUIelements()

    def selectCopyTasks(self):
        man = self.actioner.getCurrentManager()
        tasks = man.getCopyTasks(man.curr_task)
        for task in tasks:
            if task in man.task_list:
                man.addTaskToMultiSelected(task)
        return self.updateMainUIelements()
   
    def selectTaskRowFromCurrent(self, child_idx):
        man = self.actioner.getCurrentManager()
        tasks = man.curr_task.getChildSameRange(trg_idx=child_idx)
        for task in tasks:
                man.addTaskToMultiSelected(task)
        return self.updateMainUIelements()


    def getParamFromMultiSelected(self, key, info = ""):
        man = self.actioner.getCurrentManager()
        param = None
        difftasknames = []
        for task in man.multiselect_tasks:
            res, t_param = task.getParamStruct(param_name=key, only_current=True)
            if param == None:
                param = t_param
            else:
                if res and t_param == param:
                    pass
                else:
                    print('Param', task.getName(),'is diff')
                    difftasknames.append(task.getName())
        if param == None:
            return '','No param'
        
        output_info = 'Diff tasks:\n' + ','.join(difftasknames) + '\n' + info
        
        return json.dumps(param, indent=1), output_info
    
    def getValueFromJSONMultiSelect(self, param, key):
        if key in param:
            return param[key]
        return ''
    
    def setValueToMultiSelect(self, param, key, value):
        man = self.actioner.getCurrentManager()
        start = man.curr_task
        for task in man.multiselect_tasks:
            man.curr_task = task
            self.setTaskKeyValue(param_name=param, key=key, slt_value='', mnl_value=value)
        man.curr_task = start

    def setParamStructToMultiSelect(self, text_param, param_name):
        print('Set param struct to multiselect')
        task_names = []
        try:
            man = self.actioner.getCurrentManager()
            param = json.loads(text_param)
            if param_name == param['type']:
                for task in man.multiselect_tasks:
                    res = task.rewriteParamStruct( param )
                    if res:
                        task_names.append(task.getName())
            else:
                return self.getParamFromMultiSelected(param_name, info="Apply to " + ",".join(task_names))
        except Exception as e:
            print('Json error', e)
        return self.getParamFromMultiSelected(param_name, info="Apply to " + ",".join(task_names))

    def createGarlandFromMultiSelect(self):
        man = self.actioner.getCurrentManager()
        start = man.curr_task
        trg = start
        minichains = man.getMiniChainsFromMultiSelected()
        for mini in minichains:
            trg = start
            for task in mini:
                man.addTaskToSelectList(task)
                man.curr_task = trg
                self.createGarlandOnSelectedTasks('Insert')
                trg = start

        # for task in man.multiselect_tasks:
        #     man.addTaskToSelectList(task)
        #     man.curr_task = trg
        #     self.createGarlandOnSelectedTasks('Insert')
        #     trg = man.curr_task
        man.curr_task = start
        return self.updateMainUIelements()

    def createCollectFromMultiSelect(self):
        man = self.actioner.getCurrentManager()
        start = man.curr_task
        trg = start
        for task in man.multiselect_tasks:
            man.addTaskToSelectList(task)
            man.curr_task = trg
            self.createShootTreeOnSelectedTasks('SubTask')
            # self.createCollectTreeOnSelectedTasks('SubTask')
            trg = man.curr_task
        man.curr_task = start
        return self.updateMainUIelements()
    
    def runExeAutoCommandForMultiSelect(self, text : str):
        act = self.actioner
        man = act.getCurrentManager()
        for task in man.getMultiSelectedTasks():
            man.setCurrentTask(task)
            actions = json.loads(task.findKeyParam(text), strict=False)
            if isinstance(actions, list):
                for action in actions:
                    act.makeSavedAction(action)
        return self.updateMainUIelements()


    def shiftParentTagForMultiSelect(self, shift : int):
        man = self.actioner.getCurrentManager()
        start = man.curr_task
        for task in man.multiselect_tasks:
            if task.checkType('Request'):
                content = task.getLastMsgContentRaw()
                _,role,_ = task.getMsgInfo()
                edit = Finder.shiftParentTags(content,shift)
                man.curr_task = task
                self.makeTaskAction(prompt=edit,type1='Request',creation_type= 'Edit',creation_tag= role, param=[])
        man.curr_task = start
        print(f"Shift parent tag for {len(man.multiselect_tasks)} multiselected task(s)")
        return self.updateMainUIelements()

    def shiftParentTagForCurAndChilds(self, shift : int):
        man = self.actioner.getCurrentManager()
        start = man.curr_task
        tasks = man.curr_task.getAllChildChains()
        for task in tasks:
            if task.checkType('Request'):
                content = task.getLastMsgContentRaw()
                _,role,_ = task.getMsgInfo()
                edit = Finder.shiftParentTags(content,shift)
                # print('Start',content)
                # print('Edir', edit)
                man.curr_task = task
                self.makeTaskAction(prompt=edit,type1='Request',creation_type= 'Edit',creation_tag= role, param=[])
        man.curr_task = start
        print(f"Shift parent tag for {start.getName()} and its {len(tasks)} child(s)")
        return self.updateMainUIelements()

    def replaceTextForMultiSelect(self, old : str, rpc : str):
        man = self.actioner.getCurrentManager()
        start = man.curr_task
        for task in man.multiselect_tasks:
            if task.checkType('Request'):
                content = task.getLastMsgContentRaw()
                edit = content.replace(old=old, new=rpc)
                _,role,_ = task.getMsgInfo()
                man.curr_task = task
                self.makeTaskAction(prompt=edit,type1='Request',creation_type= 'Edit',creation_tag= role, param=[])
        man.curr_task = start
        print(f"Replace [{old}] to [{rpc}] for {len(man.multiselect_tasks)} multiselected task(s)")
        return self.updateMainUIelements()

    def findSubStringInTasks(self, trg : str):
        man = self.actioner.getCurrentManager()
        output = ''
        for task in man.task_list:
            if task.checkType('Request'):
                content = task.getLastMsgContentRaw()
                for idx in range(len(content)):
                    if content.startswith(trg, idx):
                        info = ':'.join([task.getName(), str(idx)]) + '\n\n'
                        start_idx = max(0, idx - 20)
                        end_idx = min((len(content) - 1), idx + len(trg) + 20)
                        info += content[start_idx : end_idx] + '\n\n\n\n'
                        output += info
        return output


    def removeMultiSelect(self):
        return self.makeTaskAction("","","RemoveTaskList","")


    # def getTaskKeyValue(self, param_name, param_key):
        # return self.getTaskKeyValue(param_name, param_key)
    
    def setTaskKeyValueUI(self, choices, value, interactive, multiselect, text, text_interactive):
        # print(f"Print {choices} - {value}")
        return (
            gr.Dropdown(choices=choices, value=value, interactive=interactive, multiselect=multiselect),
            gr.Textbox(text, interactive=text_interactive)
        )
    def getTaskKeyValue(self, param_name, param_key):
        choices, value, interactive, multiselect, text, text_interactive = self.actioner.getTaskKeyValueInternal(param_name, param_key)
        return self.setTaskKeyValueUI(choices, value, interactive, multiselect, text, text_interactive)
    
    def getAppendableParam(self):
        return self.actioner.getCurrentManager().getAppendableParam()
    
    def saveActPack(self, name):
        actor = self.actioner
        if actor.std_manager == actor.manager or 'actions' not in actor.manager.info:
            return
        if name == '':
            return
        path = os.path.join('actpacks',name + '.json')
        with open(path, 'w') as f:
            text = actor.manager.info['actions']
            print('ActPack:', text)
            json.dump(text, f, indent=1)
        return self.getActPacks()

        
    def getActPacks(self):
        return gr.Dropdown(choices=self.getActPacksList())
    
    def getActPacksList(self) -> list:
        mypath = 'actpacks'
        onlyfiles = [f.split('.')[0] for f in listdir(mypath) if isfile(join(mypath, f))]
        return onlyfiles

    
    def loadActPack(self, name):
        actor = self.actioner
        if actor.std_manager == actor.manager or 'actions' not in actor.manager.info:
            return
        if name == '':
            return
        mypath = 'actpacks'
        onlyfiles = [f.split('.')[0] for f in listdir(mypath) if isfile(join(mypath, f))]
        if name in onlyfiles:
            path = os.path.join(mypath,name + '.json')
            with open(path, 'r') as f:
                actor.manager.info['actions'] = json.load(f)
        return self.getActionsList()
    
    def cleanLastMessage(self):
        self.actioner.cleanLastMessageCurrentTask()
        return self.updateMainUIelements()
    
    def cleanLastMessageForMulti(self):
        self.actioner.cleanLastMessageForMulti()
        return self.updateMainUIelements()

    def getCurrentTaskBranchCodeTag(self):
        man = self.actioner.getCurrentManager()
        code = man.curr_task.getBranchCodeTag()
        out = []
        out.append(code)
        allchaintasknames = man.getTaskFileNamesByBranchCode(code, man.curr_task.getName())
        print(allchaintasknames)
        out.append(str(allchaintasknames))
        pyperclip.copy('\n'.join(out))
        pyperclip.paste()

   
   

    def moveBranchIdxUp(self):
        man = self.actioner.getCurrentManager()
        task = man.curr_task
        if task.getParent() == None:
            return self.updateMainUIelements()
        if len(task.getParent().getChilds()) < 2:
            return self.updateMainUIelements()
        idx = task.getPrio()
        if idx == 0:
            j = 1
            for child in task.getParent().getChilds():
                if task != child:
                    child.setPrio(j)
                    j += 1
        else:
            for child in task.getParent().getChilds():
                if child.getPrio() == idx - 1:
                    child.setPrio(idx)
            task.setPrio(idx -1)
        return self.updateMainUIelements()
    
    def moveBranchIdxDw(self):
        man = self.actioner.getCurrentManager()
        task = man.curr_task
        if task.getParent() == None:
            return self.updateMainUIelements()
        if len(task.getParent().getChilds()) < 2:
            return self.updateMainUIelements()
        idx = task.getPrio()
        length = len(task.getParent().getChilds())

        if idx < length - 1:
            task.getParent().getChilds()[idx + 1].setPrio(idx)
            task.setPrio(idx + 1)
        return self.updateMainUIelements()
    
    def moveUpTree(self):
        man = self.actioner.getCurrentManager()
        task = man.curr_task
        task.incTreeIdx()
        return self.updateMainUIelements()
 
    def moveDwTree(self):
        man = self.actioner.getCurrentManager()
        task = man.curr_task
        task.decTreeIdx()
        return self.updateMainUIelements()

 
    def addCurrTaskToSelectList(self):
        return self.actioner.getCurrentManager().addCurrTaskToSelectList()

    def getRelationBack(self, range):
        man = self.actioner.getCurrentManager()
        # taskchainnames = man.getRelatedTaskChains(man.curr_task.getName(), man.getPath(), max_idx=range)
        # for name in taskchainnames:
            # man.addTaskToMultiSelected(man.getTaskByName(name))
        man.getBackwardRelatedTaskChain(man.curr_task, range)
        return self.updateMainUIelements()

    def getRalationForward(self, range):
        man = self.actioner.getCurrentManager()
        man.getForwardRelatedTaskChain(man.curr_task, range)
        return self.updateMainUIelements()
    
    def setCurrentTaskByName(self, name):
        self.actioner.getCurrentManager().setCurrentTaskByName(name)
        return self.updateTreeAndAll()
    

    def setCurManagerColor(self, color):
        print('Set color', color,'to',self.actioner.getCurrentManager().getName())
        self.actioner.getCurrentManager().info['color'] = color
        self.actioner.getCurrentManager().saveInfo()

    def setCurManagerName(self, name):
        self.actioner.getCurrentManager().setName(name)
        self.actioner.getCurrentManager().saveInfo()
        return self.updateTaskManagerUI()
    
    def getCurManagerGlobalKeys(self):
        out = self.actioner.getCurrentManager().getGlobalKeys()
        return gr.Dropdown(choices=out), gr.Dropdown(choices=self.actioner.getCurrentManager().getManagerParameters())
    
    def getManagerParameter (self, key : str):
        return self.actioner.getCurrentManager().getManagerParameterValue ( key )
    
    def setManagerParameter( self, key : str, value : str):
        self.actioner.getCurrentManager().appendManagerParemeter( key, value )
        self.actioner.getCurrentManager().saveInfo()
        return self.getCurManagerGlobalKeys()
    
    def deleteManagerParameter (self, key : str):
        self.actioner.getCurrentManager().deleteManagerParemeter( key )
        self.actioner.getCurrentManager().saveInfo()
        return self.getCurManagerGlobalKeys()

    
    def geCurManagerGlobalValue(self, key):
        res, out = self.actioner.getCurrentManager().getGlobalValue(key)
        return out, f"[[manager:global:{key}]]"
    
    def setCurManagerGlobalValue(self, key, value):
        self.actioner.getCurrentManager().appendGlobalVariables(key, value)
        self.actioner.getCurrentManager().saveInfo()
        return self.getCurManagerGlobalKeys()
    
    def delCurManagerGlobalKey(self, key):
        self.actioner.getCurrentManager().deleteGlobalVariable( key )
        self.actioner.getCurrentManager().saveInfo()
        return self.getCurManagerGlobalKeys()
    
    def addMultiSelectTasksFromStdMan(self):
        if self.actioner.getCurrentManager() != self.actioner.std_manager:
            self.actioner.addExtTasksForManager(self.actioner.getCurrentManager(), self.actioner.std_manager.multiselect_tasks)
        return self.updateTaskManagerUI()

    def rmvMultiSelectTasksFromTmpMan(self):
        if self.actioner.getCurrentManager() != self.actioner.std_manager:
            self.actioner.rmvExtTasksForManager(self.actioner.getCurrentManager(), self.actioner.getCurrentManager().multiselect_tasks)
        return self.updateTaskManagerUI()

    def moveTaskToStdMan(self):
        print('Move TmpMan tasks to StdMan')
        if self.actioner.getCurrentManager() != self.actioner.std_manager:
            self.actioner.moveTaskFromTMPmanToSTDman(tasks= self.actioner.getCurrentManager().multiselect_tasks, 
                                                       cur_man= self.actioner.getCurrentManager(),
                                                       next_man= self.actioner.std_manager
                                                       )
        return self.updateTaskManagerUI()

    def moveTaskToTmpMan(self):
        if self.actioner.getCurrentManager() != self.actioner.std_manager:
            task_to_copy = self.actioner.std_manager.multiselect_tasks.copy()
            self.actioner.std_manager.multiselect_tasks = []
            self.actioner.moveTaskFromManagerToAnother(tasks=task_to_copy, 
                                                       cur_man=self.actioner.std_manager,
                                                       next_man=self.actioner.getCurrentManager()
                                                       )
        return self.updateTaskManagerUI()

    def moveTaskTmpToTmp(self, name):
        if self.actioner.getCurrentManager() == self.actioner.std_manager:
            return self.updateTaskManagerUI()
        if self.actioner.std_manager.getName() == name:
            return self.updateTaskManagerUI()
        else:
            start_man = self.actioner.getCurrentManager()
            trg_man = None
            for man in self.actioner.tmp_managers:
                if man.getName() == name:
                    trg_man = man
                    break
            if trg_man != None:
                task_trgs = start_man.multiselect_tasks.copy()
                self.moveTaskToStdMan()
                self.actioner.std_manager.multiselect_tasks = task_trgs
                start_man.multiselect_tasks = []
                self.actioner.setManager(trg_man)
                self.moveTaskToTmpMan()
                self.actioner.setManager(start_man)
        return self.updateTaskManagerUI()
    
    def loadMangerExtInfoExtWithBrowser(self):
        path = Loader.Loader.getDirPathFromSystem(self.actioner.getCurrentManager().getPath())
        return self.loadMangerExtInfoExt(path)
    
    def loadMangerExtInfoExtForCurTask(self):
        man = self.actioner.getCurrentManager()
        taskpath = FileManager.addFolderToPath(man.getPath(), ['tmp', man.curr_task.getName() ])
        path = Loader.Loader.checkManagerTag(taskpath, man.getPath(), False)
        return self.loadMangerExtInfoExt(path)
    
    def loadTmpManagerInfoForCopying(self):
        man = self.actioner.getCurrentManager()
        path = Loader.Loader.getDirPathFromSystem(man.getPath())
        manpath = Loader.Loader.getUniPath(Finder.findByKey(path, man, None, man.helper))
        buds_info, tasks_info, all_tasks = Searcher.ProjectSearcher.openProject(manpath)
        output = []
        for tname in tasks_info:
            output.append([tname,""])
        return (
            output,
            ','.join([t.getName() for t in man.task_list]),
            manpath
                )
    
    def copyExternalTmpManagerToCurrProject(self, change_table, path):
        man = self.actioner.getCurrentManager()
        start_files = FileManager.getFilesPathInFolder(Loader.Loader.getUniPath(man.getPath()))
        start_names = FileManager.getFilenamesFromFilepaths(start_files)
        FileManager.copyFiles(path, Loader.Loader.getUniPath(man.getPath()),exld_files=start_names)
        curr_files = FileManager.getFilesPathInFolder(Loader.Loader.getUniPath(man.getPath()))
        trg_files = [t for t in curr_files if t not in start_files]
        print(f"Copy external temporary manager {path} to current tmp man, ignore:\n{start_names}")
        for task_path in curr_files:
            task_info = Reader.ReadFileMan.readJson(task_path)
            if 'parent' in task_info:
                parentname = task_info['parent']
                for pair in change_table:
                    if parentname == pair[0]:
                        print(f"Change {pair[0]} to {pair[1]} for {task_path}")
                        task_info['parent'] = pair[1]
                        break
                Writer.writeJsonToFile(task_path, task_info)
        man.is_loaded = False
        man.loadTasksListFileBased(files=trg_files)

        print('Done')
        return self.updateMainUIelements()

    def loadMangerExtInfoExt(self, path):
        manpath = Finder.findByKey(path,self.actioner.getCurrentManager(), None, self.actioner.getCurrentManager().helper)
        buds_info, tasks_info, all_tasks = Searcher.ProjectSearcher.openProject(manpath)
        parents = self.actioner.getCurrentManager().curr_task.getAllParents()
        parnames = [t.getName() for t in parents]
        parnames.append('Self')
        self.exttreemanbudinfo = buds_info
        inexttreeparam = {'type':'external','project_path':path, 'dir':'In'}
        outexttreeparam = {'type':'external', 'dir':'Out'}
        return (json.dumps(inexttreeparam, indent=1),
                json.dumps(outexttreeparam, indent = 1), 
                gr.Radio(choices=[t['task'] for t in buds_info if 'task' in t], interactive=True),
                gr.Dropdown(choices=tasks_info, interactive=True),
                gr.Dropdown(choices=all_tasks, interactive=True),
                gr.Dropdown(choices=parnames, value='Self', interactive=True)
                )
    def getBudInfo(self, budname : str):
        for budinfo in self.exttreemanbudinfo:
            if budinfo['task'] == budname:
                return budinfo['summary'], budinfo['branch'], self.actioner.getCurrentManager().convertMsgsToChat(msgs=budinfo['message'])
        return '','',[]

    def saveCurrManInfo(self):
        self.actioner.getCurrentManager().saveInfo(True)

    def addInExtTreeInfo(self, start_inext, branch_type, exttask_name, copy_type, extreetaskname, task_name):
        extbrjson = json.loads(start_inext)
        # extbrjson['dir'] = branch_type
        extbrjson['retarget'] = {
            'std' : task_name,
            'chg' : exttask_name
        }
        extbrjson['copy'] = copy_type
        extbrjson['name'] = extreetaskname
        return json.dumps(extbrjson, indent=1)
    
    def setCurTaskToOutExtTree(self, start_inext):
        man = self.actioner.getCurrentManager()
        if self.tmp_actioner_task.checkType('InExtTree'):
            act = self.tmp_actioner_task.getActioner()
            task = act.getCurrentManager().curr_task
            return self.addOutExtTreeInfo(start_inext, task.getName())
        return self.addOutExtTreeInfo(start_inext, '')
    
    def addOutExtTreeInfo(self, start_inext,  task_name):
        extbrjson = start_inext
        extbrjson['target'] = task_name
        return json.dumps(extbrjson, indent=1)
    
    def addInExtTreeSubTask(self, params):
        man = self.actioner.getCurrentManager()
        man.createOrAddTask('','InExtTree','user',man.curr_task, [json.loads(params)])
        return self.updateMainUIelements()
    
    def createJSONparamOutExtTree(self, exttask_intype, actioner_path):
        trg_act = self.actioner
        trg_man = trg_act.std_manager
        src_act = self.getActionerByPath(actioner_path)
        if src_act == None:
            return {}
        src_man = src_act.std_manager
        standart_taskname = ""
        actioner_path = Loader.Loader.getManRePath(actioner_path, trg_man.getPath())
        inexttreeparam = {
            'type':'external',
            'dir':'Out',
            'target': '',
            'name':'',
            'exttreetask_path':actioner_path,
            'inexttree':'fromact'
            }    
        try:
            if exttask_intype == 'Selected':
                standart_taskname = src_man.getSelectedTask().getName()
            elif exttask_intype == 'Current':
                standart_taskname = src_man.getCurrentTask().getName()
            elif exttask_intype == 'Multi':
                out = []
                for task in src_man.getMultiSelectedTasks():
                    inexttreeparam['target'] = task.getName()
                    out.append(copy.deepcopy(inexttreeparam))
                return out
        except Exception as e:
            print('On get task error:', e)
        inexttreeparam['target'] = standart_taskname
        return [inexttreeparam]
    
    def createJSONparamInExtTree(self, exttask_intype, exttask_outtype, actioner_path):
        trg_act = self.actioner
        trg_man = trg_act.std_manager
        src_act = self.getActionerByPath(actioner_path)
        src_man = src_act.std_manager
        if src_act == None:
            return {}
        standart_taskname = ""
        out_tasks = []
        actioner_path = Loader.Loader.getManRePath(actioner_path, trg_man.getPath())
        try:
            if exttask_intype == 'Selected':
                standart_taskname = src_man.getSelectedTask().getName()
            elif exttask_intype == 'Current':
                standart_taskname = src_man.getCurrentTask().getName()
            elif exttask_intype == 'Default':
                standart_taskname = src_man.getTaskByTag("external, input, default").getName()

            if exttask_outtype == 'Current Bud(s)':
                buds = src_man.getCurrentTask().getAllChildChains()
                out_tasks = [b.getName() for b in buds if b.getChilds() == 0]
            elif exttask_outtype == 'Selected':
                out_tasks = [src_man.getSelectedTask().getName()]
            elif exttask_outtype == 'Multi':
                out_tasks = [m.getName() for m in src_man.getMultiSelectedTasks()]
            elif exttask_intype == 'Default':
                out_tasks = [src_man.getTaskByTag("external, output, default").getName()]
        except Exception as e:
            print('On get task error:', e)
        inexttreeparam = {
            'type':'external',
            'dir':'In',
            'jumper': standart_taskname,
            'name':'',
            'exttreetask_path':actioner_path,
            'out_task_targets': out_tasks,
            'inexttree':'fromact',
            'update_count': 1
            }    
        update_commands_task = src_man.getTaskByTag("external, updt_actions, default")
        idle_commands_task = src_man.getTaskByTag("external, idle_actions, default")
        if update_commands_task:
            inexttreeparam['updt_actions'] = update_commands_task.getLastMsgContentRaw()
        if idle_commands_task:
            inexttreeparam['idle_actions'] = idle_commands_task.getLastMsgContentRaw()
        return inexttreeparam
    
    def createInExtTreeTaskByParam(self, param):
        man = self.actioner.getCurrentManager()
        trgpar = man.getCurrentTask()
        inxttreetask = man.createOrAddTaskByInfo('JumperTree', TaskDescription(prompt='', 
                                                                              prompt_tag='user',
                                                                              parent=trgpar, 
                                                                              params=[param]))
        for outtaskname in param['out_task_targets']:
            man.setCurrentTask(inxttreetask)
            outexttreeparam = {
                'type':'external', 
                'dir':'Out',
                'target': outtaskname
                }
            outexttreetask = man.createOrAddTaskByInfo('OutExtTree', 
                TaskDescription(prompt='', prompt_tag='user',parent=inxttreetask, params=[outexttreeparam]))
        return self.updateMainUIelements()
    
    def createOutExtTreeTaskByParam(self, parameters):
        man = self.actioner.getCurrentManager()
        for param in parameters:
            outexttreetask = man.createOrAddTaskByInfo('OutExtTree', 
                TaskDescription(prompt='', prompt_tag='user',parent=None, params=[param]))
        return self.updateMainUIelements()
    
    def createOutExtTreeTask(self, trgtask_name, task_name):
        man = self.actioner.getCurrentManager()

        param = {
                'type':'external', 
                'dir':'Out',
                'target': task_name
                }
        man = self.actioner.getCurrentManager()
        outexttreetask = man.createOrAddTaskByInfo('OutExtTree', 
                TaskDescription(prompt='', prompt_tag='user',parent=man.getTaskByName(trgtask_name), params=[param]))
        return self.updateMainUIelements()

    def convertTaskBranchInInOutExtPair(self):
        man = self.actioner.getCurrentManager()
        if len(man.multiselect_tasks) == 0:
            print('No tasks for convert')
            return
        root_task = None
        buds = []
        for task in man.multiselect_tasks:
            if task.getParent() == None or task.getParent() not in man.multiselect_tasks:
                if root_task == None:
                    root_task = task
                else:
                    print('More than one root in multiselect')
                    return
            if len(task.getChilds()) == 0:
                buds.append(task)
            elif len([t for t in task.getChilds() if t in man.multiselect_tasks]) == 0:
                buds.append(task)
        if not root_task and not root_task.getParent():
            print('No parent')
            return
        trgpar = root_task.getParent()
        inexttreeparam = {
            'type':'external',
            'dir':'In',
            'retarget':{
                'std': trgpar.getName(),
                'chg': trgpar.getName()
            },
            'name':''
            }
        print('Converted branch buds:',[t.getName() for t in buds])
        inxttreetask = man.createOrAddTaskByInfo('InExtTree', TaskDescription(prompt='', prompt_tag='user',parent=trgpar, params=[inexttreeparam]))
        if inxttreetask and len(buds) > 0:
            task_actioner = inxttreetask.getActioner()
            task_actioner.getCurrentManager().loadTasksListFileBased()
            task_actioner.getCurrentManager().copyTasksIntoManager(man.multiselect_tasks)
            for bud in buds: 
                outexttreeparam = {
                    'type':'external', 
                    'dir':'Out',
                    'target': bud.getName()
                    }
                outexttreetask = man.createOrAddTaskByInfo('OutExtTree', 
                    TaskDescription(prompt='', prompt_tag='user',parent=inxttreetask, params=[outexttreeparam]))
                for child in bud.getChilds():
                    if child not in man.multiselect_tasks:
                        outexttreetask.addChild(child)
            
        return self.updateMainUIelements()
    
    def addTaskBranchInExtTree(self):
        man = self.actioner.getCurrentManager()
        if len(man.multiselect_tasks) == 0:
            print('No tasks to add')
            return
        if not man.curr_task.checkType('InExtTree'):
            return
        root_task = None
        for task in man.multiselect_tasks:
            if task.getParent() == None or task.getParent() not in man.multiselect_tasks:
                if root_task == None:
                    root_task = task
                else:
                    print('More than one root in multiselect')
                    return
        
        inexttreetask = man.curr_task
        eres, eparam = inexttreetask.getParamStruct('external')
        if not eres:
            print('No param')
            return
        if eparam['retarget']['chg'] != root_task.getParent().getName():
            print('Root different')
            return
        task_actioner = inexttreetask.getActioner()
        task_actioner.getCurrentManager().loadTasksListFileBased()
        task_actioner.getCurrentManager().copyTasksIntoManager(man.multiselect_tasks)

        return self.updateMainUIelements()
        


    
    def addOutExtTreeSubTask(self, params):
        if self.tmp_actioner_task != None:
            man = self.tmp_actioner_task.getManager()
            if self.tmp_actioner_task.checkType('InExtTree'):
                man.createOrAddTask('','OutExtTree','user',man.curr_task, [params])
        # return self.updateMainUIelements()
    
    def getExtTreeParamsForEdit(self):
        man = self.actioner.getCurrentManager()
        # if man.curr_task.checkType('InExtTree'):
        # if self.tmp_actioner_task != None:
        if True:
            self.tmp_actioner_task = man.curr_task
            print(f"Get ExtTreeTask {self.tmp_actioner_task.getName()} params")
            if self.tmp_actioner_task.checkType('InExtTree'):
                eres, eparam = self.tmp_actioner_task.getParamStruct('external')
                if eres:
                    return (self.tmp_actioner_task.getName(),
                            'None',  
                            eparam, 
                            {'type':'external', 'dir':'Out'}, 
                            gr.Button(interactive=True), 
                            gr.Button(interactive=False))
            elif self.tmp_actioner_task.checkType('OutExtTree') and self.tmp_actioner_task.getParent() != None and self.tmp_actioner_task.getParent().checkType('InExtTree'):
                eres, eparam = self.tmp_actioner_task.getParamStruct('external')
                eres1, eparam1 = self.tmp_actioner_task.getParent().getParamStruct('external')
                if eres and eres1:
                    return (self.tmp_actioner_task.getParent().getName(), 
                            self.tmp_actioner_task.getName(), 
                            eparam1, 
                            eparam, 
                            gr.Button(interactive=False), 
                            gr.Button(interactive=True))

        return 'None','None', {}, {}, gr.Button(interactive=False), gr.Button(interactive=False)
    
    def checkTaskFiles(self):
        man = self.actioner.getCurrentManager()
        self.addExternalTasksToManager(man, man.getPath(), [t.getName() for t in man.multiselect_tasks])

    def addExternalTasksToManager(self, manager : Manager, path : str, tasknames : list[str]):
        budtasknames = tasknames.copy()
        alltaskpaths = []
        for name in tasknames:
            taskname = name + manager.getTaskExtention()
            task_path = Loader.Loader.getUniPath( FileManager.addFolderToPath(path,[taskname]))
            alltaskpaths.append(task_path)
            task_info = Reader.ReadFileMan.readJson(task_path)
            parent_name = task_info['parent']
            if parent_name in budtasknames:
                budtasknames.remove(parent_name)

        print(f"Try to load tasks: {tasknames}\nBuds:{budtasknames}")
        branches = []
        for budname in budtasknames:
            trgname = budname
            taskname = trgname + manager.getTaskExtention()
            task_path = Loader.Loader.getUniPath( FileManager.addFolderToPath(path,[taskname]))
            task_info = Reader.ReadFileMan.readJson(task_path)
            branchtasks = [{"name": budname,"path": task_path}]
            idx = 0
            while idx < 1000:
                taskname = trgname + manager.getTaskExtention()
                task_path = Loader.Loader.getUniPath( FileManager.addFolderToPath(path,[taskname]))
                task_info = Reader.ReadFileMan.readJson(task_path)
                parent_name = task_info['parent']
                if parent_name != '' and parent_name in tasknames:
                    tmp = branchtasks.copy()
                    branchtasks = [{"name":parent_name,"path":task_path}]
                    branchtasks.extend(tmp)
                    trgname = parent_name
                else:
                    break
            print("Branch:",[t["name"] for t in branchtasks])
            branches.append(branchtasks)
        print("\n\n\n\nBranches:", branches)

    def createExtTaskForManager(self, manager : Manager, taskbranchinfos):
        linklist = []
        parent = None
        for i, info in enumerate(taskbranchinfos):
            if i == 0:
                parent = None
            task_name = info["name"]
            task_path = info["path"]
            task_obj = manager.getTaskByName(task_name)
            if task_obj == None:
                task_info = Reader.ReadFileMan.readJson(task_path)
                prompt = ''
                role = 'user'
                task_type = FileManager.getFileName(task_path)
                if 'chat' in task_info and len(task_info['chat']) > 0:
                    prompt = task_info['chat'][-1]['content']
                    role = task_info['chat'][-1]['role']
                for link in task_info['linked']:
                    linklist.append({'in':FileManager.getFileName(task_path),'out':link})

                parent = manager.createOrAddTaskByInfo(task_type=task_type, 
                                    info=TaskDescription(prompt=prompt, prompt_tag=role, parent=parent,trgtaskname=task_name))
                parent.setCheckParentForce(True)
            
    def copyToClickBoardDial(self):
        msgs = self.actioner.getCurrentManager().curr_task.getMsgs()
        text = ""
        for msg in msgs:
            text += msg['role'] + '\n' + 10*'====' + '\n\n\n'
            text += msg['content'] + '\n'
        self.copyToClickBoard(text)
        return "[[parent:allmsgs]]", text
    
    def getCurrentTaskReport(self):
        path = Loader.Loader.getFilePathToSaveText(task.getName())
        task = self.actioner.getCurrentManager().getCurrentTask()
        report = {
            "StartTask": task.getName(),
            "time": getTimeForSaving(),
            "chats":[]
        }
        report = task.getTaskReport(report)
        report_txt = "# Intial Info\nTask: " + report["StartTask"] + "\ntime: " + report["time"] + "\n"
        for chat in report["chats"]:
            report_txt += "##" + chat.get("chain","") + "\n\n"
            for msg_pack in chat.get("chat",[]):
                report_txt += "### Role: " + msg_pack["role"] + "\n"
                report_txt += msg_pack["content"]
        Writer.writeToFile(path, report_txt)

    def copyToClickBoard(self, text):
        pyperclip.copy(text)
        pyperclip.paste()

    def copyToClickBoardParentContent(self):
        self.copyToClickBoard("[[parent:msg_content]]")
    def copyToClickBoardParentContentJSONtrg(self):
        self.copyToClickBoard("[[parent:msg_content:json:answer]]")
        return "[[parent:msg_content:json:answer]]", ""
    def copyToClickBoardParentCode(self):
        self.copyToClickBoard("[[parent:code]]")
        return "[[parent:code]]", ""
    
    def copyToClipDirPath(self):

        path = Loader.Loader.getDirPathByBrowsing()
        relpath = Loader.Loader.getManRePath(path, self.actioner.getCurrentManager().getPath())
        return Loader.Loader.getUniPath( path ), relpath

    def copyToClickBoardPaths(self):
        paths = Loader.Loader.getFilePathsByBrowsing()
        relpaths = Loader.Loader.convertFilePathsToRelative( paths, self.actioner.getCurrentManager().getPath())
        # relpaths = Loader.Loader.getFilePathArrayFromSysten(self.actioner.getCurrentManager().getPath())
        # self.copyToClickBoard(' '.join(relpaths))
        return " ".join([Loader.Loader.getUniPath(p) for p in paths]), " ".join(relpaths)

    def copyToClickBoardDialRaw(self):
        msgs = self.actioner.getCurrentManager().curr_task.getRawMsgs()
        text = ""
        for msg in msgs:
            text += msg['role'] + '\n' + 10*'====' + '\n\n\n'
            text += msg['content'] + '\n'
        self.copyToClickBoard(text)

    def copyToClickBoardReqListRaw(self):
        msgs = self.actioner.getCurrentManager().curr_task.getRawMsgs()
        text = ""
        for msg in msgs:
            if msg['role'] == 'user':
                # text += msg['role'] + '\n' + 10*'====' + '\n\n\n'
                text += msg['content'] + '\n'
        pyperclip.copy(text)
        pyperclip.paste()
   

    def copyToClickBoardLstMsg(self):
        coded =self.actioner.getCurrentManager().getCurTaskLstMsgRaw() 
        msg = self.actioner.getCurrentManager().getCurTaskLstMsg()
        pyperclip.copy(msg)
        pyperclip.paste()
        return coded, msg

    

    def copyToClickBoardTokens(self):
        tokens, price = self.actioner.getCurrentManager().curr_task.getCountPrice()
        text  = 'Tokens: ' + str(tokens) + ' price: ' + str(price)
        pyperclip.copy(text)
        pyperclip.paste()
    
    def setMultiselectedTasksChainToMainTrack(self):
        self.setMultiSelectTaskQueueCond('Disable')
        return self.updateUIelements()

    def resetMultiselectedTasksChainToMainTrack(self):
        self.setMultiSelectTaskQueueCond('None')
        return self.updateUIelements()
    
    def setMultiSelectTaskQueueCond(self, cond : str):
        act = self.actioner
        man = act.getCurrentManager()
        multis = man.getMultiSelectedTasks()
        for task in multis:
            childs = task.getChilds()
            for child in childs:
                if child not in multis:
                    cparam = child.getQueueParam()
                    if 'cond' in cparam:
                        cparam['cond'] = cond
                        child.setQueueParam(cparam)

    def copyMultiSelectedTasksChainsToSingleChain(self):
        print('Copy multiselected tasks into single chain')
        act = self.actioner
        man = act.getCurrentManager()
       
        minichains = man.getMiniChainsFromMultiSelected()

        for i, chain in enumerate(minichains):
            if i != 0:
                man.addCurrTaskToSelectList()
            man.clearMultiSelectedTasksList()
            for task in chain:
                man.addTaskToMultiSelected(task)
            man.curr_task = chain[0]
            # prompt = man.getCurTaskLstMsgRaw()
            role = man.getCurTaskRole()
            print('Selected task:', man.getSelectedTask().getName())
            print('Current task:', man.getCurrentTask().getName())
            self.makeRequestAction('','Edit',role,{'onlymulti','sel2par'})
        return self.updateUIelements()
    
    def checkTrashInManagerFolder(self):
        act = self.actioner
        man = act.getCurrentManager()
        names = [t.getName()+".json" for t in man.task_list]
        names.append("project.json")
        files = FileManager.getFilesInFolder(Loader.Loader.getUniPath(man.getPath()))
        trash = []
        for file in files:
            if file not in names:
                trash.append( Loader.Loader.getUniPath(FileManager.addFolderToPath(man.getPath(),[file])))
        print('Found trash:\n', '\n'.join(trash))
        for file in trash:
            FileManager.deleteFile(file)

    def loadAdditionalTasksInManager(self):
        act = self.actioner
        man = act.getCurrentManager()
        path = Loader.Loader.getDirPathFromSystem(self.actioner.getCurrentManager().getPath())
        manpath = Finder.findByKey(path,self.actioner.getCurrentManager(), None, self.actioner.getCurrentManager().helper)
        names = [t.getName()+".json" for t in man.task_list]
        names.append("project.json")
        files = FileManager.getFilesInFolder(Loader.Loader.getUniPath(manpath))
        filepaths = []
        for file in files:
            if file not in names:
                filepaths.append( Loader.Loader.getUniPath(FileManager.addFolderToPath(manpath,[file])))
        print('Found additional tasks:\n', '\n'.join(filepaths))
        man.is_loaded = False
        man.loadTasksListFileBased(filepaths)
        return act.updateUIelements()


    def getConvertTreeTo3PlainText(self, tree_type = 'Current'):
        act = self.actioner
        man = act.getCurrentManager()
        if tree_type == 'Current Task Tree':
            trgtasklist = man.curr_task.getAllChildsRecursive()
        elif tree_type == 'Tree':
            trgtasklist = man.curr_task.getAllParents()[0].getAllChildsRecursive()
        elif tree_type == 'MultiSelected':
            minichains = man.getMiniChainsFromMultiSelected()
            if len(minichains) == 0:
                return self.getTree3PlainText()
            trgtasklist = []
            for chain in minichains:
                rechild = chain[0].getAllChildsRecursive( check_tasks = False, trgs = man.multiselect_tasks)
                for t in rechild:
                    if t not in trgtasklist:
                        trgtasklist.append(t)
        else:
            return self.getTree3PlainText()

        tasks = [t for t in trgtasklist if not t.checkType('SetOptions')]
        self.tree3plaintext_tasks = tasks
        self.tree3plaintext_idx = 0
        return self.getTree3PlainText()
    
    def editPromptTree3PlainText(self, prompt):
        task = self.tree3plaintext_tasks[self.tree3plaintext_idx]
        role = task.getLastMsgRole()
        self.actioner.getCurrentManager().curr_task = task
        self.makeRequestAction(prompt,"Edit", role,[])
        return self.getTree3PlainText()
    
    def moveUpTree3PlainText(self):
        if self.tree3plaintext_idx > 0:
            self.tree3plaintext_idx += -1
        return self.getTree3PlainText()
    def moveDwTree3PlainText(self):
        if self.tree3plaintext_idx < len(self.tree3plaintext_tasks) - 1:
            self.tree3plaintext_idx += 1
        return self.getTree3PlainText()

    def getTree3PlainText(self):
        pretext = ""
        text = ""
        suftext = ""

        for i, task in enumerate(self.tree3plaintext_tasks):
            if i < self.tree3plaintext_idx:
                pretext += task.getLastMsgContentRaw() + '\n'
            elif i == self.tree3plaintext_idx:
                text += task.getLastMsgContentRaw() + '\n'
            elif i > self.tree3plaintext_idx:
                suftext += task.getLastMsgContentRaw() + '\n'
        return pretext, text, suftext

    def fixCurManQtasks(self):
        self.actioner.getCurrentManager().fixTasks()
        return self.updateMainUIelements() 
    
    def searchInExtTreeTasksUsage( self ):
        # man = self.actioner.getCurrentManager()
        trg_path = self.actioner.getPath()
        paths = []
        for act in self.getActionersList():
            task_names, out_paths = act.getCurManInExtTreeTasks()
            # paths.extend(out_paths)
            for idx, path in enumerate(out_paths):
                if trg_path in path:
                    if idx < len(task_names):
                        task_name = task_names[idx]
                        paths.append( f"{idx}.{act.getPath()}:{task_name}")
                    # return f"Found {act.getPath()}"
        
        text = f"Target:\n{trg_path}\n"
        text += "\n".join(paths)
        return text

    def getCurManInExtTreeTasks(self):
        man = self.actioner.getCurrentManager()
        out, out_paths = self.actioner.getCurManInExtTreeTasks()
        checks = []
        for name in out:
            task = man.getTaskByName(name)
            if task.getActioner() == None:
                checks.append( name )
        act_info_text = "Paths to actioners:\n"
        act_info_text += '\n'.join([ "* " + p for p in out_paths])
        act_paths = []
        act_info_text += "\n\nRelated:\n" + '\n'.join(["* " + p for p in self.actioner.getRelatedActionersPaths(act_paths)])
        return gr.CheckboxGroup(choices=out, value=checks, interactive=True), act_info_text
    
    def updateInExtTreeTasksByName(self, names : list[str]):
        self.actioner.loadExtTreeTaskActionersByTaskNames( names )
        return self.updateMainUIelements() 
    
    def copyManagerTaskFilesToAnotherFolder(self):
        man = self.actioner.getCurrentManager()
        
        trg_path = Loader.Loader.getDirPathFromSystem()
        print(f"Target path: {trg_path}")
        for task in man.task_list:
            print(f"Copy file by path {task.getJsonFilePath()}")
            FileManager.copyFile(Loader.Loader.getUniPath(task.getJsonFilePath()), Loader.Loader.getUniPath(trg_path))
        print('Copying done')

    def setHideTaskStatus(self, value):
        self.actioner.hide_task = value
        return self.updateMainUIelements() 
    
    def setShowWorkGraph(self, value):
        self.show_workgraph = value
        return self.updateMainUIelements() 


    def getByTaskNameParamList(self, task_name):
        man = self.actioner.getCurrentManager()
        task = man.getTaskByName(task_name)
        return gr.Dropdown(choices=man.getByTaskNameParamListInternal(task), interactive=True)

    def getTaskKeys(self, param_name):
        man = self.actioner.getCurrentManager()
        return self.getNamedTaskKeys(man.curr_task, param_name)

    def getByTaskNameTasksKeys(self, task_name, param_name):
        man = self.actioner.getCurrentManager()
        task = man.getTaskByName(task_name)
        return self.getNamedTaskKeys(task, param_name)

    def getNamedTaskKeys(self, task : BaseTask, param_name : str):
        res, data = task.getParamStruct(param_name)
        a = ['None']
        if res:
            task_man = TaskManager()
            def_vals =task_man.getListBasedOptionsDict(data) 
            if len(def_vals) == 0:
                def_vals = [k for k, v in data.items()]
            a.extend(def_vals)
        # print('Get named task keys', a)
        val = None
        return gr.Dropdown(choices=a, value=val, interactive=True)

    def getFinderKeyString(self,task_name, fk_type, param_name, key_name):
        value = Finder.getKey(task_name, fk_type, param_name, key_name, self)
        pyperclip.copy(value)
        pyperclip.paste()

    def getTextFromBuffer( self, text ):
        return text + "\n" + pyperclip.paste()

    def updateMainUIelements(self):
        return self.updateUIelements()

    def convToGradioUI(self, 
                        r_msgs, 
                        mancurtaskgetname, 
                        res_params, 
                        update_info,
                        set_prompt, 
                        mangettasklist,
                        mangetcurtaskparamlist, 
                        curtaskallpars,
                        gettreenameforradio_names,
                        gettreenameforradio_trg,
                        mancurtaskgetbranchsum,
                        mangetbranchend,
                        mangetbranchendname,
                        mangetbranchlist,
                        mangetbranchmessages,
                        status_msg,
                        status_color,
                        rawinfo_msgs,
                        manholdgarlands,
                        mangetname,
                        mangetcolor,
                        multitasks,
                        bud_msgs,
                        sel_task,
                        sel_cont
                       ):
        out =  (
            r_msgs, 
            # in_prompt ,
            # out_prompt, 
            # in_role, 
            # chck, 
            mancurtaskgetname, 
            res_params,
            update_info,
            set_prompt, 
            gr.Dropdown(choices= mangettasklist),
            gr.Dropdown(choices=mangetcurtaskparamlist, interactive=True), 
            gr.Dropdown(choices=curtaskallpars, 
                               value=mancurtaskgetname, 
                               interactive=True), 
            gr.Radio(value="SubTask"), 
            bud_msgs,
            # self.getCurrentExtTaskOptions(),
            # gr.Radio(choices=gettreenameforradio_names, interactive=True),
            gr.Textbox(value=mancurtaskgetbranchsum, interactive=True),
            gr.Radio(choices=mangetbranchend, value = None, interactive=True),
            mangetbranchendname,
            gr.CheckboxGroup(value=[]),
            mangetbranchlist,
            mangetbranchmessages,
            status_msg,
            status_color,
            rawinfo_msgs,
            gr.Radio(choices=manholdgarlands, interactive=True),
            mangetname,
            mangetcolor,
            multitasks,
            sel_task,
            sel_cont
            )
        return out
    

    def updateSecActUI(self, prompt = '' ):
        if self.sec_actioner == None:
            act = self.actioner
        else:
            act = self.sec_actioner
        [r_msgs, 
        mancurtaskgetname, 
        res_params, 
        set_prompt, 
        mangettasklist,
        mangetcurtaskparamlist, 
        curtaskallpars,
        gettreenameforradio_names,
        gettreenameforradio_trg,
        mancurtaskgetbranchsum,
        mangetbranchend,
        mangetbranchendname,
        mangetbranchlist,
        mangetbranchmessages,
        status_msg,
        rawinfo_msgs,
        manholdgarlands,
        mangetname,
        mangetcolor,
        multitasks, 
        bud_msgs] = act.getCurrTaskPrompts2(set_prompt=prompt, hide_tasks=act.hide_task)


        maingraph = act.drawGraph(hide_tasks=True, out_childtask_max=1)
        branchnames = act.getCurrentTaskBranchNames()
        saved_man, tmp_man, mangetname, name, tmpmannames = act.getTmpManagerInfo()
        acts_list = [a['act'].getPath() for a in self.actioners_list]
        cur_act = act.getPath() if self.sec_actioner != None else None
        out =  (
            r_msgs,
            maingraph, 
            gr.Radio(choices=acts_list, value=cur_act, interactive=True),
            gr.Radio(choices=tmp_man, value=mangetname, interactive=True),
            gr.Dropdown(choices=gettreenameforradio_names, interactive=True),
            gr.Dropdown(choices=mangetbranchend, interactive=True),
            gr.Dropdown(choices=branchnames, interactive=True)
            )
        return out
    
    def convertMsgsToChat(self, task : BaseTask, param = {}):
        hide_tasks = self.actioner.hide_task
        if "max_symbols" in param:
            msgs = task.getMsgs(hide_task=hide_tasks, max_symbols=param["max_symbols"], inparam=param)
        else:
            msgs = task.getMsgs(hide_task=hide_tasks, inparam=param)
        out = []
        for msg in msgs:
            pack = None
            if msg['role'] not in ['user','assistant']:
                msg['role'] = 'user'
            if 'attach' in msg and msg['attach']['category'] == 'image_url':
                image_url = Loader.Loader.getUniPath(msg['attach']['content'])
                pack = { "role": msg["role"], "content": gr.Image(value=image_url,label=msg['content']) }
                del msg['attach']
            out.append(msg)
            if pack:
                out.append(pack)
        return out


    def updateUIelements(self, prompt = ''):
        hide_tasks = False

        [r_msgs, 
        mancurtaskgetname, 
        res_params,
        update_info, 
        set_prompt, 
        mangettasklist,
        mangetcurtaskparamlist, 
        curtaskallpars,
        gettreenameforradio_names,
        gettreenameforradio_trg,
        mancurtaskgetbranchsum,
        mangetbranchend,
        mangetbranchendname,
        mangetbranchlist,
        mangetbranchmessages,
        status_msg,
        status_color,
        rawinfo_msgs,
        manholdgarlands,
        mangetname,
        mangetcolor,
        multitasks, 
        bud_msgs,
        sel_task,
        sel_cont
        ] = self.actioner.getCurrTaskPrompts2(set_prompt=prompt, hide_tasks=self.actioner.hide_task)

        maingraph = self.actioner.drawGraph(hide_tasks=True, out_childtask_max=1, hide_mono_childs=True)
        stepgraph = self.actioner.drawGraph(max_index = 3, path = "output/img2", hide_tasks=True, max_childs=-1,add_linked=True, out_childtask_max=4)
        rawgraph = self.actioner.drawGraph(hide_tasks=True, max_childs=1, path="output/img3", all_tree_task=True, add_garlands=True, out_childtask_max=4, hide_mono_childs=True)

        task = self.actioner.getCurrentManager().getCurrentTask()
        tres, tparam = task.getParamStruct('draw_wrk')
        task_param = tparam if tres else self.params['workgraph']
        workspace_msgs = self.convertMsgsToChat(task,{"attach":True,"max_symbols":10000,"max_per_task":task_param})
        step_params = {"attach":True}
        if self.params['stepgraph']['on']:
            step_params['max_per_task'] = self.params['stepgraph']

        stepiteration_msgs = self.convertMsgsToChat(self.actioner.getCurrentManager().getBranchEndTask(),step_params)


        out = self.convToGradioUI(
                workspace_msgs, 
                mancurtaskgetname, 
                res_params, 
                update_info,
                set_prompt, 
                mangettasklist,
                mangetcurtaskparamlist, 
                curtaskallpars,
                gettreenameforradio_names,
                gettreenameforradio_trg,
                mancurtaskgetbranchsum,
                mangetbranchend,
                mangetbranchendname,
                mangetbranchlist,
                mangetbranchmessages,
                status_msg,
                status_color,
                rawinfo_msgs,
                manholdgarlands,
                mangetname,
                mangetcolor,
                multitasks,
                stepiteration_msgs,
                sel_task,
                sel_cont
        )

        cmdinfo = "Commands:\n"
        cmds = self.actioner.getCurrentManager().getCommandList()
        cmdinfo += "\n".join(cmds)
        cmdinfo += f"\ncount: {len(cmds)}"

        nearest_exttreetask = self.actioner.getNearestExtTreeTask()
        nearest_exttreetask_name = "None" if nearest_exttreetask == None else nearest_exttreetask.getName()
        nearest_exttreetask_list = [] if nearest_exttreetask == None else self.actioner.getExtTreeCmdsListOfTask( nearest_exttreetask )

        out += (
            self.actioner.getCurrentManager().getTreesList(True), gr.Image(maingraph, visible=self.show_workgraph), 
                stepgraph, rawgraph, cmdinfo, 
                nearest_exttreetask_name,
                gr.CheckboxGroup(choices=nearest_exttreetask_list,value=[]),
                self.actioner.getPath(),
                gr.Radio(choices=self.getRelatedActionersToCurrent(), interactive=True,value = None),
                gr.Radio(choices=self.getControledActionersByCurrent(), interactive=True, value=None)
                )
        # print('act:',out)
        return out
        # else:
        #     hide_tasks = True
        #     maingraph = self.manager.drawGraph(hide_tasks=hide_tasks)
        #     stepgraph = self.manager.drawGraph(max_index= 1, path = "output/img2", hide_tasks=hide_tasks, max_childs=-1,add_linked=True)
        #     rawgraph = self.manager.drawGraph(hide_tasks=hide_tasks, max_childs=1, path="output/img3", all_tree_task=True)
        #     out = self.getCurrTaskPrompts2(set_prompt=prompt)
        #     if out == None:
        #         self.setManager(self.std_manager)
        #         out = self.getCurrTaskPrompts2(set_prompt=prompt)
        #     out += (self.manager.getTreesList(True), maingraph, stepgraph, rawgraph)
        #     return out

    def updateTreeAndAll(self):
        man = self.actioner.getCurrentManager()
        gettreenameforradio_names, gettreenameforradio_trg = man.getTreeNamesForRadio()
        out = self.updateUIelements()
        saved_man, tmp_man, mangetname, name, tmpmannames = self.actioner.getTmpManagerInfo()
        out += self.convTmpManagerInfo(saved_man, tmp_man, mangetname, name, tmpmannames)
        out += (gr.Radio(choices=gettreenameforradio_names, value=gettreenameforradio_trg),self.getUAT_Times())
        return out
     
    def updateTaskManagerUI(self):
        out = self.updateUIelements()
        saved_man, tmp_man, mangetname, name, tmpmannames = self.actioner.getTmpManagerInfo()
        out += self.convTmpManagerInfo(saved_man, tmp_man, mangetname, name, tmpmannames)
        return out
 
    def convTmpManagerInfo(self, saved_man, tmp_man, mangetname, name, tmpmannames):
        return (gr.Dropdown(choices= saved_man, value=None, interactive=True), 
                gr.Radio(choices= tmp_man, value=mangetname, interactive=True), 
                # json.dumps(param, indent=1), 
                gr.Text(value=name), 
                # self.manager.getCurrentExtTaskOptions(),
                gr.Dropdown(choices= tmpmannames, value=None, interactive=True),
                self.getCurrentSessionName(),
                self.getActionerPathsList()
                )

    def getUItmpmanagers(self):
        saved_man, tmp_man, mangetname, name, tmpmannames = self.actioner.getTmpManagerInfo()
        return self.convTmpManagerInfo(saved_man, tmp_man, mangetname, name, tmpmannames)
    
    def selectSecActionerByInfo(self, info):
        print(f"Select second actioner by {info}")
        for act in self.actioners_list:
            if act['act'].getPath() == info:
                print(f"Select actioner by path{act['act'].getPath()}")
                self.sec_actioner = act['act']
        return self.updateSecActUI()
    
    def selectSecActMan(self, name):
        self.sec_actioner.selectManagerByName(name)
        return self.updateSecActUI()
    
    def selectSecActTree(self, name):
        self.sec_actioner.goToTreeByName(name)
        return self.updateSecActUI()
    
    def selectSecActBud(self, name):
        self.sec_actioner.setCurrTaskByBranchEndName(name)
        return self.updateSecActUI()
    
    def selectSecActTask(self, name):
        self.sec_actioner.setCurManTaskByName(name)
        return self.updateSecActUI()


    def setTextWindowToCurrTask(self, minval,maxval):
        man = self.actioner.getCurrentManager()
        task = man.getCurrentTask()
        task.setParamStruct({
            "type":"attention",
            "start":minval,
            "end":maxval
        })

 
    def getTextWindowFromCurrTask(self):
        man = self.actioner.getCurrentManager()
        text = man.getCurrentTask().getLastMsgContent2()

        hres, hparam = man.getCurrentTask().getParamStruct('attention', only_current=True)
        min_smbls = 0
        max_smbls = len(text)
        text_len = len(text)
        if hres:
            if hparam['end'] == -1:
                max_smbls = len(text)
            else:
                max_smbls = min(len(text), hparam['end'])
            min_smbls = min(max_smbls, hparam['start'])
        wintext = max_smbls - min_smbls
        out_text = text[min_smbls:max_smbls]
        return [
            gr.Number(value=wintext,maximum=text_len, interactive=True),
            gr.Slider(value=min_smbls, minimum=0,maximum=text_len, interactive=True),
            gr.Slider(value=max_smbls, minimum=0,maximum=text_len, interactive=True),
            gr.Textbox(value=out_text)
        ]
    
    def moveTextWindowFromCurrTask( self, winsz, slider_str ):
        man = self.actioner.getCurrentManager()
        text = man.getCurrentTask().getLastMsgContent2()
        text_len = len(text)
        wintext = min(winsz, text_len)
        out_text = text[slider_str:slider_str + wintext]
        return (
            gr.Textbox(value=out_text)
        )
 
    def changeTextWindowFromCurrTask( self, minval, maxval ):
        man = self.actioner.getCurrentManager()
        text = man.getCurrentTask().getLastMsgContent2()
        text_len = len(text)
        text_end = min(text_len, maxval)
        text_start = min(minval, maxval)
        cut_top = max(text_start - 100, 0)
        cut_bottom = min( text_end + 100, text_len)
        out_text = "```\n" + text[cut_top:text_start] + "\n```\n" + text[text_start:text_end] + "\n```\n" + text[text_end:cut_bottom] + "\n```"
        return (
            out_text
        )

    def createMessageBasedOnRecords( self, chat, header : str , prefix : str, suffix : str, post : str):

        out = header

        for idx, msg in enumerate(chat):
            start = prefix
            start = start.replace("[[number]]", str(idx))
            out += start
            out += msg[1]
            out += suffix
        out += post

        return out
    
    def resetActUpdateCnt (self):
        self.actioner.updateallcounter = 0
        return self.updateUIelements()

    def copyMultiSelectToFolder(self):
        act = self.actioner
        man = act.getCurrentManager()
        selpath = Loader.Loader.getDirPathFromSystem()
        path = Loader.Loader.getUniPath(selpath)
        for task in man.getMultiSelectedTasks():
            task.saveAllParamsByPath(path)

        return "Done"
    
    def selectTargetActioner(self):
        self.trg_actioner = self.actioner

        return gr.Button(interactive=True),gr.Button(interactive=True), self.trg_actioner.getPath()

    def moveMultiSelectedTasksFromTargetActioner( self ):
        act = self.trg_actioner
        cur_man = act.getCurrentManager()
        next_man = self.actioner.getCurrentManager()
        tasks = act.getCurrentManager().getMultiSelectedTasks()
        for task in tasks:
                next_man.addTask(task)
                task.setManager(next_man)
                cur_man.rmvTask(task)
                task.saveAllParams()
        print('Move to ext actioner tasks:', [t.getName() for t in tasks])
        return gr.Button(interactive=False), gr.Button(interactive=False), ''
    
    def copyMultiSelectedTasksFromTargetActioner( self ):
        act = self.trg_actioner
        cur_man = act.getCurrentManager()
        next_man = self.actioner.getCurrentManager()
        tasks = act.getCurrentManager().getMultiSelectedTasks()
        for task in tasks:
                new_task = copy.deepcopy(task)
                next_man.addTask(new_task)
                new_task.setManager(next_man)
                new_task.saveAllParams()
                print(f"Copy {task.getName()} from {task.manager.getName()} to {new_task.manager.getName()}")
        # print('Move to ext actioner tasks:', [t.getName() for t in tasks])
        return gr.Button(interactive=False), gr.Button(interactive=False),''
   
    def copyExtTreeTaskContentWithSelected(self):
        print('Copy InExtTree Task(s): Selected -> Multi')
        man = self.actioner.getCurrentManager()
        src = man.getSelectedTask()
        if src.checkType('InExtTree'):
            src_path = src.getInExtTreeFolderPath()
            if src_path != "":      
                targets = man.getMultiSelectedTasks()
                for task in targets:
                    print('Try to copy', src.getName(),'to', task.getName())
                    if task.checkType('InExtTree'):
                        trg_path = task.getInExtTreeFolderPath()
                        if trg_path != "":
                            FileManager.copyFiles(src_folder=src_path, trg_folder=trg_path, exld_files=["project.json"])
                            task.reset()              
        return self.updateUIelements()
    
    def setPartialLinksParams(self, symbols_count, prefix_count, suffix_count):
        man = self.actioner.getCurrentManager()
        task = man.getCurrentTask()
        out_text = task.getForLinkedPrompt()

        targets = task.getHoldGarlands()

        text_part = TextTool.cut_text_into_parts(out_text, symbols_count, prefix_count, suffix_count)

        param = {'type':'partial', 'links':[]}

        for idx, target in enumerate(targets):
            if idx < len(text_part):
                param['links'].append({'name':target.getName(),
                'start':text_part[idx]['Start Index of Text'],
                'end': text_part[idx]['End Index of Text']})
            else:
                break
        task.setParamStruct(param)

        output = ""
        for idx, part in enumerate(text_part):
            output += "Part " + str(idx) + "\n\n"
            output += part['Result Text']
            output += "\n\n---\n\n"

        return output
    
    def getOutExtTreeLinkInfo( self ):
        man = self.actioner.getCurrentManager()
        infos = []
        for task in man.getTasks():
            eres, eparam = task.getParamStruct('external')
            if eres:
                if task.checkType("OutExtTree"):
                    curr_trg_name = eparam['target']
                    infos.append(f"{task.getName()} -> {curr_trg_name}")
        return "OutTreeTasks:\n" + "\n".join(infos)
   
    def getExtTreeParams(self):
        man = self.actioner.getCurrentManager()
        task = man.getCurrentTask()
        act : Actioner = task.getActioner()
        curr_trg_name = ""
        cur = ""
        sel = ""
        trg_names = []
        isjumpaer = False
        outexttree_task_names = []
        multitasks_names = ""
        if act != None:
            eres, eparam = task.getParamStruct('external')
            if eres:
                if task.checkType("JumperTree"):
                    curr_trg_name = eparam['jumper']
                    isjumpaer = True
                elif task.checkType("OutExtTree"):
                    curr_trg_name = eparam['target']
                
                for child in task.getChilds():
                    eres, eparam = child.getParamStruct("external", True)
                    if eres and "target" in eparam:
                        outexttree_task_names.append(eparam["target"])

                trg_names =[t.getName() for t in act.getCurrentManager().task_list]
                cur = act.getCurrentManager().getCurrentTask().getName()
                if act.getCurrentManager().getSelectedTask():
                    sel = act.getCurrentManager().getSelectedTask().getName()
                else:
                    sel = ""
            multitasks_names = ", ".join([t.getName() for t in act.getCurrentManager().getMultiSelectedTasks()])

        return (gr.Dropdown(value=curr_trg_name, choices=trg_names, interactive=True),
                cur, 
                sel, 
                man.getCurrentTask().getName(),
                gr.Button(interactive=isjumpaer),
                multitasks_names,
                ", ".join(outexttree_task_names)
                )
    
    def setExtTreeParams(self, target_name):
        man = self.actioner.getCurrentManager()
        task = man.getCurrentTask()
        act = task.getActioner()
        if act != None:
            eres, eparam = task.getParamStruct('external')
            if eres:
                if task.checkType("JumperTree"):
                    eparam['jumper'] = target_name
                elif task.checkType("OutExtTree"):
                    eparam['target'] = target_name
                task.setParamStruct(eparam)
                task.loadActionerTasks(self.getActionersList())
                task.saveAllParams()

    def getActionerFromLoadedOrTask(self, name)-> Actioner:
        src_act = self.getActionerByPath( name )
        if src_act == None:
            task = self.actioner.getCurrentManager().getTaskByName( name )
            if task != None:
                src_act = task.getActioner()
        return src_act


    def interCompareActioners(self, actioner_path, targets: list, gettype, checks):
        out = {"trees":[],"links": []}
        trg_man = self.getActionerByPath(actioner_path).getCurrentManager()
        if gettype == 'Current children':
            out["trees"].append( trg_man.getBranchInfo( trg_man.getCurrentTask(), checks ))
        elif gettype == 'Act diffs':
            src_act = self.getActionerFromLoadedOrTask(actioner_path)
            if src_act == None:
                return out
            src_man = src_act.getCurrentManager()

            trgtasknames = []
            for name in targets:
                trg_act = self.getActionerFromLoadedOrTask(name)
                if trg_act:
                    if len(trgtasknames) == 0:
                        trgtasknames = trg_act.getCurrentManager().getTaskNamesList()
                    else:
                        names = trg_act.getCurrentManager().getTaskNamesList()
                        for name in trgtasknames:
                            if name not in names:
                                trgtasknames.remove(name)
            diff_tasks = []
            srctasknames = src_man.getTaskNamesList()
            # trgtasknames = trg_man.getTaskNamesList()
            for name in srctasknames:
                if name not in trgtasknames:
                    diff_tasks.append(src_man.getTaskByName(name))
            rooottreetasks = src_man.getSeparateTreesFromTaskList(diff_tasks)
            for task in rooottreetasks:
                out["trees"].append( src_man.getBranchInfo( task, checks ))

            srclinks = src_man.getLinksList()
            trglinks = trg_man.getLinksList()
            for link in srclinks:
                if link not in trglinks:
                    out["links"].append(link)

        return out
    
    def copyTasksFromActionerToActioner(self, infos, names, starttasktype : str):
        for name in names:
            trg_act = self.getActionerFromLoadedOrTask(name)
            if trg_act:
                trg_man = trg_act.getCurrentManager()
                print(f"Copy for {name} by infos[{starttasktype}]")
                for info in infos["trees"]:
                    if starttasktype == "New":
                        trg_man.copyTree(info)
                    elif starttasktype == "Current":
                        trg_man.copyTree(info, trg_man.getCurrentTask())
                for info in infos["links"]:
                    print(f"Try to make link using:{info}")
                    task_in = trg_man.getTaskByName(info['to'])
                    task_out = trg_man.getTaskByName(info['from'])
                    trg_man.makeLink(task_in, task_out)
        return {}

    def forceUnFreezeParentTasks( self ):
        man = self.actioner.getCurrentManager()
        for task in man.getCurrentTask().getAllParents():
            man.forceUnFreezeTask(task)
        return self.updateMainUIelements()
    
    def executeExtTreeActionerJsonCmd( self, cmds_list ):
        task = self.actioner.getCurrentManager().getCurrentTask()
        cmds = []
        for cmd_txt in cmds_list:
            res, cmd = Loader.Loader.loadJsonFromText(cmd_txt)
            if res:
                cmds.append( cmd )
        # print(f"exe ext tree actions:\n{cmds}")
        task.exeExTreeTaskCmds( cmds )
        return self.updateMainUIelements()
    
    def removeExtTreeActionerJsonCmd( self, cmds_list ):
        task = self.actioner.getCurrentManager().getCurrentTask()
        cmds = []
        for cmd_txt in cmds_list:
            res, cmd = Loader.Loader.loadJsonFromText(cmd_txt)
            if res:
                cmds.append( cmd )
        # print(f"exe ext tree actions:\n{cmds}")
        task.removeJsonTaskCmds( cmds )
        return self.updateMainUIelements()
    
    def editSelectedExtTreeActionerJsonCmd( self, cmds_list ):
        cmds = []
        cmd_text = ""
        highligth = []
        for jsoncmd_txt in cmds_list:
            res, cmd = Loader.Loader.loadJsonFromText(jsoncmd_txt)
            if res:
                cmds.append( cmd )
                if "action" in cmd:
                    cmd_action = cmd.get("action","")
                    cmd_reason = cmd.get("reason","")
                    cmd_text += f"# Action `{cmd_action}`\n"
                    cmd_text += f"{cmd_reason}\n"
                    kwargs : dict = cmd.get("kwargs",{})
                    for k, v in kwargs.items():
                        cmd_text += f"### {k}\n{v}\n\n"
                # if "aa_info" in cmd:
                highligth.extend(CommandTool.highlightCmdResult(cmd))
        return Loader.Loader.convJsonToText( cmds ), cmd_text, highligth

    def executeEditedExtTreeActionerJsonCmd( self, cmds, taskname ):
        print(f"Execute edited extreeact json commands for {taskname}")
        task = self.actioner.getCurrentManager().getTaskByName( taskname )
        if task != None:
            task.exeExTreeTaskCmds( cmds )
            task.saveUpdationInfo()
            task.resetUpdationInfo()
        else:
            print("No task found")
        return self.updateMainUIelements()
 
    def executeJsonCmd( self, cmds, path ):
        print(f"Exe json cmd for act ({path})")
        act = self.getActionerByPath( path )
        if act != None:
            act.getJsonCmd( cmds )
        return self.updateMainUIelements()

    def cleanTasksChat(self):
        self.actioner.cleanTasksChat()
        return self.updateMainUIelements()
    
    def getCurrentActRelatedActionersPaths( self ):
        return gr.Dropdown(value=self.actioner.getPath(),choices= self.actioner.getRelatedActionersPaths( [self.actioner.getPath()] ) )
    
    def getCurrentTaskRelatedActionersPaths( self ):
        task = self.actioner.getCurrentManager().getCurrentTask()
        task_act_path = [] if task.getActioner() == None else [task.getActioner().getPath()]
        act_paths = task.getRelatedActionersPaths( task_act_path )
        return gr.Dropdown(value=None if len(act_paths) == 0 else act_paths[0],choices=act_paths)
 
    
    def getTasksWithCmds ( self, path ):
        out = []
        act = self.getActionerByPath( path)
        if act != None:
            for task in act.getCurrentManager().getTasks():
                res, actions = task.getAutoActCmds(checkhash = False)
                if res:
                    out.append( task.getName()) 
        return gr.Radio(choices=out)
    
    def setTaskCmdStatus ( self, name, idxs, status, act_path ):
        task :BaseTask = self.actioner.getCurrentManager().getTaskByName( name )
        if task:
            for i in idxs:
                task.setAutoActCmdStatus(i, status)
        return self.getTaskCmdList(act_path)
    
    def removeCmdFromTask (self, name, idxs):
        task :BaseTask = self.actioner.getCurrentManager().getTaskByName( name )
        if task:
            for i in idxs:
                task.removeAutoActCmdByIndex( idxs )
        return self.getTasksWithCmds()
    
    def exeTaskCmdsByStatus( self, name, status ):
        task :BaseTask = self.actioner.getCurrentManager().getTaskByName( name )
        cmds = []
        if task:
            cmds = task.getAutoActCmdByStatus(status)
            # self.actioner.getJsonCustomCmd( cmds )
            # return cmds
        return Loader.Loader.convJsonToText(cmds, indent = 3)


 
   
    def acceptTaskCmd( self, name, idxs ):
        task :BaseTask = self.actioner.getCurrentManager().getTaskByName( name )
        if task:
            cmds = []
            for i in idxs:
                cmds.append( task.getAutoActCmdAndSetStatus(aa_idx=i, status="accepted") )
            self.actioner.getJsonCustomCmd(cmds)
        return self.updateMainUIelements()

    def declineTaskCmd( self, name, idxs ):
        task :BaseTask = self.actioner.getCurrentManager().getTaskByName( name )
        if task:
            cmds = []
            for i in idxs:
                cmds.append( task.getAutoActCmdAndSetStatus(aa_idx=i, status="declined") )
        # return self.updateMainUIelements()

    def sendToRevisionTaskCmd( self, name, idxs ):
        task :BaseTask = self.actioner.getCurrentManager().getTaskByName( name )
        if task:
            cmds = []
            for i in idxs:
                cmds.append( task.getAutoActCmdAndSetStatus(aa_idx=i, status="needreview") )
        # return self.updateMainUIelements()
    
    def getTaskCmdList( self, path ):

        out = []
        act = self.getActionerByPath( path )
        if act != None:
            task = act.getCurrentManager().getCurrentTask()
            if task:
                res, cmds = task.getAutoActCmds(checkhash = False)
                if res:
                    # cres, cmds = Loader.Loader.loadJsonFromText( actions )
                    if isinstance(cmds, list):
                        for cmd in cmds:
                            if "action" in cmd:
                                out.append([Loader.Loader.convJsonToText(cmd), cmd["aa_idx"]])
                else:
                    print("No act")
            else:
                print("No task")
        return gr.CheckboxGroup(choices=out)
    
    def getTaskKwargsList ( self, cmdname, key ):
        task = self.actioner.getCurrentManager().getCurrentTask()
        out = ""
        if task:
            res, cmds = task.getAutoActCmds(checkhash = False)
            if res:
                # cres, cmds = Loader.Loader.loadJsonFromText( actions )
                if isinstance(cmds, list):
                    for cmd in cmds:
                        if "action" in cmd and cmd["action"] in cmdname and "kwargs" in cmd:
                            for k, value in cmd["kwargs"].items():
                                if k == key:
                                    out += value
                    return out
        return out


    def getGroupCommanagerCode( self ):
        target_file = Path("genslides/commanager/group.py")
        with target_file.open("r", encoding="utf-8") as f:
            text = f.read()
        return text

    def getJsonCmdsMethods( self ):
        text = self.getGroupCommanagerCode()
        methods, classes = pyparser.get_class_info(text, "Actioner")
        return methods
    
    def appendCmdToJson( self, cmds_str : str, cmd_name : str):
        cres, cmds = Loader.Loader.loadJsonFromText( cmds_str )
        code = self.getGroupCommanagerCode()
        action_value = {"action":cmd_name,"kwargs":{}}
        kwargs = pyparser.get_class_function_body(code, "Actioner", cmd_name, return_type= "params") 
        if kwargs != None:
            kwargs_list = kwargs.split(",")
            for arg in kwargs_list:
                re_arg = arg.replace("\n","")
                action_value['kwargs'].update({re_arg : ""})
        if cres and isinstance(cmds, list):
            cmds.append(action_value)
            cmds_str = Loader.Loader.convJsonToText( cmds, indent=3 )
        else:
            cmds_str = Loader.Loader.convJsonToText( [ action_value ], indent=3 )
        return cmds_str
    
    def undoCurrentManagerCommand( self ):
        self.actioner.getCurrentManager().undoCmd()
        return self.updateMainUIelements()
    
    def redoCurrentManagerCommand ( self ):
        self.actioner.getCurrentManager().redoCmd()
        return self.updateMainUIelements()
        
    def freezeCurrentTask( self ):
        task = self.actioner.getCurrentManager().getCurrentTask()
        task.freezeTask()
        return self.updateMainUIelements()
    
    def forceGetCurrentTaskUpdationInfo( self ):
        task = self.actioner.getCurrentManager().getCurrentTask()
        task.saveUpdationInfo()
        return self.updateMainUIelements()
    

