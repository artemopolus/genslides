from genslides.task.base import TaskManager, BaseTask, TaskDescription
from genslides.utils.savedata import SaveData
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

from os import listdir
from os.path import isfile, join


import os
import json
import gradio as gr
import datetime

import pyperclip
import pathlib
import matplotlib.pyplot as plt

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

        self.actioner = None

        self.tmp_actioner = None
        self.tmp_actioner_task = None

        # self.actioners_list : list[Actioner] = []

        self.actioners_list : list[dict] = []

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
        self.session_name_curr = 'untitled'
        self.session_name_path = 'session'
        FileManager.createFolder(self.session_name_path)
        self.session_names_list = FileManager.getClearFilenamesFromFilepaths(FileManager.getFilesPathInFolder(self.session_name_path))
        trg_name = self.session_name_curr
        idx = 0
        while( trg_name in self.session_names_list):
            trg_name = 'untitled' + str(idx)
            idx += 1
        
        self.session_name_curr = trg_name
        # self.session_names_list.append(trg_name)

        self.sec_actioner : Actioner = None

        self.trg_actioner : Actioner = None

        

    def getSessionNameList(self):
        return self.session_names_list

    def getSessionName(self):
        session_names = self.getSessionNameList()
        return gr.Dropdown(choices=session_names, value=self.getCurrentSessionName(), interactive=True)
    
    def setNewSessionName(self, name):
        if name not in self.session_names_list:
            self.session_name_curr = name
            self.session_names_list.append(name)
            self.saveSession()
        return  (
            self.getCurrentSessionName(),
            self.getSessionName()
            )
    
    def getSessionNameFromList(self, name):
        if name in self.session_names_list:
            self.session_name_curr = name
            self.loadSession()
        
        return self.updateTaskManagerUI()
    

    def getCurrentSessionName(self):
        return self.session_name_curr


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
        print("Vars for manager")
        print(f"Python path: { Loader.Loader.getUniPath( python_path )}")
        print(f"Manager folder: {Loader.Loader.getUniPath( fld )}")
        print(f"Manager space: { Loader.Loader.getUniPath( spc )}")
   
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
        print('Manager start tasks list:',len(self.manager.task_list))
        self.manager.onStart()
        print('Manager after reset tasks list:',len(self.manager.task_list))
        self.manager.initInfo(self.loadExtProject, path = self.actioner.getPath())
        if load:
            self.manager.disableOutput2()
            self.manager.loadTasksList(fast)
            self.manager.enableOutput2()
            self.actioner.loadTmpManagers()

 

