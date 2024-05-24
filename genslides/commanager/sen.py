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

        self.resetManager(manager, load=False)
        # saver = SaveData()
        # saver.removeFiles()
        self.current_project_name = self.manager.getParam("current_project_name")
        if self.current_project_name is None:
            self.current_project_name = 'Unnamed'
        self.updateSessionName()
        self.actioner.clearTmp()

        self.exttreemanbudinfo = None

    def loadManager(self):
        self.resetManager(self.actioner.std_manager)
        if len(self.actioner.std_manager.task_list) == 0:
            return self.createNewTree()
        return self.actioner.updateUIelements()
    
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
        return self.actioner.updateUIelements()

    def resetManager(self, manager : Manager, fast = True, load = True, path = 'saved'):
        if self.actioner is None:
            self.actioner = Actioner(manager)
        else:
            self.actioner.reset()
        self.actioner.setPath(path)
        self.manager = self.actioner.std_manager
        self.manager.onStart()
        self.manager.initInfo(self.loadExtProject, path = self.actioner.getPath())
        if load:
            self.manager.disableOutput2()
            self.manager.loadTasksList(fast)
            self.manager.enableOutput2()
            self.actioner.loadTmpManagers()
 

# сохранение сессионных имен необходимо связать только с проектером сеном, а не с менеджером
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
        path = Loader.Loader.getUniPath( Finder.findByKey("[[manager:path:spc]]", man, man.curr_task, man.helper ) )
        folder = Finder.findByKey("[[manager:path:fld]]", man, man.curr_task, man.helper )
        name = Finder.findByKey("[[manager:path:spc:name]]", man, man.curr_task, man.helper )
        fld_path = Loader.Loader.getUniPath( FileManager.addFolderToPath(folder, ["tt_temp"]))
        FileManager.createFolder(fld_path)
        trg_path = Loader.Loader.getUniPath( FileManager.addFolderToPath(folder, ["tt_temp",name + ".7z"]))
        Archivator.saveAllbyPath(data_path=path, trgfile_path=trg_path)

    def loadFromTmp(self):
        self.actioner.setManager(self.actioner.std_manager)
        man = self.actioner.manager
        folder = Finder.findByKey("[[manager:path:fld]]", man, man.curr_task, man.helper )
        filename = Finder.findByKey("[[manager:path:spc:name]]", man, man.curr_task, man.helper )
        fld_path = Loader.Loader.getUniPath( FileManager.addFolderToPath(folder, ["tt_temp"]))
        path = Loader.Loader.getUniPath( Finder.findByKey("[[manager:path:spc]]", man, man.curr_task, man.helper ) )


        self.clearFiles()

        project_path = fld_path

        Archivator.extractFiles(project_path, filename, path)
        self.resetManager(self.actioner.manager, path=self.actioner.getPath())
        return self.actioner.updateTaskManagerUI()

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

        return gr.Dropdown( choices= self.loadList(), interactive=True)
    
    def saveTmpMan(self):
        if self.actioner.manager == self.actioner.std_manager:
            return
        print(f"Save {self.actioner.manager.getName()} tmp manager")
        path = Loader.Loader.getUniPath(self.actioner.manager.getPath())
        trg_path = Loader.Loader.getUniPath(Archivator.getProjectFileName())
        Archivator.saveAllbyPath(data_path=path, trgfile_path=trg_path)
       

   
    
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
        mypath = 'tools'
        return [f.split('.')[0] for f in listdir(mypath) if isfile(join(mypath, f))]
    
    def getFullCmdList(self):
        a = self.getCustomCmdList()
        p = self.getStdCmdList()
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
        return self.actioner.updateUIelements()
    
    def makeResponseAction(self, prompt, selected_action, selected_tag):
        if selected_action == 'Edit':
            return self.makeTaskAction(prompt, "Response","Divide", selected_tag)
        else:
            return self.makeTaskAction("", "Response",selected_action, "assistant")
    
    def getParamListForEdit(self):
        # TODO: добавить простую копию задачи
        return ['change', #Копировать ветвь
                'resp2req','coll2req','read2req', #конвертировать задачи этого типа в другой
                'in','out','link','av_cp', #Параметры ветвления
                'step','chckresp',
                'sel2par', # Копировать и ветвиться от выбранной задачи
                'ignrlist',
                'wishlist', #
                'upd_cp', #Обновить ветки, которые скопирован ранее через Edit
                'onlymulti', #Копировать только мультивыбранные задачи
                'reqSraw', #Конвертировать ссылки в сообщениях при копировании
                'forcecopyresp' #Насильно вставлять промпт в Response
                ]
    
    def makeRequestAction(self, prompt, selected_action, selected_tag, checks):
        print('Make',selected_action,'Request')
        act_type = ""
        param = {}
        if selected_action == "New" or selected_action == "SubTask" or selected_action == "Insert":
            act_type = "Request"
            selected_tag = "user"
            return self.makeTaskAction(prompt=prompt,type1= act_type,creation_type= selected_action,creation_tag= selected_tag, param=param)
        elif selected_action == "Edit":
            act_type = "Request"
        if len(checks) > 0:
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
        print('Action param=', param)
        return self.makeTaskAction(prompt=prompt,type1= act_type,creation_type= selected_action,creation_tag= selected_tag, param=param)

    def createGarlandOnSelectedTasks(self, action_type):
        self.manager.createTreeOnSelectedTasks(action_type,'Garland')
        return self.actioner.updateUIelements()

    def createCollectTreeOnSelectedTasks(self, action_type):
        self.manager.createTreeOnSelectedTasks(action_type,"Collect")
        return self.actioner.updateUIelements()
    
    def createShootTreeOnSelectedTasks(self, action_type):
        self.manager.createTreeOnSelectedTasks(action_type,"GroupCollect")
        return self.actioner.updateUIelements()
    
    def makeTaskAction(self, prompt, type1, creation_type, creation_tag, param = {}, save_action = True):
        # TODO: Критическая проблема. Из-за вылетов программы может потеряться важный текст запроса, что может весьма расстроить, поэтому следует сохранять сообщение в проектный файл и передавать их пользователю по отдельному запросу через GUI
        self.actioner.makeTaskAction(prompt, type1, creation_type, creation_tag, param , save_action)
        return self.actioner.updateUIelements()
        # return self.manager.getCurrTaskPrompts()
 

    def makeActionParent(self):
        man = self.actioner.manager
        if len(man.selected_tasks) == 0:
            return self.actioner.updateUIelements()
        else:
            param = {'select': man.selected_tasks[0].getName()}
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
        return self.actioner.updateUIelements()

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
        return self.actioner.updateUIelements()


    
    def makeActionChild(self):
        man = self.actioner.manager
        if len(man.selected_tasks) == 0:
            return self.actioner.updateUIelements()
        else:
            param = {'curr': man.selected_tasks[0].getName()}
        return self.makeTaskAction("","","Parent","", param)
    

    def makeActionUnParent(self):
        return self.makeTaskAction("","","Unparent","")
    

    def makeActionLink(self):
        man = self.actioner.manager
        if len(man.selected_tasks) == 0:
            return self.actioner.updateUIelements()
        else:
            param = {'select': man.selected_tasks[0].getName()}
        return self.makeTaskAction("","","Link","", param)
 
    def makeActionRevertLink(self):
        man = self.actioner.manager
        if len(man.selected_tasks) == 0:
            return man.getCurrTaskPrompts()
        else:
            param = {'curr': man.selected_tasks[0].getName()}
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
        return self.actioner.updateUIelements()

    
    def goToNextBranchEnd(self):
        self.actioner.manager.goToNextBranchEnd()
        return self.actioner.updateUIelements()
    
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
        return self.actioner.updateUIelements()
    
    def goToNextBranch(self):
        self.actioner.manager.goToNextBranch()
        return self.actioner.updateUIelements()
    
    def goToBranchFork(self):
        man = self.actioner.manager
        _, trg = man.getBranchFork(start_task=man.curr_task)
        man.curr_task = trg
        return self.actioner.updateUIelements()
    
    def createNewTree(self):
        self.makeTaskAction("","SetOptions","New","user",[])
        self.actioner.manager.updateTreeArr()
        return self.actioner.updateUIelements()
    
    def goToNextTree(self):
        if self.actioner.manager != self.actioner.std_manager:
            self.actioner.manager.sortTreeOrder(check_list=True)
        else:
            self.actioner.manager.sortTreeOrder()
        self.actioner.manager.goToNextTree()
        return self.actioner.updateUIelements()
    
    def goBackByLink(self):
        man = self.actioner.manager
        task = man.curr_task
        trgs = task.getGarlandPart()
        if len(trgs) > 0:
            man.curr_task = trgs[0]
        return self.actioner.updateUIelements()
    
    def goToNextChild(self):
        self.actioner.manager.goToNextChild()
        return self.actioner.updateUIelements()
        # return self.makeTaskAction("","","GoToNextChild","")

    def goToParent(self):
        self.actioner.manager.goToParent()
        return self.actioner.updateUIelements()
        # return self.makeTaskAction("","","GoToParent","")

    def goToHalfBranch(self):
        cur = self.actioner.manager.curr_task
        tasks = cur.getAllParents()
        idx = int(len(tasks)/2)
        self.actioner.manager.curr_task = tasks[idx]
        return self.actioner.updateUIelements()
    
    def moveToNextChild(self):
        self.actioner.manager.goToNextChild()
        return self.actioner.updateUIelements()
    
    def moveToParent(self):
        # self.actioner.manager.curr_task.resetQueue()
        self.actioner.manager.goToParent()
        return self.actioner.updateUIelements()
    
    def moveToNextBranch(self):
        man = self.actioner.manager
        man.goToNextBranch()
        if man.curr_task.parent != None:
            trg = man.curr_task.parent
            man.curr_task = trg
        return self.actioner.updateUIelements()

    def switchRole(self, role, prompt):
        task = self.actioner.manager.curr_task
        print('Set role[', role, ']for',task.getName())
        self.makeTaskAction(task.getLastMsgContent(), "Request", "Edit", role)
        return self.actioner.updateUIelements(prompt=prompt)
  
 
    def appendNewParamToTask(self, param_name):
        self.makeTaskAction('','','AppendNewParam','', {'name':param_name})
        return self.actioner.updateTaskManagerUI()
    
    def removeParamFromTask(self, param_name):
        self.makeTaskAction('','','RemoveTaskParam','', {'name':param_name})
        return self.actioner.updateTaskManagerUI()
    
    def setTaskKeyValue(self, param_name, key, slt_value, mnl_value):
        print('Set task key value:','|'.join([param_name,key,str(slt_value),str(mnl_value)]))
        self.makeTaskAction('','','SetParamValue','', {'name':param_name,'key':key,'select':slt_value,'manual':mnl_value})
        return self.actioner.updateTaskManagerUI()
    
    def addTaskNewKeyValue(self, param_name, key, value):
        print('Set task key value:','|'.join([param_name,key,str(value)]))
        self.makeTaskAction('','','SetParamValue','', {'name':param_name,'key':key,'select':value,'manual':''})
        return self.actioner.updateTaskManagerUI()
    
    def getMainCommandList(self):
        return self.manager.getMainCommandList()

    def getSecdCommandList(self):
        return self.manager.getSecdCommandList()
    

    def newExtProject(self, filename, prompt):
        self.makeTaskAction(prompt,"New","NewExtProject","")
        return self.actioner.updateTaskManagerUI()

    def appendExtProject(self, filename, prompt):
        self.makeTaskAction(prompt,"SubTask","SubExtProject","")
        return self.actioner.updateTaskManagerUI()
    

    def initPrivManager(self):
        print("Init empty private manager")
        man = self.actioner.manager
        tags = []
        for task in man.multiselect_tasks:
            code = task.getName()
            tags.append(code)
        self.makeTaskAction("","","InitPrivManager","", {'actions':[],'repeat':3, 'task_names':tags})
        return self.actioner.updateTaskManagerUI()
    
    def loadTmpManager(self, name):
        if self.actioner.std_manager.getName() == name:
            self.actioner.setManager(self.actioner.std_manager)
        else:
            for man in self.actioner.tmp_managers:
                if man.getName() == name:
                    self.actioner.setManager(man)
                    break
        return self.actioner.updateTaskManagerUI()
    
    def switchToExtTaskManager(self):
        man = self.actioner.manager
        task_actioner = man.curr_task.getActioner()
        if task_actioner != None and self.tmp_actioner == None:
            self.tmp_actioner_task = man.curr_task
            self.tmp_actioner = self.actioner
            self.actioner = task_actioner
            self.actioner.loadStdManagerTasks()
            print('Switch on actioner of', man.curr_task.getName())
            print('Path:', self.actioner.getPath())
            print('Man:', self.actioner.manager.getName())
            # print('Tasks:',[t.getName() for t in self.actioner.manager.task_list])
        return self.actioner.updateTaskManagerUI()
    
    def backToDefaultActioner(self):
        if self.tmp_actioner != None:
            self.actioner = self.tmp_actioner
            self.tmp_actioner = None
            self.tmp_actioner_task = None
        return self.actioner.updateTaskManagerUI()
 
    
    def initSavdManagerToCur(self,name):
        self.makeTaskAction("","","InitSavdManagerToCur","", {'task': name})
        return self.actioner.getTmpManagerInfo()
 
    
    def loadPrivManager(self, name):
        self.makeTaskAction("","","InitSavdManager","", {'task': name})
        return self.actioner.getTmpManagerInfo()
    
    def savePrivManToTask(self):
        self.makeTaskAction("","","SavePrivManToTask","")
        return self.actioner.getTmpManagerInfo()
   
    def stopPrivManager(self):
        self.makeTaskAction("","","StopPrivManager","")
        #TODO: Нужно разобраться почему так происходит и убрать этот костыль
        self.actioner.manager.fixTasks()
        return self.actioner.updateTaskManagerUI()
  
    def rmvePrivManager(self):
        self.makeTaskAction("","","RmvePrivManager","")
        #TODO: Нужно разобраться почему так происходит и убрать этот костыль
        self.actioner.manager.fixTasks()
        return self.actioner.updateTaskManagerUI()
    
    def getPrivManager(self):
        return self.actioner.getTmpManagerInfo()

    def exeActions(self):
        # Закомментированной командой производится запись команды в список команд менеджера
        # self.makeTaskAction("","","ExecuteManager","")
        # Для исполнения команд нужна отдельная команда, чтобы не переводить это все в цикл
        self.actioner.exeActions()
        # Альтернатива
        # self.makeTaskAction("","","ExecuteManager","",{},save_action=False)
        return self.actioner.updateTaskManagerUI()
    
    def exeSmplScript(self):
        self.actioner.exeCurManagerSmpl()
        return self.actioner.getTmpManagerInfo()

    def editParamPrivManager(self, param):
        self.makeTaskAction("","","EditPrivManager","",param)
        return self.actioner.getTmpManagerInfo()

    def actionTypeChanging(self, action):
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
            return (self.actioner.manager.getCurTaskLstMsgRaw(), 
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
        return self.actioner.getTmpManagerInfo()
    
    def setCurrAsManagerStartTask(self):
        name = self.actioner.manager.curr_task.getName()
        return self.setManagerStartTask(name)
    
    def backToStartTask(self):
        manager = self.actioner.manager
        task = manager.getTaskByName(manager.getName())
        manager.curr_task = task
        return self.actioner.updateUIelements()

    def setCurrentExtTaskOptions(self, names : list):
        self.makeTaskAction("","","SetCurrentExtTaskOptions","", {'names': names})
        return self.actioner.getTmpManagerInfo()

    def resetAllExtTaskOptions(self):
        self.makeTaskAction("","","ResetAllExtTaskOptions","", {})
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

    def copyChainStepped(self):
        print('Copy chain stepped')
        # tasks_chains = self.actioner.manager.curr_task.getTasksFullLinks({'in':True, 'out':True,'link':True})
        # self.actioner.manager.copyTasksByInfo(tasks_chains=tasks_chains,edited_prompt='test', change_prompt=True, trg_type_t='', src_type_t='')
        self.actioner.manager.copyTasksByInfoStep()
        return self.actioner.updateUIelements()

    def setTreeName(self, name : str):
        self.actioner.manager.curr_task.setBranchSummary(name)
        return self.actioner.updateUIelements()

    def goToTreeByName(self, name):
        self.actioner.manager.goToTreeByName(name)
        return self.actioner.updateUIelements()

    def resetUpdate(self):
        self.actioner.resetUpdate()
        return self.actioner.updateUIelements()
       
    def update(self):
        self.actioner.update()
        return self.actioner.updateUIelements()
        
    def updateAll(self, check = False):
        print('Update All trees stepped')
        self.actioner.manager.disableOutput2()
        self.actioner.updateAll(force_check=check)
        self.actioner.manager.enableOutput2()
        return self.actioner.updateUIelements()
    
    def updateCurrentTree(self):
        self.actioner.manager.disableOutput2()
        self.actioner.updateCurrentTree()
        self.actioner.manager.enableOutput2()
        return self.actioner.updateUIelements()

   
    def updateAllUntillCurrTask(self, force_check = False):
        self.actioner.manager.disableOutput2()
        self.actioner.updateAllUntillCurrTask(force_check=force_check)
        self.actioner.manager.enableOutput2()
        return self.actioner.updateUIelements()
   
    def setBranchEndName(self, summary):
        self.actioner.manager.setBranchEndName(summary)
        return self.actioner.updateUIelements()

    
    def setCurrTaskByBranchEndName(self, name):
        self.actioner.manager.setCurrTaskByBranchEndName( name)
        return self.actioner.updateUIelements()
    
    def cleanCurrTask(self):
        man = self.actioner.manager
        man.curr_task.forceCleanChat()
        return self.actioner.updateUIelements()


    def relinkToCurrTaskByName(self, name):
        return self.makeTaskAction('','','RelinkToCurrTask','', {'name':name})
    
    def selectRelatedChain(self):
        man = self.actioner.manager
        taskchainnames = man.getRelatedTaskChains(man.curr_task.getName(), man.getPath())
        for name in taskchainnames:
            man.multiselect_tasks.append(man.getTaskByName(name))
        # return self.actioner.getRelationTasksChain()
        return self.actioner.updateUIelements()
    
    def selectNearestTasks(self):
        man = self.actioner.manager
        tasks = man.curr_task.getHoldGarlands()
        tasks.extend(man.curr_task.getGarlandPart())
        for task in tasks:
            if task not in man.multiselect_tasks:
                man.multiselect_tasks.append(task)
        return self.actioner.updateUIelements()
       
    
    def deselectRealtedChain(self):
        self.actioner.manager.multiselect_tasks = []
        return self.actioner.updateUIelements()
    
    def appendTaskToChain(self):
        man = self.actioner.manager
        if man.curr_task not in man.multiselect_tasks:
            man.multiselect_tasks.append(man.curr_task)
        return self.actioner.updateUIelements()
    
    def removeTaskFromChain(self):
        man = self.actioner.manager
        if man.curr_task in man.multiselect_tasks:
            man.multiselect_tasks.remove(man.curr_task)
        return self.actioner.updateUIelements()
    
    def appendTreeToChain(self):
        man = self.actioner.manager
        tasks = man.curr_task.getTree()
        for task in tasks:
            if task not in man.multiselect_tasks:
                man.multiselect_tasks.append(task)
        return self.actioner.updateUIelements()
    
    def removeTreeFromChain(self):
        man = self.actioner.manager
        tasks = man.curr_task.getTree()
        for task in tasks:
            if task in man.multiselect_tasks:
                man.multiselect_tasks.remove(task)
        return self.actioner.updateUIelements()
   
    def appendBranchPartToChain(self):
        man = self.actioner.manager
        tasks = man.curr_task.getAllChildChains()
        for task in tasks:
            if task not in man.multiselect_tasks:
                man.multiselect_tasks.append(task)
        tasks = man.curr_task.getAllParents()
        while(len(tasks)):
            task = tasks.pop(-1)
            if len(task.getChilds()) > 1 or task.isRootParent():
                return self.actioner.updateUIelements()
            if task not in man.multiselect_tasks:
                man.multiselect_tasks.append(task)
        return self.actioner.updateUIelements()

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
                return man.getCurrTaskPrompts()
            if task in man.multiselect_tasks:
                man.multiselect_tasks.remove(task)
        return self.actioner.updateUIelements()


    def appendBranchtoChain(self):
        man = self.actioner.manager
        buds = man.curr_task.getAllBuds()
        bud = buds.pop()
        tasks = bud.getAllParents()
        for task in tasks:
            if task not in man.multiselect_tasks:
                man.multiselect_tasks.append(task)
        return self.actioner.updateUIelements()
 
    def removeBranchFromChain(self):
        man = self.actioner.manager
        buds = man.curr_task.getAllBuds()
        bud = buds.pop()
        tasks = bud.getAllParents()
        for task in tasks:
            if task in man.multiselect_tasks:
                man.multiselect_tasks.remove(task)
        return self.actioner.updateUIelements()
   
    def appendChildsToChain(self):
        man = self.actioner.manager
        tasks = man.curr_task.getAllChildChains()
        for task in tasks:
            if task not in man.multiselect_tasks:
                man.multiselect_tasks.append(task)
        return self.actioner.updateUIelements()
 
    def removeChildsFromChain(self):
        man = self.actioner.manager
        tasks = man.curr_task.getAllChildChains()
        for task in tasks:
            if task in man.multiselect_tasks:
                man.multiselect_tasks.remove(task)
        return self.actioner.updateUIelements()
    
    def removeParentsFromChain(self):
        man = self.actioner.manager
        tasks = man.curr_task.getAllParents()
        tasks.remove(man.curr_task)
        for task in tasks:
            if task in man.multiselect_tasks:
                man.multiselect_tasks.remove(task)
        return self.actioner.updateUIelements()

    def selectRowTasks(self):
        man = self.actioner.manager
        trg, child_idx = man.curr_task.getClosestBranching()
        tasks = trg.getChildSameRange(trg_idx=child_idx)
        for task in tasks:
            if task in man.task_list and task not in man.multiselect_tasks:
                man.multiselect_tasks.append(task)
        return self.actioner.updateUIelements()
    
    def selectCopyBranch(self):
        man = self.actioner.manager
        tasks = man.getCopyBranch(man.curr_task)
        for task in tasks:
            if task in man.task_list and task not in man.multiselect_tasks:
                man.multiselect_tasks.append(task)
        return self.actioner.updateUIelements()

    def selectCopyTasks(self):
        man = self.actioner.manager
        tasks = man.getCopyTasks(man.curr_task)
        for task in tasks:
            if task in man.task_list and task not in man.multiselect_tasks:
                man.multiselect_tasks.append(task)
        return self.actioner.updateUIelements()
   
    def selectTaskRowFromCurrent(self, child_idx):
        man = self.actioner.manager
        tasks = man.curr_task.getChildSameRange(trg_idx=child_idx)
        for task in tasks:
            if task not in man.multiselect_tasks:
                man.multiselect_tasks.append(task)
        return self.actioner.updateUIelements()


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
        for task in man.multiselect_tasks:
            man.addTaskToSelectList(task)
            man.curr_task = trg
            self.createGarlandOnSelectedTasks('Insert')
            trg = man.curr_task
        man.curr_task = start
        return self.actioner.updateUIelements()

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
        return self.actioner.updateUIelements()

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
        return self.actioner.updateUIelements()

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
        return self.actioner.updateUIelements()

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
        return self.actioner.updateUIelements()

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

    def getTaskKeys(self, param_name):
        return self.actioner.manager.getTaskKeys(param_name)

    def getTaskKeyValue(self, param_name, param_key):
        return self.actioner.manager.getTaskKeyValue(param_name, param_key)
    
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
        if task.checkType( 'Response'):
            task.forceCleanChat()
            task.freezeTask()
        return self.actioner.updateUIelements()

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
            return self.actioner.updateUIelements()
        if len(task.getParent().getChilds()) < 2:
            return self.actioner.updateUIelements()
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
        return self.actioner.updateUIelements()
    
    def moveBranchIdxDw(self):
        man = self.actioner.manager
        task = man.curr_task
        if task.getParent() == None:
            return self.actioner.updateUIelements()
        if len(task.getParent().getChilds()) < 2:
            return self.actioner.updateUIelements()
        idx = task.getPrio()
        length = len(task.getParent().getChilds())

        if idx < length - 1:
            task.getParent().getChilds()[idx + 1].setPrio(idx)
            task.setPrio(idx + 1)
        return self.actioner.updateUIelements()
    
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
        return self.actioner.updateUIelements()
 
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
        return self.actioner.updateUIelements()

 
    def addCurrTaskToSelectList(self):
        return self.actioner.manager.addCurrTaskToSelectList()

    def getRelationBack(self, range):
        man = self.actioner.manager
        taskchainnames = man.getRelatedTaskChains(man.curr_task.getName(), man.getPath(), max_idx=range)
        for name in taskchainnames:
            man.multiselect_tasks.append(man.getTaskByName(name))
        return self.actioner.updateUIelements()

    def getRalationForward(self, range):
        man = self.actioner.manager
        man.getForwardRelatedTaskChain(man.curr_task, range)
        return self.actioner.updateUIelements()
    
    def setCurrentTaskByName(self, name):
        self.actioner.manager.setCurrentTaskByName(name)
        return self.actioner.updateUIelements()
    

    def setCurManagerColor(self, color):
        print('Set color', color,'to',self.actioner.manager.getName())
        self.actioner.manager.info['color'] = color
        self.actioner.manager.saveInfo()

    def setCurManagerName(self, name):
        self.actioner.manager.setName(name)
        self.actioner.manager.saveInfo()
        return self.actioner.updateTaskManagerUI()
    
    def addMultiSelectTasksFromStdMan(self):
        if self.actioner.manager != self.actioner.std_manager:
            self.actioner.addExtTasksForManager(self.actioner.manager, self.actioner.std_manager.multiselect_tasks)
        return self.actioner.updateTaskManagerUI()

    def rmvMultiSelectTasksFromTmpMan(self):
        if self.actioner.manager != self.actioner.std_manager:
            self.actioner.rmvExtTasksForManager(self.actioner.manager, self.actioner.manager.multiselect_tasks)
        return self.actioner.updateTaskManagerUI()

    def moveTaskToStdMan(self):
        if self.actioner.manager != self.actioner.std_manager:
            self.actioner.moveTaskFromManagerToAnother(tasks= self.actioner.manager.multiselect_tasks, 
                                                       cur_man= self.actioner.manager,
                                                       next_man= self.actioner.std_manager,
                                                       to_std=True)
        return self.actioner.updateTaskManagerUI()

    def moveTaskToTmpMan(self):
        if self.actioner.manager != self.actioner.std_manager:
            task_to_copy = self.actioner.std_manager.multiselect_tasks.copy()
            self.actioner.std_manager.multiselect_tasks = []
            self.actioner.moveTaskFromManagerToAnother(tasks=task_to_copy, 
                                                       cur_man=self.actioner.std_manager,
                                                       next_man=self.actioner.manager
                                                       )
        return self.actioner.updateTaskManagerUI()

    def moveTaskTmpToTmp(self, name):
        if self.actioner.manager == self.actioner.std_manager:
            return self.actioner.updateTaskManagerUI()
        if self.actioner.std_manager.getName() == name:
            return self.actioner.updateTaskManagerUI()
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
        return self.actioner.updateTaskManagerUI()
    
    def loadManagerInfoForExtWithBrowser(self):
        path = Loader.Loader.getDirPathFromSystem(self.actioner.manager.getPath())
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
        return self.addOutExtTreeInfo(start_inext, man.curr_task.getName())
    
    def addOutExtTreeInfo(self, start_inext,  task_name):
        extbrjson = start_inext
        extbrjson['target'] = task_name
        return json.dumps(extbrjson, indent=1)
    
    def addInExtTreeSubTask(self, params):
        man = self.actioner.manager
        man.createOrAddTask('','InExtTree','user',man.curr_task, [json.loads(params)])
        return self.actioner.updateUIelements()
    
    def addOutExtTreeSubTask(self, params):
        if self.tmp_actioner_task != None:
            man = self.tmp_actioner_task.getManager()
            if self.tmp_actioner_task.checkType('InExtTree'):
                man.createOrAddTask('','OutExtTree','user',man.curr_task, [params])
        # return self.actioner.updateUIelements()
    
    def getExtTreeParamsForEdit(self):
        if self.tmp_actioner_task != None:
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
        pyperclip.copy(text)
        pyperclip.paste()

    def copyToClickBoardDialRaw(self):
        msgs = self.actioner.manager.curr_task.getRawMsgs()
        text = ""
        for msg in msgs:
            text += msg['role'] + '\n' + 10*'====' + '\n\n\n'
            text += msg['content'] + '\n'
        pyperclip.copy(text)
        pyperclip.paste()

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

    

    def copyToClickBoardTokens(self):
        tokens, price = self.actioner.manager.curr_task.getCountPrice()
        text  = 'Tokens: ' + str(tokens) + ' price: ' + str(price)
        pyperclip.copy(text)
        pyperclip.paste()
           
