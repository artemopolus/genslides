from genslides.task.base import TaskManager, BaseTask
from genslides.utils.savedata import SaveData
from genslides.utils.archivator import Archivator
from genslides.commanager.jun import Manager
from genslides.commanager.group import Actioner

from genslides.utils.reqhelper import RequestHelper
from genslides.utils.testrequest import TestRequester
from genslides.utils.searcher import GoogleApiSearcher
import genslides.utils.loader as Loader

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
        return self.actioner.manager.getCurrTaskPrompts()
    
    def loadManagerFromBrowser(self):
        man_path = Loader.Loader.getDirPathFromSystem()
        self.actioner.std_manager.setPath(man_path)
        self.resetManager(manager = self.actioner.std_manager, path = man_path)
        if len(self.actioner.std_manager.task_list) == 0:
            return self.createNewTree()
        return self.actioner.manager.getCurrTaskPrompts()

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
        for f in listdir(mypath):
            f_path = join(mypath, f)
            if isfile(f_path):
                os.remove(f_path)
            else:
                shutil.rmtree(f_path)
    def clear(self):
        self.clearFiles()
        self.resetManager(self.manager, fast=False, load=False)

    def reload(self):
        self.resetManager(self.manager, fast=False, load=True)



    def getEvaluetionResults(self, input):
        print("In:", input)
        saver = SaveData()
        saver.updateEstimation(input)




    def load(self, filename):
        if filename == "":
            return ""
        self.clearFiles()
        path = self.actioner.manager.getPath()
        path = Loader.Loader.getUniPath(path)
        print('Load files to',path)
        project_path = Loader.Loader.getUniPath(self.mypath)
        Archivator.extractFiles(project_path, filename, path)
        self.resetManager(self.actioner.manager, path=self.actioner.getPath())
        self.current_project_name = filename
        self.actioner.manager.setParam("current_project_name",self.current_project_name)
        self.updateSessionName()
        return filename
    
    def appendProjectTasks(self, filename):
        tmp_manager = Manager(RequestHelper(), TestRequester(), GoogleApiSearcher())
        tmp_path = os.path.join(self.actioner.getPath(),'tmp', filename)
        print('Open file',filename,'from',self.mypath,'to',tmp_path)
        tmp_manager.initInfo(method = self.actioner.loadExtProject, task=None, path = tmp_path  )
        Archivator.extractFiles(self.mypath, filename, tmp_manager.getPath())
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
            idx = 0
            while (idx < 1000):
                ext_pr_name = 'pr' + str(idx)
                trg = os.path.join(manager.getPath(),'ext', ext_pr_name) +'/'
                if not os.path.exists(trg):
                    if Archivator.extractFiles(mypath, filename, trg):
                        self.ext_proj_names.append(ext_pr_name)
                        print('Append project',filename,'task to', trg)
                        return True, ext_pr_name
                idx += 1
        return False, ''
    
    
    def save(self, name):
        self.current_project_name = name
        self.actioner.std_manager.setParam("current_project_name",self.current_project_name)

        # Archivator.saveOnlyFiles(self.savedpath, self.mypath, name)
        print('Save man', self.actioner.manager.getName(),'(Temp)' if self.actioner.manager != self.actioner.std_manager else '(Main)')
        path = self.actioner.manager.getPath()
        path = Loader.Loader.getUniPath(path)
        trg_path = Loader.Loader.getUniPath(self.mypath)
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
        if custom_action in self.getStdCmdList():
            return self.makeTaskAction(prompt, custom_action, selected_action, "assistant")
        elif custom_action in self.getCustomCmdList():
            if selected_action == "New":
                return self.makeTaskAction(prompt, custom_action, "NewExtProject", "")
            elif selected_action == "SubTask":
                return self.makeTaskAction(prompt, custom_action, "SubExtProject", "")
            elif selected_action == "Insert":
                return self.makeTaskAction(prompt, custom_action, "InsExtProject", "")
        elif custom_action == 'Garland':
            self.makeTaskAction('', custom_action, selected_action, '')
        return self.manager.getCurrTaskPrompts()
    
    def makeResponseAction(self, prompt, selected_action, selected_tag):
        if selected_action == 'Edit':
            return self.makeTaskAction(prompt, "Response","Divide", selected_tag)
        else:
            return self.makeTaskAction("", "Response",selected_action, "assistant")
    
    def getParamListForEdit(self):
        # TODO: добавить простую копию задачи
        return ['resp2req','coll2req','read2req','in','out','link','step','change','chckresp','sel2par','ignrlist']
    
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
        return self.manager.createTreeOnSelectedTasks(action_type,'Garland')

    def createCollectTreeOnSelectedTasks(self, action_type):
        return self.manager.createTreeOnSelectedTasks(action_type,"Collect")
    
    def createShootTreeOnSelectedTasks(self, action_type):
        return self.manager.createTreeOnSelectedTasks(action_type,"GroupCollect")
    
    def makeTaskAction(self, prompt, type1, creation_type, creation_tag, param = {}, save_action = True):
        # TODO: Критическая проблема. Из-за вылетов программы может потеряться важный текст запроса, что может весьма расстроить, поэтому следует сохранять сообщение в проектный файл и передавать их пользователю по отдельному запросу через GUI
        return self.actioner.makeTaskAction(prompt, type1, creation_type, creation_tag, param , save_action)
        # return self.manager.getCurrTaskPrompts()
 

    def makeActionParent(self):
        man = self.actioner.manager
        if len(man.selected_tasks) == 0:
            return man.getCurrTaskPrompts()
        else:
            param = {'select': man.selected_tasks[0].getName()}
        return self.makeTaskAction("","","Parent","", param)
    
    def makeActionChild(self):
        man = self.actioner.manager
        if len(man.selected_tasks) == 0:
            return man.getCurrTaskPrompts()
        else:
            param = {'curr': man.selected_tasks[0].getName()}
        return self.makeTaskAction("","","Parent","", param)
    

    def makeActionUnParent(self):
        return self.makeTaskAction("","","Unparent","")
    

    def makeActionLink(self):
        man = self.actioner.manager
        if len(man.selected_tasks) == 0:
            return man.getCurrTaskPrompts()
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
        return man.getCurrTaskPrompts()

    
    def goToNextBranchEnd(self):
        return self.actioner.manager.goToNextBranchEnd()
    
    def goToNextBranch(self):
        return self.actioner.manager.goToNextBranch()
    
    def createNewTree(self):
        self.makeTaskAction("","SetOptions","New","user",[])
        self.actioner.manager.updateTreeArr()
        return self.actioner.manager.getCurrTaskPrompts()
    
    def goToNextTree(self):
        if self.actioner.manager != self.actioner.std_manager:
            self.actioner.manager.updateTreeArr(check_list=True)
        if self.actioner.manager != self.actioner.std_manager:
            self.actioner.manager.sortTreeOrder(check_list=True)
        else:
            self.actioner.manager.sortTreeOrder()
        return self.actioner.manager.goToNextTree()
        # return self.goToNextBranchEnd()
    
    def goBackByLink(self):
        man = self.actioner.manager
        task = man.curr_task
        trgs = task.getGarlandPart()
        if len(trgs) > 0:
            man.curr_task = trgs[0]
        return man.getCurrTaskPrompts()
    
    def goToNextChild(self):
        return self.actioner.manager.goToNextChild()
        # return self.makeTaskAction("","","GoToNextChild","")

    def goToParent(self):
        return self.actioner.manager.goToParent()
        # return self.makeTaskAction("","","GoToParent","")
    
    def moveToNextChild(self):
        self.actioner.manager.goToNextChild()
        return self.actioner.manager.getCurrTaskPrompts()
    
    def moveToParent(self):
        self.actioner.manager.curr_task.resetQueue()
        self.actioner.manager.goToParent()
        return self.actioner.manager.getCurrTaskPrompts()
    
    def moveToNextBranch(self):
        man = self.actioner.manager
        man.goToNextBranch()
        if man.curr_task.parent != None:
            trg = man.curr_task.parent
            man.curr_task = trg
        return man.getCurrTaskPrompts()

    def switchRole(self, role, prompt):
        task = self.actioner.manager.curr_task
        print('Set role[', role, ']for',task.getName())
        self.makeTaskAction(task.getLastMsgContent(), "Request", "Edit", role)
        return self.actioner.manager.getCurrTaskPrompts(prompt)
  
 
    def appendNewParamToTask(self, param_name):
        return self.makeTaskAction('','','AppendNewParam','', {'name':param_name})
    
    def removeParamFromTask(self, param_name):
        return self.makeTaskAction('','','RemoveTaskParam','', {'name':param_name})
    
    def setTaskKeyValue(self, param_name, key, slt_value, mnl_value):
        print('Set task key value:','|'.join([param_name,key,str(slt_value),str(mnl_value)]))
        return self.makeTaskAction('','','SetParamValue','', {'name':param_name,'key':key,'select':slt_value,'manual':mnl_value})
    
    def addTaskNewKeyValue(self, param_name, key, value):
        print('Set task key value:','|'.join([param_name,key,str(value)]))
        return self.makeTaskAction('','','SetParamValue','', {'name':param_name,'key':key,'select':value,'manual':''})
    
    def getMainCommandList(self):
        return self.manager.getMainCommandList()

    def getSecdCommandList(self):
        return self.manager.getSecdCommandList()
    

    def newExtProject(self, filename, prompt):
        return self.makeTaskAction(prompt,"New","NewExtProject","")
    def appendExtProject(self, filename, prompt):
        return self.makeTaskAction(prompt,"SubTask","SubExtProject","")
    

    def initPrivManager(self):
        print("Init empty private manager")
        man = self.actioner.manager
        tags = []
        for task in man.multiselect_tasks:
            code = task.getName()
            tags.append(code)
        self.makeTaskAction("","","InitPrivManager","", {'actions':[],'repeat':3, 'task_names':tags})
        out = self.actioner.manager.getCurrTaskPrompts()
        out += self.actioner.getTmpManagerInfo()
        return out
    
    def loadTmpManager(self, name):
        if self.actioner.std_manager.getName() == name:
            self.actioner.manager = self.actioner.std_manager
        else:
            for man in self.actioner.tmp_managers:
                if man.getName() == name:
                    self.actioner.manager = man
                    break
        out = self.actioner.manager.getCurrTaskPrompts()
        out += self.actioner.getTmpManagerInfo()
        return out
    
    def switchToExtTaskManager(self):
        man = self.actioner.manager
        if man.curr_task.getType() == 'ExtProject' and self.tmp_actioner == None:
            self.tmp_actioner = self.actioner
            self.actioner = man.curr_task.getActioner()
            print('Switch on actioner of', man.curr_task.getName())
            print('Path:', self.actioner.getPath())
            print('Man:', self.actioner.manager.getName())
            print('Tasks:',[t.getName() for t in self.actioner.manager.task_list])
        out = self.actioner.manager.getCurrTaskPrompts()
        out += self.actioner.getTmpManagerInfo()
        return out
    
    def backToDefaultActioner(self):
        if self.tmp_actioner != None:
            self.actioner = self.tmp_actioner
            self.tmp_actioner = None
        out = self.actioner.manager.getCurrTaskPrompts()
        out += self.actioner.getTmpManagerInfo()
        return out
 
    
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
        out = self.actioner.manager.getCurrTaskPrompts()
        out += self.actioner.getTmpManagerInfo()
        return out
  
    def rmvePrivManager(self):
        self.makeTaskAction("","","RmvePrivManager","")
        #TODO: Нужно разобраться почему так происходит и убрать этот костыль
        self.actioner.manager.fixTasks()
        out = self.actioner.manager.getCurrTaskPrompts()
        out += self.actioner.getTmpManagerInfo()
        return out
    
    def getPrivManager(self):
        return self.actioner.getTmpManagerInfo()

    def exeActions(self):
        # Закомментированной командой производится запись команды в список команд менеджера
        # self.makeTaskAction("","","ExecuteManager","")
        # Для исполнения команд нужна отдельная команда, чтобы не переводить это все в цикл
        self.actioner.exeActions()
        # Альтернатива
        # self.makeTaskAction("","","ExecuteManager","",{},save_action=False)
        out = self.actioner.manager.getCurrTaskPrompts()
        out += self.actioner.getTmpManagerInfo()
        return out
    
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
        return self.actioner.manager.curr_task.getTextInfo(param)
        

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
        return self.actioner.manager.getCurrTaskPrompts()

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
        return self.actioner.manager.getCurrTaskPrompts()

    def setTreeName(self, name : str):
        self.actioner.manager.curr_task.setBranchSummary(name)
        return self.actioner.manager.getCurrTaskPrompts()

    def goToTreeByName(self, name):
        return self.actioner.manager.goToTreeByName(name)

    def resetUpdate(self):
        return self.actioner.resetUpdate()
       
    def update(self):
        return self.actioner.update()
        
    def updateAll(self):
        self.actioner.manager.disableOutput2()
        self.actioner.updateAll()
        self.actioner.manager.enableOutput2()
        return self.actioner.manager.getCurrTaskPrompts()
    
    def updateCurrentTree(self):
        return self.actioner.updateCurrentTree()

   
    def updateAllUntillCurrTask(self):
        return self.actioner.updateAllUntillCurrTask()
   
    def setBranchEndName(self, summary):
        return self.actioner.manager.setBranchEndName(summary)

    
    def setCurrTaskByBranchEndName(self, name):
        return self.actioner.manager.setCurrTaskByBranchEndName( name)
    
    def cleanCurrTask(self):
        man = self.actioner.manager
        man.curr_task.forceCleanChat()
        return man.getCurrTaskPrompts()


    def relinkToCurrTaskByName(self, name):
        return self.makeTaskAction('','','RelinkToCurrTask','', {'name':name})
    
    def selectRelatedChain(self):
        return self.actioner.getRelationTasksChain()
    
    def selectNearestTasks(self):
        man = self.actioner.manager
        tasks = man.curr_task.getHoldGarlands()
        tasks.extend(man.curr_task.getGarlandPart())
        for task in tasks:
            if task not in man.multiselect_tasks:
                man.multiselect_tasks.append(task)
        return man.getCurrTaskPrompts()
       
    
    def deselectRealtedChain(self):
        self.actioner.manager.multiselect_tasks = []
        return self.actioner.manager.getCurrTaskPrompts()
    
    def appendTaskToChain(self):
        man = self.actioner.manager
        if man.curr_task not in man.multiselect_tasks:
            man.multiselect_tasks.append(man.curr_task)
        return man.getCurrTaskPrompts()
    
    def removeTaskFromChain(self):
        man = self.actioner.manager
        if man.curr_task in man.multiselect_tasks:
            man.multiselect_tasks.remove(man.curr_task)
        return man.getCurrTaskPrompts()
    
    def appendTreeToChain(self):
        man = self.actioner.manager
        tasks = man.curr_task.getTree()
        for task in tasks:
            if task not in man.multiselect_tasks:
                man.multiselect_tasks.append(task)
        return man.getCurrTaskPrompts()
    
    def removeTreeFromChain(self):
        man = self.actioner.manager
        tasks = man.curr_task.getTree()
        for task in tasks:
            if task in man.multiselect_tasks:
                man.multiselect_tasks.remove(task)
        return man.getCurrTaskPrompts()
   
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
                return man.getCurrTaskPrompts()
            if task not in man.multiselect_tasks:
                man.multiselect_tasks.append(task)
        return man.getCurrTaskPrompts()

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
        return man.getCurrTaskPrompts()


    def appendBranchtoChain(self):
        man = self.actioner.manager
        buds = man.curr_task.getAllBuds()
        bud = buds.pop()
        tasks = bud.getAllParents()
        for task in tasks:
            if task not in man.multiselect_tasks:
                man.multiselect_tasks.append(task)
        return man.getCurrTaskPrompts()
 
    def removeBranchFromChain(self):
        man = self.actioner.manager
        buds = man.curr_task.getAllBuds()
        bud = buds.pop()
        tasks = bud.getAllParents()
        for task in tasks:
            if task in man.multiselect_tasks:
                man.multiselect_tasks.remove(task)
        return man.getCurrTaskPrompts()
   
    def appendChildsToChain(self):
        man = self.actioner.manager
        tasks = man.curr_task.getAllChildChains()
        for task in tasks:
            if task not in man.multiselect_tasks:
                man.multiselect_tasks.append(task)
        return man.getCurrTaskPrompts()
 
    def removeChildsFromChain(self):
        man = self.actioner.manager
        tasks = man.curr_task.getAllChildChains()
        for task in tasks:
            if task in man.multiselect_tasks:
                man.multiselect_tasks.remove(task)
        return man.getCurrTaskPrompts()

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