# сохранение сессионных имен необходимо связать только с проектером сеном, а не с менеджером
    def updateSessionName(self):
        self.session_name_curr = self.current_project_name + "_" + datetime.datetime.now().strftime("%y%m%d_%H%M%S")
        print("Name of session=",self.session_name_curr)
        self.manager.setParam("session_name",self.session_name_curr)


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




    def load(self):
        self.actioner.setManager(self.actioner.std_manager)
        self.clearFiles()
        path = self.actioner.manager.getPath()
        path = Loader.Loader.getUniPath(path)
        print('Load files to',path)
        project_path = Loader.Loader.getUniPath(self.mypath)
        ppath = Loader.Loader.getFilePathFromSystemRaw()
        project_path = Loader.Loader.getUniPath(ppath.parent)
        filename = str(ppath.stem)

        Archivator.extractFiles(project_path, filename, path)
        self.resetManager(self.actioner.manager, path=self.actioner.getPath())
        self.current_project_name = filename
        self.actioner.manager.setParam("current_project_name",self.current_project_name)
        self.updateSessionName()
        return filename
    
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
        self.actioner.setManager(self.actioner.std_manager)
        man = self.actioner.manager
        self.saveManToTmp(man)
        return "Save"
    
    def saveManToTmp(self, man : Manager):
        path = Loader.Loader.getUniPath( Finder.findByKey("[[manager:path:spc]]", man, man.curr_task, man.helper ) )
        folder = Finder.findByKey("[[manager:path:fld]]", man, man.curr_task, man.helper )
        name = Finder.findByKey("[[manager:path:spc:name]]", man, man.curr_task, man.helper )
        fld_path = Loader.Loader.getUniPath( FileManager.addFolderToPath(folder, ["tt_temp"]))
        FileManager.createFolder(fld_path)
        trg_path = Loader.Loader.getUniPath( FileManager.addFolderToPath(folder, ["tt_temp",name + ".7z"]))
        Archivator.saveAllbyPath(data_path=path, trgfile_path=trg_path)


    def loadFromTmp(self):
        print('Load from temporary')
        self.actioner.setManager(self.actioner.std_manager)
        man = self.actioner.manager
        folder = Finder.findByKey("[[manager:path:fld]]", man, man.curr_task, man.helper )
        filename = Finder.findByKey("[[manager:path:spc:name]]", man, man.curr_task, man.helper )
        fld_path = Loader.Loader.getUniPath( FileManager.addFolderToPath(folder, ["tt_temp"]))
        path = Loader.Loader.getUniPath( Finder.findByKey("[[manager:path:spc]]", man, man.curr_task, man.helper ) )


        # self.clearFiles()
        # man.beforeRemove()
        FileManager.deleteFiles(man.getPath())

        project_path = fld_path

        Archivator.extractFiles(project_path, filename, path)
        self.resetManager(self.actioner.manager, path=self.actioner.getPath())
        return self.updateTaskManagerUI()

    def save(self, name):
        self.current_project_name = name
        self.actioner.std_manager.setParam("current_project_name",self.current_project_name)

        # Archivator.saveOnlyFiles(self.savedpath, self.mypath, name)
        self.actioner.setManager(self.actioner.std_manager)
        print('Save man', self.actioner.manager.getName(),'(Temp)' if self.actioner.manager != self.actioner.std_manager else '(Main)')
        path = self.actioner.manager.getPath()
        path = Loader.Loader.getUniPath(path)
        trg_path = Loader.Loader.getUniPath(Archivator.getProjectFileName())
        Archivator.saveAllbyPath(data_path=path, trgfile_path=trg_path)
        # Archivator.saveAllbyName(path, trg_path, name)

        # return gr.Dropdown( choices= self.loadList(), interactive=True)
        return "Save"
    
    def saveTmpMan(self):
        if self.actioner.manager == self.actioner.std_manager:
            return
        print(f"Save {self.actioner.manager.getName()} tmp manager")
        path = Loader.Loader.getUniPath(self.actioner.manager.getPath())
        trg_path = Loader.Loader.getUniPath(Archivator.getProjectFileName())
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
    
    def getFullCmdList(self, full = False):
        a = self.getCustomCmdList()
        p = self.getStdCmdList(full=full)
        a.extend(p)
        return a


    def makeCustomAction(self, prompt, selected_action, custom_action):
        print('Make custom action:', selected_action, custom_action, 'with prompt:\n', prompt)
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
                'resp2req','coll2req','read2req', #конвертировать задачи этого типа в другой
                'in','out','link','av_cp', #Параметры ветвления
                # 'step','chckresp',
                'sel2par', # Копировать и ветвиться от выбранной задачи
                'ignrlist',
                'wishlist', #
                'upd_cp', #Обновить ветки, которые скопирован ранее через Edit
                'onlymulti', #Копировать только мультивыбранные задачи
                'reqSraw', #Конвертировать ссылки в сообщениях при копировании
                'forcecopyresp', #Насильно вставлять промпт в Response,
                'check_man' #проверять менеджера
                ]
    
    def setEditChecks(self, checks):
        param = {}
        param['extedit'] = True
        names = self.getParamListForEdit()
        names.remove('resp2req')
        for name in names:
            if name =='onlymulti':
                if 'onlymulti' in checks:
                    param['trg_tasks'] = [t.getName() for t in self.actioner.manager.multiselect_tasks]
                else:
                    param['trg_tasks'] = [t.getName() for t in self.actioner.manager.task_list]
            else:
                param[name] = True if name in checks else False
        param['switch'] = []
        if 'resp2req' in checks:
            param['switch'].append({'src':'Response','trg':'Request'})
        if 'coll2req' in checks:
            param['switch'].append({'src':'Collect','trg':'Request'})
            param['switch'].append({'src':'GroupCollect','trg':'Request'})
            param['switch'].append({'src':'Garland','trg':'Request'})
        if 'read2req' in checks:
            param['switch'].append({'src':'ReadFileParam','trg':'Request'})
        return param

    
    def makeRequestAction(self, prompt, selected_action, selected_tag, checks):
        print('Make',selected_action,'Request\n', prompt)
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
        print('Action param=', param)
        return self.makeTaskAction(prompt=prompt,type1= act_type,creation_type= selected_action,creation_tag= selected_tag, param=param)

    def createGarlandOnSelectedTasks(self, action_type):
        self.actioner.manager.createTreeOnSelectedTasks(action_type,'Garland')
        return self.updateMainUIelements()

    def createCollectTreeOnSelectedTasks(self, action_type):
        self.actioner.manager.createTreeOnSelectedTasks(action_type,"Collect")
        return self.updateMainUIelements()
    
    def createShootTreeOnSelectedTasks(self, action_type):
        self.actioner.manager.createTreeOnSelectedTasks(action_type,"GroupCollect")
        return self.updateMainUIelements()
    
    def makeTaskAction(self, prompt, type1, creation_type, creation_tag, param = {}, save_action = True):
        self.actioner.makeTaskAction(prompt, type1, creation_type, creation_tag, param , save_action)
        return self.updateMainUIelements()
 

    def makeActionParent(self):
        man = self.actioner.manager
        if len(man.selected_tasks) == 0:
            return self.updateMainUIelements()
        else:
            param = {'select': man.getSelectedTask().getName()}
        return self.makeTaskAction("","","Parent","", param)
    
    def reparentCurTaskChildsUP(self):
        man = self.actioner.manager
        new_parent = man.curr_task.getParent()
        if new_parent != None:
            man.addTaskToSelectList(new_parent)
            for child in man.curr_task.getChilds():
                man.curr_task = child
                self.makeActionParent()
            man.curr_task = new_parent
        return self.updateMainUIelements()

    def swicthCurTaskUP(self):
        man = self.actioner.manager
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
        man = self.actioner.manager
        if len(man.selected_tasks) == 0:
            return self.updateMainUIelements()
        else:
            param = {'curr': man.getSelectedTask().getName()}
        return self.makeTaskAction("","","Parent","", param)
    

    def makeActionUnParent(self):
        return self.makeTaskAction("","","Unparent","")
    

    def makeActionLink(self):
        man = self.actioner.manager
        if len(man.selected_tasks) == 0:
            return self.updateMainUIelements()
        else:
            param = {'select': man.getSelectedTask().getName()}
        return self.makeTaskAction("","","Link","", param)
 
    def makeActionRevertLink(self):
        man = self.actioner.manager
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
    
    def uniteTask(self):
        man = self.actioner.manager
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
        self.actioner.manager.goToNextBranchEnd()
        return self.updateMainUIelements()
    
    def getComparisonTypes(self):
        return ['MultiSelect','Buds']
    
    def getBudMsgs(self, select_type):
        buds_chat = []
        iterate_array = []
        if select_type == 'Buds':
            iterate_array = self.actioner.manager.getBranchEndTasksList()
        elif select_type == 'MultiSelect':
            iterate_array = self.actioner.manager.multiselect_tasks
        for bud in iterate_array:
            name = bud.getName()
            res, contents, _ = bud.getLastMsgAndParent()
            if res:
                content = contents.pop()
                content['content'] = name + '\n\n---\n\n' + content['content']
                buds_chat.append(content)
        
        return self.actioner.manager.convertMsgsToChat(buds_chat)

    def getCopyBranch(self, id_branch):
        print('Get copy id:', id_branch)
        out = [self.actioner.manager.getChatRecord(id_branch)]
        out.extend( list( self.getCopyBranchesInfo()))
        return out
    
    def getCopyBranchRow(self, id_task):
        print('Get copy row by id:', id_task)
        out = [self.actioner.manager.getChatRecordRow(id_task)]
        out.extend(list(self.getCopyBranchesInfo()))
        return out
    
    def getCopyBranchesInfo(self):
        data = self.actioner.manager.curr_task.getChatRecords()
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
        self.actioner.manager.curr_task.setRecordsParam()
        return self.updateMainUIelements()
    
    def clearTaskRecords( self ):
        self.actioner.manager.curr_task.clearRecordParam()
        return self.updateMainUIelements()

    
    def goToNextBranch(self):
        self.actioner.manager.goToNextBranch()
        return self.updateMainUIelements()
    
    def goToPrevBranch(self):
        self.actioner.manager.goToNextBranch(revert=True)
        return self.updateMainUIelements()

    
    def goToBranchFork(self):
        man = self.actioner.manager
        _, trg = man.getBranchUpFork(start_task=man.getCurrentTask())
        man.curr_task = trg
        return self.updateMainUIelements()
    
    def goToCurrTaskBud(self):
        man = self.actioner.manager
        man.setCurrentTask(man.goToTaskBud(man.getCurrentTask()))
        return self.updateMainUIelements()

    
    def createNewTree(self):
        self.makeTaskAction("","SetOptions","New","user",[])
        self.actioner.manager.updateTreeArr()
        return self.updateMainUIelements()
    
    def goToNextTree(self):
        print('Go to next tree')
        # if self.actioner.manager != self.actioner.std_manager:
        #     self.actioner.manager.sortTreeOrder(check_list=True)
        # else:
        #     self.actioner.manager.sortTreeOrder(True)
        self.actioner.manager.goToNextTree()
        return self.updateMainUIelements()
    
    def goBackByLink(self):
        man = self.actioner.manager
        man.goBackByLink()
        return self.updateMainUIelements()
    
    def goToNextChild(self):
        self.actioner.manager.goToNextChild()
        return self.updateMainUIelements()
        # return self.makeTaskAction("","","GoToNextChild","")

    def goToParent(self):
        self.actioner.manager.goToParent()
        return self.updateMainUIelements()
        # return self.makeTaskAction("","","GoToParent","")

    def goToHalfBranch(self):
        cur = self.actioner.manager.curr_task
        tasks = cur.getAllParents()
        idx = int(len(tasks)/2)
        self.actioner.manager.curr_task = tasks[idx]
        return self.updateMainUIelements()
    
    def moveToNextChild(self):
        self.actioner.manager.goToNextChild()
        return self.updateMainUIelements()
    
    def moveToParent(self):
        # self.actioner.manager.curr_task.resetQueue()
        self.actioner.manager.goToParent()
        return self.updateMainUIelements()
    
    def moveToNextBranch(self):
        man = self.actioner.manager
        man.goToNextBranch()
        if man.curr_task.parent != None:
            trg = man.curr_task.parent
            man.curr_task = trg
        return self.updateMainUIelements()

    def switchRole(self, role, prompt):
        task = self.actioner.manager.curr_task
        print('Set role[', role, ']for',task.getName())
        self.makeTaskAction(task.getLastMsgContent(), "Request", "Edit", role)
        return self.updateUIelements(prompt=prompt)
  
 
    def appendNewParamToTask(self, param_name):
        self.makeTaskAction('','','AppendNewParam','', {'name':param_name})
        return self.updateTaskManagerUI()
    
    def removeParamFromTask(self, param_name):
        self.makeTaskAction('','','RemoveTaskParam','', {'name':param_name})
        return self.updateTaskManagerUI()
    
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
        print('Set task key value:','|'.join([param_name,key,str(mnl_value)]))
        self.makeTaskAction('','','SetParamValue','', {'name':param_name,'key':key,'manual':mnl_value})
        return self.updateTaskManagerUI()
    
    def setSelectOptionToValue(self, name, key, option):
        return option
    
    def addTaskNewKeyValue(self, param_name, key, value):
        print('Set task key value:','|'.join([param_name,key,str(value)]))
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
        man = self.actioner.manager
        param_json = {'actions':[],'repeat':3,'task_names':[t.getName() for t in man.multiselect_tasks]}
        if mannametype == 'Current':
            param_json['name'] = man.curr_task.getName()
        elif mannametype == 'Selected':
            param_json['name'] = man.getSelectedTask().getName()
        elif mannametype == '1st MultiS' and len(man.getMultiSelectedTasks()):
            param_json['name'] = man.getMultiSelectedTasks()[0]
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
        man = act.manager
        if man != act.std_manager:
            print ('Can init only from Base')
            return self.updateTaskManagerUI()
        if 'move_tasks'  in params:
            copytasks = [man.getTaskByName(name) for name in params['move_tasks']]
            del params['move_tasks']
        self.makeTaskAction("","","InitPrivManager","", params)
        man.clearMultiSelectedTasksList()
        if len(copytasks) and man != act.manager:
            act.std_manager.clearMultiSelectedTasksList()
            act.moveTaskFromManagerToAnother(tasks=copytasks, 
                                                        cur_man=act.std_manager,
                                                        next_man=act.manager
                                                        )

        return self.updateTaskManagerUI()

    def initPrivManager(self):
        print("Init empty private manager")
        man = self.actioner.manager
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
    
    def getActionerList(self):
        return gr.Radio(choices=[a['act'].getPath() for a in self.actioners_list], 
    value=self.actioner.getPath() if self.actioner != None else None, interactive=True)
    
    def selectActionerByInfo(self, info):
        for act in self.actioners_list:
            if act['act'].getPath() == info:
                self.actioner = act['act']
        return self.updateTaskManagerUI()
 
   
    def addActionerTolist(self, act : Actioner, params = {'type':'project'}, move2selected = True):
        found = False
        for actpack in self.actioners_list:
            if actpack['act'] == act:
                found = True
                break
        if not found:
            self.actioners_list.append({'act':act, 'params':params})
            self.saveSession()
        if move2selected:
            self.actioner = act

    def saveSession(self):
        act_data = []
        for act in self.actioners_list:
            act_info = {
                'act_path': act['act'].getPath(),
                'type' : act['params']['type']
            }
            if act['params']['type'] == 'exttreetask':
                act_info['trg_task_name'] = act['params']['task'].getName()
            act_data.append(act_info)
        session_data = {
            'actioners': act_data
        }
        path = FileManager.addFolderToPath(self.session_name_path,[self.session_name_curr + ".json"])
        Writer.writeJsonToFile(Loader.Loader.getUniPath(path), session_data)
   
    def loadSession(self):
        path = FileManager.addFolderToPath(self.session_name_path,[self.session_name_curr + ".json"])
        session_data = Reader.ReadFileMan.readJson(path)
        projects_info = []
        exttreetask_info = []
        if 'actioners' in session_data:
            for act_info in session_data['actioners']:
                if act_info['type'] == 'project':
                    projects_info.append(act_info)
                elif act_info['type'] == 'exttreetask':
                    exttreetask_info.append(act_info)

        for info in projects_info:
            self.loadActionerByPath(info['act_path'])

        active_act = self.actioners_list.copy()
        for info in exttreetask_info:
            name = info['trg_task_name']
            trg_tasks = []
            for act in active_act:
                act_tasks = act['act'].getTasksByName(name)
                
                trg_tasks.extend([t for t in act_tasks if t not in trg_tasks])
            for task in trg_tasks:
                self.addExtTreeTaskActioner(task)

        for act in self.actioners_list:
            act['act'].afterLoading()



    def addCurrentExtTreeTaskActioner(self):
        man = self.actioner.manager
        task = man.curr_task
        self.addExtTreeTaskActioner(task)
        return self.updateTaskManagerUI()
    
    def addExtTreeTaskActioner(self, task : BaseTask):
        task_actioner = task.getActioner()
        if task_actioner != None:
            self.addActionerTolist(task_actioner, params={'type':'exttreetask','task': task})
            self.actioner.loadStdManagerTasks()

    def createActioner(self, eparam) -> Actioner:
        dt1 = datetime.datetime.now()        
        path = eparam['exttreetask_path']
        manager = Manager(RequestHelper(), TestRequester(), GoogleApiSearcher())
        manager.onStart()
        manager.initInfo(self.loadExtProject, path = path)
        if 'retarget' in eparam:
            manager.addRenamedPair(eparam['retarget']['std'],eparam['retarget']['chg'])
        elif 'retrgs' in eparam:
            for pair in eparam['retrgs']:
                manager.addRenamedPair(pair['std'], pair['chg'])
        act = Actioner(manager)
        act.setPath(path)
        self.saveManToTmp(manager)
        if 'load' in eparam and eparam['load']:
            manager.disableOutput2()
            if 'loadtype' in eparam:
                manager.loadTasksList(safe = True if eparam['loadtype' == 'safe'] else False)
            else:
                manager.loadTasksList(safe = False)
            manager.enableOutput2()
            act.loadTmpManagers()
        dt2 = datetime.datetime.now()     
        print('Actioner was created by:\t',(dt2-dt1).seconds,'second(s)')    
        return act


    def loadActionerByBrowsing(self):
        path = Loader.Loader.getDirPathFromSystem()
        print('Load manager by path',path)
        man_path = Loader.Loader.getUniPath(path)
        self.loadActionerByPath(man_path)
        return self.updateTaskManagerUI()

    def loadActionerByPath(self, man_path : str):
        actioner = self.createActioner({'exttreetask_path':man_path,'load':True})
        self.addActionerTolist(actioner)
        man = self.actioner.std_manager
        if len(man.task_list) == 0:
            self.createNewTree()
        print('Load manager from browser is complete')
        python_path = Finder.findByKey("[[project:RunScript:python]]", man, man.curr_task, man.helper)
        fld = Finder.findByKey("[[manager:path:fld]]", man, man.curr_task, man.helper)
        spc = Finder.findByKey("[[manager:path:spc]]", man, man.curr_task, man.helper)
        print("Vars for manager")
        print(f"Python path: { Loader.Loader.getUniPath( python_path )}")
        print(f"Manager folder: {Loader.Loader.getUniPath( fld )}")
        print(f"Manager space: { Loader.Loader.getUniPath( spc )}")
   


    def switchToExtTaskManager(self):
        print('Switch to ext task manager')
        man = self.actioner.manager
        task = man.curr_task
        return self.switchToTargetInExtTreeTask(task)
    
    def switchToTargetInExtTreeTask(self, task):
        task_actioner = task.getActioner()
        if task_actioner != None and self.tmp_actioner == None:
            self.tmp_actioner_task = task
            self.tmp_actioner = self.actioner
            self.actioner = task_actioner
            self.actioner.loadStdManagerTasks()
            print('Switch on actioner of', task.getName())
            print('Path:', self.actioner.getPath())
            print('Man:', self.actioner.manager.getName())
            # print('Tasks:',[t.getName() for t in self.actioner.manager.task_list])
        return self.updateTaskManagerUI()
    
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
        #TODO: Нужно разобраться почему так происходит и убрать этот костыль
        self.actioner.manager.fixTasks()
        return self.updateTaskManagerUI()
  
    def rmvePrivManager(self):
        self.makeTaskAction("","","RmvePrivManager","")
        #TODO: Нужно разобраться почему так происходит и убрать этот костыль
        self.actioner.manager.fixTasks()
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
            out = gr.Code(value=self.actioner.manager.getCurTaskLstMsgRaw(), language=None)
            if vizualisation != 'None':
                out =  gr.Code(value=self.actioner.manager.getCurTaskLstMsgRaw(),language=vizualisation)
        return out


    def actionTypeChanging(self, action, vizualisation):
        print('Action switch to=', action)
        # highlighttext = []
        if action == 'New':
            return ("", 
                    gr.Button(value='Request'), 
                    gr.Button(value='Response', interactive=False), 
                    gr.Button(value='Custom',interactive=True), 
                    gr.Radio(interactive=False),
                    gr.CheckboxGroup(choices=[])
                    )
        elif action == 'SubTask' or action == 'Insert':
            return ("", 
                    gr.Button(value='Request'), 
                    gr.Button(value='Response', interactive=True), 
                    gr.Button(value='Custom',interactive=True), 
                    gr.Radio(interactive=False),
                    gr.CheckboxGroup(choices=[])
                    )
        elif action == 'Edit' or action == 'EditCopy' or action.startswith('EdCp'):
            print('Get text from',self.actioner.manager.curr_task.getName(),'(',self.actioner.manager.getName(),')')
            _,role,_ = self.actioner.manager.curr_task.getMsgInfo()
            # out = gr.Code(value=self.actioner.manager.getCurTaskLstMsgRaw(), language=None)
            out = gr.Textbox(value=self.actioner.manager.getCurTaskLstMsgRaw())
            # if vizualisation != 'None':
                # out =  gr.Code(value=self.actioner.manager.getCurTaskLstMsgRaw(),language=vizualisation)
            return (out, 
                    gr.Button(value='Apply'), 
                    gr.Button(value='Divide',interactive=True), 
                    gr.Button(value='',interactive=False), 
                    gr.Radio(interactive=True,value=role),
                    gr.CheckboxGroup(choices=self.getParamListForEdit(), interactive=True)
                    )
    def getTextInfo(self, notgood, bad):
        param = {'notgood': notgood, 'bad':bad}
        pairs, log, vector = self.actioner.manager.curr_task.getTextInfo(param)
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
        man = self.actioner.manager
        pairs = man.curr_task.getWordTokenPairs()
        todraw = []
        for pair in pairs:
            todraw.append([pair['token'],'token'])
            todraw.append([ str(pair['bytes']) ,'bytes'])
        return todraw


    def getActionsList(self) -> list:
        actions = self.actioner.manager.info['actions']
        out = []
        for act in actions:
            name = ':'.join([str(act['id']),act['action'],act['type']])
            out.append(name)
        return gr.CheckboxGroup(choices=out, interactive=True,value=None)
    
    def getActionInfo(self, names : list):
        print('Get action info from', names)
        text = ''
        for name in names:
            pack = name.split(':')
            actions = self.actioner.manager.info['actions']
            for idx in range(len(actions)):
                if pack[0] == str(actions[idx]['id']):
                    text += json.dumps(actions[idx], indent=1) + '\n'
        return text
 
    
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
                    break

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
        return self.getUItmpmanagers()
    
    def setCurrAsManagerStartTask(self):
        name = self.actioner.manager.curr_task.getName()
        return self.setManagerStartTask(name)
    
    def backToStartTask(self):
        manager = self.actioner.manager
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
        self.actioner.manager.addActions(action=action, param=json.loads(param))
        return self.getActionsList()

    def copyChainStepped(self):
        print('Copy chain stepped')
        # tasks_chains = self.actioner.manager.curr_task.getTasksFullLinks({'in':True, 'out':True,'link':True})
        # self.actioner.manager.copyTasksByInfo(tasks_chains=tasks_chains,edited_prompt='test', change_prompt=True, trg_type_t='', src_type_t='')
        self.actioner.manager.copyTasksByInfoStep()
        return self.updateMainUIelements()

    def setTreeName(self, name : str):
        self.actioner.manager.curr_task.setBranchSummary(name)
        return self.updateMainUIelements()

    def goToTreeByName(self, name):
        self.actioner.goToTreeByName(name)
        return self.updateMainUIelements()

    def resetUpdate(self):
        self.actioner.resetUpdate()
        return self.updateMainUIelements()
       
    def update(self):
        self.actioner.update()
        return self.updateMainUIelements()
        
    def updateAll(self, check = False):
        print('Update All trees stepped')
        self.actioner.manager.disableOutput2()
        self.actioner.updateAll(force_check=check)
        self.actioner.manager.enableOutput2()
        return self.updateMainUIelements()
    
    def updateAllnTimes(self, n, check = False):
        print('Update All trees stepped',n,'times')
        self.actioner.manager.disableOutput2()
        for i in range(n):
            print('UAT:', i)
            self.actioner.updateAll(force_check=check)
        self.actioner.manager.enableOutput2()
        return self.updateMainUIelements()

    
    def updateCurrentTree(self):
        self.actioner.manager.disableOutput2()
        self.actioner.updateCurrentTree()
        self.actioner.manager.enableOutput2()
        return self.updateMainUIelements()

   
    def updateAllUntillCurrTask(self, force_check = False):
        self.actioner.manager.disableOutput2()
        self.actioner.updateAllUntillCurrTask(force_check=force_check)
        self.actioner.manager.enableOutput2()
        return self.updateMainUIelements()
    
    def updateChildTasks(self, force_check = False):
        man = self.actioner.manager
        act = self.actioner
        start_task = man.curr_task
        if force_check:
            targets = [t for t in man.curr_task.getAllChildChains() if t in man.task_list]
        else:
            targets = man.curr_task.getAllChildChains()
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
        
    def updateMultiSelectedTasks(self, force_check = False):
        man = self.actioner.manager
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
        man = self.actioner.manager
        start_task = man.curr_task
        fork_root = None
        trg = start_task
        idx = 0
        while(idx < 1000):
            par = trg.getParent()
            if par == None:
                return
            if len(par.getChilds()) > 1:
                fork_root = trg
                break
            elif par.isRootParent():
                fork_root = par
                break
            else:
                trg = par
            idx +=1
        man.curr_task = fork_root
        self.updateChildTasks(force_check)
        man.curr_task = start_task
        return self.updateMainUIelements()
        
 
   
    def setBranchEndName(self, summary):
        self.actioner.manager.setBranchEndName(summary)
        return self.updateMainUIelements()

    
    def setCurrTaskByBranchEndName(self, name):
        self.actioner.setCurrTaskByBranchEndName( name)
        return self.updateMainUIelements()
    
    def cleanCurrTask(self):
        man = self.actioner.manager
        man.curr_task.forceCleanChat()
        return self.updateMainUIelements()


    def relinkToCurrTaskByName(self, name):
        return self.makeTaskAction('','','RelinkToCurrTask','', {'name':name})
    
    def selectRelatedChain(self):
        man = self.actioner.manager
        taskchainnames = man.getRelatedTaskChains(man.curr_task.getName(), man.getPath())
        for name in taskchainnames:
            man.addTaskToMultiSelected(man.getTaskByName(name))
        # return self.actioner.getRelationTasksChain()
        return self.updateMainUIelements()
    
    def selectNearestTasks(self):
        man = self.actioner.manager
        tasks = man.curr_task.getHoldGarlands()
        tasks.extend(man.curr_task.getGarlandPart())
        for task in tasks:
                man.addTaskToMultiSelected(task)
        return self.updateMainUIelements()
    
    def selectGarlandHolders(self):
        man = self.actioner.manager
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
    
    def applyAutoCommandsToMulti(self):
        self.actioner.createTmpManagerForCommandExe()
        return self.updateTaskManagerUI()

    def saveManagerActionToCurrentTask(self, type_name):
        self.actioner.saveActionsToCurrTaskAutoCommand(type_name=type_name)
        return self.updateTaskManagerUI()

       
    
    def deselectRealtedChain(self):
        self.actioner.manager.multiselect_tasks = []
        return self.updateMainUIelements()
    
    def appendTaskToChain(self):
        man = self.actioner.manager
        man.addTaskToMultiSelected(man.curr_task)
        return self.updateMainUIelements()
    
    def removeTaskFromChain(self):
        man = self.actioner.manager
        if man.curr_task in man.multiselect_tasks:
            man.multiselect_tasks.remove(man.curr_task)
        return self.updateMainUIelements()
    
    def appendTreeToChain(self):
        man = self.actioner.manager
        tasks = man.curr_task.getTree()
        for task in tasks:
                man.addTaskToMultiSelected(task)
        return self.updateMainUIelements()
    
    def removeTreeFromChain(self):
        man = self.actioner.manager
        tasks = man.curr_task.getTree()
        for task in tasks:
            if task in man.multiselect_tasks:
                man.multiselect_tasks.remove(task)
        return self.updateMainUIelements()
   
    def appendBranchPartToChain(self):
        man = self.actioner.manager
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
        man = self.actioner.manager
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
        man = self.actioner.manager
        buds = man.curr_task.getAllBuds()
        bud = buds.pop()
        tasks = bud.getAllParents()
        for task in tasks:
                man.addTaskToMultiSelected(task)
        return self.updateMainUIelements()
 
    def removeBranchFromChain(self):
        man = self.actioner.manager
        buds = man.curr_task.getAllBuds()
        bud = buds.pop()
        tasks = bud.getAllParents()
        for task in tasks:
            if task in man.multiselect_tasks:
                man.multiselect_tasks.remove(task)
        return self.updateMainUIelements()
   
    def appendChildsToChain(self):
        man = self.actioner.manager
        tasks = man.curr_task.getAllChildChains()
        for task in tasks:
                man.addTaskToMultiSelected(task)
        return self.updateMainUIelements()
 
    def removeChildsFromChain(self):
        man = self.actioner.manager
        tasks = man.curr_task.getAllChildChains()
        for task in tasks:
            if task in man.multiselect_tasks:
                man.multiselect_tasks.remove(task)
        return self.updateMainUIelements()
    
    def removeParentsFromChain(self):
        man = self.actioner.manager
        tasks = man.curr_task.getAllParents()
        tasks.remove(man.curr_task)
        for task in tasks:
            if task in man.multiselect_tasks:
                man.multiselect_tasks.remove(task)
        return self.updateMainUIelements()

    def selectRowTasks(self):
        man = self.actioner.manager
        trg, child_idx = man.curr_task.getClosestBranching()
        tasks = trg.getChildSameRange(trg_idx=child_idx)
        for task in tasks:
            if task in man.task_list:
                man.addTaskToMultiSelected(task)
        return self.updateMainUIelements()
    
    def selectCopyBranch(self):
        man = self.actioner.manager
        tasks = man.getCopyBranch(man.curr_task)
        for task in tasks:
            if task in man.task_list:
                man.addTaskToMultiSelected(task)
        return self.updateMainUIelements()

    def selectCopyTasks(self):
        man = self.actioner.manager
        tasks = man.getCopyTasks(man.curr_task)
        for task in tasks:
            if task in man.task_list:
                man.addTaskToMultiSelected(task)
        return self.updateMainUIelements()
   
    def selectTaskRowFromCurrent(self, child_idx):
        man = self.actioner.manager
        tasks = man.curr_task.getChildSameRange(trg_idx=child_idx)
        for task in tasks:
                man.addTaskToMultiSelected(task)
        return self.updateMainUIelements()


    def getParamFromMultiSelected(self, key, info = ""):
        man = self.actioner.manager
        param = None
        difftasknames = []
        for task in man.multiselect_tasks:
            res, t_param = task.getParamStruct(param_name=key)
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
        man = self.actioner.manager
        start = man.curr_task
        for task in man.multiselect_tasks:
            man.curr_task = task
            self.setTaskKeyValue(param_name=param, key=key, slt_value='', mnl_value=value)
        man.curr_task = start

    def setParamStructToMultiSelect(self, text_param, param_name):
        print('Set param struct to multiselect')
        task_names = []
        try:
            man = self.actioner.manager
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
        man = self.actioner.manager
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
        man = self.actioner.manager
        start = man.curr_task
        trg = start
        for task in man.multiselect_tasks:
            man.addTaskToSelectList(task)
            man.curr_task = trg
            self.createCollectTreeOnSelectedTasks('SubTask')
            trg = man.curr_task
        man.curr_task = start
        return self.updateMainUIelements()

    def shiftParentTagForMultiSelect(self, shift : int):
        man = self.actioner.manager
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
        man = self.actioner.manager
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
        man = self.actioner.manager
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
        man = self.actioner.manager
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
        return (
            gr.Dropdown(choices=choices, value=value, interactive=interactive, multiselect=multiselect),
            gr.Textbox(text, interactive=text_interactive)
        )
    def getTaskKeyValue(self, param_name, param_key):
        choices, value, interactive, multiselect, text, text_interactive = self.actioner.getTaskKeyValueInternal(param_name, param_key)
        return self.setTaskKeyValueUI(choices, value, interactive, multiselect, text, text_interactive)
    
    def getAppendableParam(self):
        return self.actioner.manager.getAppendableParam()
    
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
        man = self.actioner.manager
        task = man.curr_task
        task.forceCleanChat()
        return self.updateMainUIelements()

    def getCurrentTaskBranchCodeTag(self):
        man = self.actioner.manager
        code = man.curr_task.getBranchCodeTag()
        out = []
        out.append(code)
        allchaintasknames = man.getTaskFileNamesByBranchCode(code, man.curr_task.getName())
        print(allchaintasknames)
        out.append(str(allchaintasknames))
        pyperclip.copy('\n'.join(out))
        pyperclip.paste()

   
   

    def moveBranchIdxUp(self):
        man = self.actioner.manager
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
            task.getParent().getChilds()[idx - 1].setPrio(idx)
            task.setPrio(idx -1)
        return self.updateMainUIelements()
    
    def moveBranchIdxDw(self):
        man = self.actioner.manager
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
        man = self.actioner.manager
        task = man.curr_task
        cur_tree = task.getRootParent()
        sres, sparam = cur_tree.getParamStruct('tree_step', True)
        if sres:
            idx = sparam['idx']
            if idx != 0:
                idx -= 1
            cur_tree.updateParamStruct(param_name='tree_step',key='idx', val=idx)
        return self.updateMainUIelements()
 
    def moveDwTree(self):
        man = self.actioner.manager
        task = man.curr_task
        cur_tree = task.getRootParent()
        sres, sparam = cur_tree.getParamStruct('tree_step', True)
        if sres:
            idx = sparam['idx']
            if idx != 0:
                idx += 1
            cur_tree.updateParamStruct(param_name='tree_step',key='idx', val=idx)
        return self.updateMainUIelements()

 
    def addCurrTaskToSelectList(self):
        return self.actioner.manager.addCurrTaskToSelectList()

    def getRelationBack(self, range):
        man = self.actioner.manager
        # taskchainnames = man.getRelatedTaskChains(man.curr_task.getName(), man.getPath(), max_idx=range)
        # for name in taskchainnames:
            # man.addTaskToMultiSelected(man.getTaskByName(name))
        man.getBackwardRelatedTaskChain(man.curr_task, range)
        return self.updateMainUIelements()

    def getRalationForward(self, range):
        man = self.actioner.manager
        man.getForwardRelatedTaskChain(man.curr_task, range)
        return self.updateMainUIelements()
    
    def setCurrentTaskByName(self, name):
        self.actioner.manager.setCurrentTaskByName(name)
        return self.updateMainUIelements()
    

    def setCurManagerColor(self, color):
        print('Set color', color,'to',self.actioner.manager.getName())
        self.actioner.manager.info['color'] = color
        self.actioner.manager.saveInfo()

    def setCurManagerName(self, name):
        self.actioner.manager.setName(name)
        self.actioner.manager.saveInfo()
        return self.updateTaskManagerUI()
    
    def addMultiSelectTasksFromStdMan(self):
        if self.actioner.manager != self.actioner.std_manager:
            self.actioner.addExtTasksForManager(self.actioner.manager, self.actioner.std_manager.multiselect_tasks)
        return self.updateTaskManagerUI()

    def rmvMultiSelectTasksFromTmpMan(self):
        if self.actioner.manager != self.actioner.std_manager:
            self.actioner.rmvExtTasksForManager(self.actioner.manager, self.actioner.manager.multiselect_tasks)
        return self.updateTaskManagerUI()

    def moveTaskToStdMan(self):
        print('Move TmpMan tasks to StdMan')
        if self.actioner.manager != self.actioner.std_manager:
            self.actioner.moveTaskFromTMPmanToSTDman(tasks= self.actioner.manager.multiselect_tasks, 
                                                       cur_man= self.actioner.manager,
                                                       next_man= self.actioner.std_manager
                                                       )
        return self.updateTaskManagerUI()

    def moveTaskToTmpMan(self):
        if self.actioner.manager != self.actioner.std_manager:
            task_to_copy = self.actioner.std_manager.multiselect_tasks.copy()
            self.actioner.std_manager.multiselect_tasks = []
            self.actioner.moveTaskFromManagerToAnother(tasks=task_to_copy, 
                                                       cur_man=self.actioner.std_manager,
                                                       next_man=self.actioner.manager
                                                       )
        return self.updateTaskManagerUI()

    def moveTaskTmpToTmp(self, name):
        if self.actioner.manager == self.actioner.std_manager:
            return self.updateTaskManagerUI()
        if self.actioner.std_manager.getName() == name:
            return self.updateTaskManagerUI()
        else:
            start_man = self.actioner.manager
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
        path = Loader.Loader.getDirPathFromSystem(self.actioner.manager.getPath())
        return self.loadMangerExtInfoExt(path)
    
    def loadMangerExtInfoExtForCurTask(self):
        man = self.actioner.manager
        taskpath = FileManager.addFolderToPath(man.getPath(), ['tmp', man.curr_task.getName() ])
        path = Loader.Loader.checkManagerTag(taskpath, man.getPath(), False)
        return self.loadMangerExtInfoExt(path)
    
    def loadTmpManagerInfoForCopying(self):
        man = self.actioner.manager
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
        man = self.actioner.manager
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
        manpath = Finder.findByKey(path,self.actioner.manager, None, self.actioner.manager.helper)
        buds_info, tasks_info, all_tasks = Searcher.ProjectSearcher.openProject(manpath)
        parents = self.actioner.manager.curr_task.getAllParents()
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
                return budinfo['summary'], budinfo['branch'], self.actioner.manager.convertMsgsToChat(msgs=budinfo['message'])
        return '','',[]

    def saveCurrManInfo(self):
        self.actioner.manager.saveInfo(True)

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
        man = self.actioner.manager
        if self.tmp_actioner_task.checkType('InExtTree'):
            act = self.tmp_actioner_task.getActioner()
            task = act.manager.curr_task
            return self.addOutExtTreeInfo(start_inext, task.getName())
        return self.addOutExtTreeInfo(start_inext, '')
    
    def addOutExtTreeInfo(self, start_inext,  task_name):
        extbrjson = start_inext
        extbrjson['target'] = task_name
        return json.dumps(extbrjson, indent=1)
    
    def addInExtTreeSubTask(self, params):
        man = self.actioner.manager
        man.createOrAddTask('','InExtTree','user',man.curr_task, [json.loads(params)])
        return self.updateMainUIelements()
    
    def convertTaskBranchInInOutExtPair(self):
        man = self.actioner.manager
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
            task_actioner.manager.loadTasksListFileBased()
            task_actioner.manager.copyTasksIntoManager(man.multiselect_tasks)
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
        man = self.actioner.manager
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
        task_actioner.manager.loadTasksListFileBased()
        task_actioner.manager.copyTasksIntoManager(man.multiselect_tasks)

        return self.updateMainUIelements()
        


    
    def addOutExtTreeSubTask(self, params):
        if self.tmp_actioner_task != None:
            man = self.tmp_actioner_task.getManager()
            if self.tmp_actioner_task.checkType('InExtTree'):
                man.createOrAddTask('','OutExtTree','user',man.curr_task, [params])
        # return self.updateMainUIelements()
    
    def getExtTreeParamsForEdit(self):
        man = self.actioner.manager
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
        man = self.actioner.manager
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
        msgs = self.actioner.manager.curr_task.getMsgs()
        text = ""
        for msg in msgs:
            text += msg['role'] + '\n' + 10*'====' + '\n\n\n'
            text += msg['content'] + '\n'
        self.copyToClickBoard(text)
        return "[[parent:allmsgs]]", text

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
    def copyToClickBoardPaths(self):
        paths = Loader.Loader.getFilePathArrayFromSysten(self.actioner.manager.getPath())
        self.copyToClickBoard(' '.join(paths))
        return paths, ""

    def copyToClickBoardDialRaw(self):
        msgs = self.actioner.manager.curr_task.getRawMsgs()
        text = ""
        for msg in msgs:
            text += msg['role'] + '\n' + 10*'====' + '\n\n\n'
            text += msg['content'] + '\n'
        self.copyToClickBoard(text)

    def copyToClickBoardReqListRaw(self):
        msgs = self.actioner.manager.curr_task.getRawMsgs()
        text = ""
        for msg in msgs:
            if msg['role'] == 'user':
                # text += msg['role'] + '\n' + 10*'====' + '\n\n\n'
                text += msg['content'] + '\n'
        pyperclip.copy(text)
        pyperclip.paste()
   

    def copyToClickBoardLstMsg(self):
        msg = self.actioner.manager.getCurTaskLstMsg()
        pyperclip.copy(msg)
        pyperclip.paste()
        return "[[parent:msg_content]]", msg

    

    def copyToClickBoardTokens(self):
        tokens, price = self.actioner.manager.curr_task.getCountPrice()
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
        man = act.manager
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
        man = act.manager
       
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
        man = act.manager
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
        man = act.manager
        path = Loader.Loader.getDirPathFromSystem(self.actioner.manager.getPath())
        manpath = Finder.findByKey(path,self.actioner.manager, None, self.actioner.manager.helper)
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
        man = act.manager
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
        self.actioner.manager.curr_task = task
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
        self.actioner.manager.fixTasks()
        return self.updateMainUIelements() 

    def getCurManInExtTreeTasks(self):
        man = self.actioner.manager
        out = []
        for task in man.task_list:
            if task.checkType('InExtTree'):
                out.append(task.getName())
        return gr.CheckboxGroup(choices=out, interactive=True)
    
    def updateInExtTreeTasksByName(self, names : list[str]):
        man = self.actioner.manager
        for name in names:
            task = man.getTaskByName(name)
            if task != None and task.checkType('InExtTree'):
                self.switchToTargetInExtTreeTask(task)
                self.backToDefaultActioner()
        return self.updateMainUIelements() 
    
    def copyManagerTaskFilesToAnotherFolder(self):
        man = self.actioner.manager
        
        trg_path = Loader.Loader.getDirPathFromSystem()
        print(f"Target path: {trg_path}")
        for task in man.task_list:
            print(f"Copy file by path {task.getJsonFilePath()}")
            FileManager.copyFile(Loader.Loader.getUniPath(task.getJsonFilePath()), Loader.Loader.getUniPath(trg_path))
        print('Copying done')

    def setHideTaskStatus(self, value):
        self.actioner.hide_task = value
        return self.updateMainUIelements() 


    def getByTaskNameParamList(self, task_name):
        man = self.actioner.manager
        task = man.getTaskByName(task_name)
        return gr.Dropdown(choices=man.getByTaskNameParamListInternal(task), interactive=True)

    def getTaskKeys(self, param_name):
        man = self.actioner.manager
        return self.getNamedTaskKeys(man.curr_task, param_name)

    def getByTaskNameTasksKeys(self, task_name, param_name):
        man = self.actioner.manager
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
        print('Get named task keys', a)
        val = None
        return gr.Dropdown(choices=a, value=val, interactive=True)

    def getFinderKeyString(self,task_name, fk_type, param_name, key_name):
        value = Finder.getKey(task_name, fk_type, param_name, key_name, self)
        pyperclip.copy(value)
        pyperclip.paste()

    def updateMainUIelements(self):
        return self.updateUIelements()

    def convToGradioUI(self, 
                        r_msgs, 
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
            set_prompt, 
            gr.Dropdown(choices= mangettasklist),
            gr.Dropdown(choices=mangetcurtaskparamlist, interactive=True), 
            gr.Dropdown(choices=curtaskallpars, 
                               value=mancurtaskgetname, 
                               interactive=True), 
            gr.Radio(value="SubTask"), 
            bud_msgs,
            # self.getCurrentExtTaskOptions(),
            gr.Radio(choices=gettreenameforradio_names, value=gettreenameforradio_trg, interactive=True),
            gr.Textbox(value=mancurtaskgetbranchsum, interactive=True),
            gr.Radio(choices=mangetbranchend, interactive=True),
            mangetbranchendname,
            gr.CheckboxGroup(value=[]),
            mangetbranchlist,
            mangetbranchmessages,
            status_msg,
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
            gr.Dropdown(choices=gettreenameforradio_names, value=gettreenameforradio_trg, interactive=True),
            gr.Dropdown(choices=mangetbranchend, interactive=True),
            gr.Dropdown(choices=branchnames, interactive=True)
            )
        return out
 
    def updateUIelements(self, prompt = ''):
        hide_tasks = False

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
        bud_msgs,
        sel_task,
        sel_cont
        ] = self.actioner.getCurrTaskPrompts2(set_prompt=prompt, hide_tasks=self.actioner.hide_task)

        maingraph = self.actioner.drawGraph(hide_tasks=True, out_childtask_max=1)
        stepgraph = self.actioner.drawGraph(max_index= 1, path = "output/img2", hide_tasks=True, max_childs=-1,add_linked=True, out_childtask_max=4)
        rawgraph = self.actioner.drawGraph(hide_tasks=True, max_childs=1, path="output/img3", all_tree_task=True, add_garlands=True, out_childtask_max=4)


        out = self.convToGradioUI(
                r_msgs, 
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
                bud_msgs,
                sel_task,
                sel_cont
        )


        out += (self.actioner.manager.getTreesList(True), maingraph, stepgraph, rawgraph)
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
                self.getActionerList()
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


 
    def getTextWindowFromCurrTask(self):
        man = self.actioner.manager
        text = man.curr_task.getLastMsgContent()
        text_len = len(text)
        wintext = min(200, text_len)
        slider_size = text_len - wintext
        out_text = text[0:wintext]
        return [
            gr.Number(value=wintext,maximum=text_len, interactive=True),
            gr.Slider(value=0, minimum=0,maximum=slider_size, interactive=True),
            gr.Textbox(value=out_text)
        ]
    
    def moveTextWindowFromCurrTask( self, winsz, slider_str ):
        man = self.actioner.manager
        text = man.curr_task.getLastMsgContent()
        text_len = len(text)
        wintext = min(winsz, text_len)
        out_text = text[slider_str:slider_str + wintext]
        return (
            gr.Textbox(value=out_text)
        )
 
    def changeTextWindowFromCurrTask( self, winsz, slider_str ):
        man = self.actioner.manager
        text = man.curr_task.getLastMsgContent()
        text_len = len(text)
        wintext = min(winsz, text_len)
        out_text = text[slider_str:slider_str + wintext]
        slider_size = text_len - wintext
        return (
            gr.Textbox(value=out_text),
            gr.Slider(value=slider_str, minimum=0,maximum=slider_size, interactive=True),
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
        man = act.manager
        selpath = Loader.Loader.getDirPathFromSystem()
        path = Loader.Loader.getUniPath(selpath)
        for task in man.getMultiSelectedTasks():
            task.saveAllParamsByPath(path)

        return "Done"
    
    def selectTargetActioner(self):
        self.trg_actioner = self.actioner
        return gr.Button(interactive=True)

    def moveMultiSelectedTasksFromTargetActioner( self ):
        act = self.trg_actioner
        cur_man = act.manager
        next_man = self.actioner.manager
        tasks = act.manager.getMultiSelectedTasks()
        for task in tasks:
                next_man.addTask(task)
                task.setManager(next_man)
                cur_man.rmvTask(task)
                task.saveAllParams()
        print('Move to ext actioner tasks:', [t.getName() for t in tasks])
        return gr.Button(interactive=False)
