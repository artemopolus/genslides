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
        self.update_state = 'init'

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
        print('Load files to',self.savedpath)
        Archivator.extractFiles(self.mypath, filename, self.savedpath)
        self.manager.onStart() 
        self.manager.loadTasksList()
        self.current_project_name = filename
        self.manager.setParam("current_project_name",self.current_project_name)
        self.updateSessionName()
        return filename
    
    def appendProjectTasks(self, filename):
        tmp_manager = Manager(RequestHelper(), TestRequester(), GoogleApiSearcher())
        tmp_path = os.path.join('saved','tmp', filename)
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
        self.manager.setParam("current_project_name",self.current_project_name)

        # Archivator.saveOnlyFiles(self.savedpath, self.mypath, name)
        Archivator.saveAll(self.savedpath, self.mypath, name)

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
        elif custom_action == 'Garland':
            self.makeTaskAction('', custom_action, selected_action, '')
        return self.manager.getCurrTaskPrompts()
    
    def makeResponseAction(self, selected_action):
        return self.makeTaskAction("", "Response",selected_action, "assistant")
    
    def getParamListForEdit(self):
        return ['resp2req','coll2req','in','out','link','step','change','chckresp']
    
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
    
    def createNewTree(self):
        return self.makeTaskAction("","SetOptions","New","user",[])
    
    def goToNextTree(self):
        self.actioner.manager.sortTreeOrder()
        self.actioner.manager.goToNextTree()
        return self.goToNextBranchEnd()
    
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
        print('Set task key value:','|'.join([param_name,key,str(slt_value),str(mnl_value)]))
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
                    gr.Button(value='',interactive=False), 
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


    def updateInit(self):
        man = self.actioner.manager
        man.sortTreeOrder()
        self.update_state = 'start tree'
        self.update_tree_idx = 0

    def updateStepInternal(self):
        man = self.actioner.manager
        next = man.updateSteppedSelectedInternal()

        if next is None:
            self.update_state = 'next tree'
        elif self.root_task_tree == next:
            self.update_state = 'next tree'
            # print('Complete tree', self.root_task_tree.getName())
        else:
            self.update_state = 'step'
            self.update_processed_chain.append(next.getName())

        if len(next.getChilds()) == 0:
            print('Branch complete:', self.root_task_tree.getName(), '-', next.getName())

    def resetUpdate(self):
        self.update_state = 'init'
        man = self.actioner.manager
        man.curr_task = man.tree_arr[0]
        for task in man.tree_arr:
            task.resetTreeQueue()
        return man.getCurrTaskPrompts()

       
    def update(self):
        man = self.actioner.manager
        # print('Curr state:', self.update_state,'|task:',man.curr_task.getName())
        if self.update_state == 'init':
            self.updateInit()
        elif self.update_state == 'start tree':
            task = man.tree_arr[self.update_tree_idx]
            # print('Start tree', task.getName(),'[',self.update_tree_idx,']')
            self.root_task_tree = task
            man.curr_task = task
            # man.curr_task.resetTreeQueue()
            self.update_processed_chain = [self.root_task_tree.getName()]
            self.updateStepInternal()
        elif self.update_state == 'step':
            self.updateStepInternal()
                # self.root_task_tree = next
        elif self.update_state == 'next tree':
            if self.update_tree_idx + 1 < len(man.tree_arr):
                self.update_tree_idx += 1
                self.update_state = 'start tree'
            else:
                self.update_state = 'done'
                self.update_tree_idx = 0

        # cnt = 0
        # for task in man.task_list:
        #     if task.is_freeze:
        #         cnt += 1
        # print('Frozen tasks cnt:', cnt)
        out = man.getCurrTaskPrompts()
        return out

    def updateAll(self):
        man = self.actioner.manager
        start_task = man.curr_task
        self.resetUpdate()
        idx = 0
        while(idx < 1000):
            self.update()
            if self.update_state == 'done':
                break
            idx += 1

        cnt = 0
        for task in man.task_list:
            if task.is_freeze:
                cnt += 1
        print('Frozen tasks cnt:', cnt)
        man.curr_task = start_task
        out = man.getCurrTaskPrompts()
        return out
    
    def updateAllUntillCurrTask(self):
        man = self.actioner.manager
        start_task = man.curr_task
        self.resetUpdate()
        idx = 0
        while(idx < 1000):
            self.update()
            if self.update_state == 'done' or man.curr_task == start_task:
                break
            idx += 1

        cnt = 0
        for task in man.task_list:
            if task.is_freeze:
                cnt += 1
        print('Frozen tasks cnt:', cnt)
        # man.curr_task = start_task
        out = man.getCurrTaskPrompts()
        return out
 