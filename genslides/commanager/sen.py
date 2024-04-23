from genslides.task.base import TaskManager, BaseTask
from genslides.utils.savedata import SaveData
from genslides.utils.archivator import Archivator
from genslides.commanager.jun import Manager
from genslides.commanager.group import Actioner

from genslides.utils.reqhelper import RequestHelper
from genslides.utils.testrequest import TestRequester
from genslides.utils.searcher import GoogleApiSearcher
import genslides.utils.loader as Loader
import genslides.utils.filemanager as FileManager

from os import listdir
from os.path import isfile, join


import os
import json
import gradio as gr
import datetime

import genslides.utils.filemanager as fm
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

        self.resetManager(manager, load=False)
        # saver = SaveData()
        # saver.removeFiles()
        self.current_project_name = self.manager.getParam("current_project_name")
        if self.current_project_name is None:
            self.current_project_name = 'Unnamed'
        self.updateSessionName()
        self.actioner.clearTmp()

    def loadManager(self):
        self.resetManager(self.actioner.std_manager)
        if len(self.actioner.std_manager.task_list) == 0:
            return self.createNewTree()
        return self.actioner.updateUIelements()
    
    def loadManagerFromBrowser(self):
        # man_path = Loader.Loader.getFilePathFromSystemRaw(filetypes=[("Project File", "project.json")])
        man_path = Loader.Loader.getDirPathFromSystem()
        # files = FileManager.getFilesInFolder(man_path)
        # if 'project.json' in files:
            # man_path = man_path.parent
        man_path = Loader.Loader.getUniPath(man_path)
        self.actioner.std_manager.setPath(man_path)
        self.resetManager(manager = self.actioner.std_manager, path = man_path)
        if len(self.actioner.std_manager.task_list) == 0:
            self.createNewTree()
        self.actioner.loadTmpManagers()
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
        fm.deleteFiles(mypath)

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
    
    
    def save(self, name):
        self.current_project_name = name
        self.actioner.std_manager.setParam("current_project_name",self.current_project_name)

        # Archivator.saveOnlyFiles(self.savedpath, self.mypath, name)
        print('Save man', self.actioner.manager.getName(),'(Temp)' if self.actioner.manager != self.actioner.std_manager else '(Main)')
        path = self.actioner.manager.getPath()
        path = Loader.Loader.getUniPath(path)
        trg_path = Loader.Loader.getUniPath(Loader.Loader.getDirPathFromSystemRaw())
        Archivator.saveAll(path, trg_path, name)

        return gr.Dropdown( choices= self.loadList(), interactive=True)

   
    
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
        return ['change','resp2req','coll2req','read2req','in','out','link','av_cp','step','chckresp','sel2par','ignrlist','wishlist','upd_cp']
    
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
                param[name] = True if name in checks else False
            param['switch'] = []
            if 'resp2req' in checks:
                param['switch'].append({'src':'Response','trg':'Request'})
            if 'coll2req' in checks:
            # TODO: Если надо заменить задачу типа Collect, то меняем все типы задач Receive/Collect/GroupCollect
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
    
    def goToNextBranch(self):
        self.actioner.manager.goToNextBranch()
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
            self.actioner.manager = self.actioner.std_manager
        else:
            for man in self.actioner.tmp_managers:
                if man.getName() == name:
                    self.actioner.manager = man
                    break
        return self.actioner.updateTaskManagerUI()
    
    def switchToExtTaskManager(self):
        man = self.actioner.manager
        task_actioner = man.curr_task.getActioner()
        if task_actioner != None and self.tmp_actioner == None:
            self.tmp_actioner = self.actioner
            self.actioner = task_actioner
            print('Switch on actioner of', man.curr_task.getName())
            print('Path:', self.actioner.getPath())
            print('Man:', self.actioner.manager.getName())
            print('Tasks:',[t.getName() for t in self.actioner.manager.task_list])
        return self.actioner.updateTaskManagerUI()
    
    def backToDefaultActioner(self):
        if self.tmp_actioner != None:
            self.actioner = self.tmp_actioner
            self.tmp_actioner = None
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
        return self.actioner.resetUpdate()
       
    def update(self):
        return self.actioner.update()
        
    def updateAll(self):
        self.actioner.manager.disableOutput2()
        self.actioner.updateAll()
        self.actioner.manager.enableOutput2()
        return self.actioner.updateUIelements()
    
    def updateCurrentTree(self):
        self.actioner.manager.disableOutput2()
        self.actioner.updateCurrentTree()
        self.actioner.manager.enableOutput2()
        return self.actioner.updateUIelements()

   
    def updateAllUntillCurrTask(self):
        self.actioner.manager.disableOutput2()
        self.actioner.updateAllUntillCurrTask()
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
    
    def selectRowTasks(self):
        man = self.actioner.manager
        trg, child_idx = man.curr_task.getClosestBranching()
        tasks = trg.getChildSameRange(trg_idx=child_idx)
        for task in tasks:
            if task not in man.multiselect_tasks:
                man.multiselect_tasks.append(task)
        return self.actioner.updateUIelements()
    
    def selectTaskRowFromCurrent(self, child_idx):
        man = self.actioner.manager
        tasks = man.curr_task.getChildSameRange(trg_idx=child_idx)
        for task in tasks:
            if task not in man.multiselect_tasks:
                man.multiselect_tasks.append(task)
        return self.actioner.updateUIelements()


    def getParamFromMultiSelected(self, key):
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
            return {}, gr.Radio(choices=[]),'No param'
        
        return param, gr.Radio(choices=list(param.keys())), 'Diff tasks:\n' + ','.join(difftasknames)
    
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
        return self.actioner.updateTaskManagerUI()
