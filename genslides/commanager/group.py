from genslides.task.base import TaskManager, BaseTask
# from genslides.commanager.jun import Manager
import genslides.commanager.jun as Manager
import genslides.commanager.man as BaseMan

from genslides.utils.reqhelper import RequestHelper
from genslides.utils.testrequest import TestRequester
from genslides.utils.searcher import GoogleApiSearcher
import  genslides.utils.archivator as Archivator

import genslides.utils.ids as Ids
import genslides.utils.savedata as SaveData
import genslides.utils.filemanager as FileManager
import genslides.utils.finder as finder
import genslides.utils.loader as Loader
import genslides.task_tools.text as TextTool
import genslides.task_tools.cmds as CommandTool
import genslides.utils.llmodel as LlmModel
import genslides.utils.readfileman as ReadFM
import genslides.utils.writer as Writer
import genslides.utils.convert2genslidesjson as Converter
import os
import json
import shutil
import graphviz
import copy
import datetime
import time

import logging

logger = logging.getLogger(__name__)


def printGreenCmd(text : str):
    # print(f"\033[32m{text}\033[0m")
    logger.info("\033[32m%s\033[0m", text)

class Actioner():
    def __init__(self, manager : Manager.Manager, parameters = {}) -> None:
        self.std_manager = manager
        self.setManager(manager)
        self.tmp_managers = []
        self.loadExtProject = manager.loadexttask
        # TODO: установить как значение по умолчанию
        self.path = 'saved'
        self.is_executing = False
        self.executing_man = None
        
        self.time_marker = datetime.datetime.now()
        self.parameters : dict = parameters 

        self.session_prefix = "session_"
        self.session_suffix = ""

        self.rsrvd_tmp_prefix = ""
        self.rsrvd_tmp_suffix = "_tempload"
        self.setInitialValues()

    def setInitialValues(self ):
        self.updateallcounter = 0
        self.is_updating = False
        self.force_update_stop = False
        self.hide_task = True
        self.update_state = 'init'

    def setManager(self, manager : Manager.Manager):
        if manager != self.std_manager and not manager.is_loaded:
            manager.disableOutput2()
            manager.loadTasksListFileBased()
            manager.enableOutput2()
 
        self.setCurrentManager(manager)

    def setCurrentManager(self, manager : Manager.Manager):
        if manager.is_executing:
            return
        self.manager = manager
        if manager != self.std_manager:
            if manager not in self.tmp_managers:
                self.tmp_managers.append(manager)
        manager.setActioner(self)

    def removeManager( self, manager : BaseMan.Jun):
        if manager in self.tmp_managers:
            manager.beforeRemove()
            self.tmp_managers.remove(manager)

    def reset(self):
        self.setManager(self.std_manager)
        for manager in self.tmp_managers:
            print(f"Reset {manager.getName()} manager")
            manager.onStart()
        self.tmp_managers : list[BaseMan.Jun] = []
        self.clearTmp()
        self.setInitialValues()

    def setPath(self, path: str):
        self.path = path

    def getPath(self) -> str:
        return self.path

    def clearTmp(self):
        # print('Clear temporary files')
        pass
        # tmppath = os.path.join(self.getPath(),'tmp')
        # if os.path.exists(tmppath):
        #     shutil.rmtree(tmppath)

    def loadTmpManagers(self):
        tmppath = os.path.join(self.getPath(),'tmp')
        if not os.path.exists(tmppath):
            return
        for fldname in FileManager.getFoldersInFolder(tmppath):
            manfoldpath = os.path.join(tmppath, fldname)
            self.loadManagerByPath(manfoldpath)
                
    def loadManagerByPath(self, manfoldpath):
                manager = Manager.Manager(RequestHelper(), TestRequester(), GoogleApiSearcher())
                manager.initInfo(
                                method =self.loadExtProject, 
                                task = None,
                                # path = tmppath,
                                params={'path': manfoldpath}
                                )
                self.addTasksByInfo(manager)
                # Добавляем менеджера
                if manager is not None:
                    # manager.disableOutput2()
                    # manager.loadTasksListFileBased()
                    # manager.enableOutput2()
                    self.tmp_managers.append(manager)

    def loadStdManagerTasks(self):
        self.setCurrentManager(self.std_manager)
        man = self.manager
        if not man.is_loaded:
            man.disableOutput2()
            man.loadTasksListFileBased()
            man.enableOutput2()



    def loadTmpManagerTasks(self):
        print('Load Temporary Manager Tasks')
        for man in self.tmp_managers:
            if not man.is_loaded:
                man.disableOutput2()
                man.loadTasksListFileBased()
                man.enableOutput2()


    def createPrivateManagerForTaskByName(self, man)-> Manager.Manager:
        # получаем имя задачи из текущего менеджера
        task = self.manager.getTaskByName(man['task'])
        return self.createPrivateManagerForTask(task, man)

    def createPrivateManagerForTask(self, task: BaseTask, man)-> Manager.Manager:
        print(10*"----------")
        print('Create private manager based on', task.getName(), '\nInfo:\n', man)
        print(10*"----------")
        for manager in self.tmp_managers:
            if task.getName() == manager.getName():
                return None
        manager = Manager.Manager(RequestHelper(), TestRequester(), GoogleApiSearcher())
        manager.initInfo(
                         method =self.loadExtProject, 
                         task = task,
                         path = self.getPath(), 
                         act_list= man['actions'],
                         repeat = man['repeat'],
                         params=man
                         )
        self.addTasksByInfo(manager)
        return manager
    
    def addTmpManager(self, path : str, start_task : BaseTask = None, trg_files = []) ->Manager.Manager:
        manager = Manager.Manager(RequestHelper(), TestRequester(), GoogleApiSearcher())
        manager.initInfo(
                         method =self.loadExtProject, 
                         task = start_task,
                         path = path 
                         )
        manager.disableOutput2()
        manager.loadTasksList(trg_files=trg_files)
        manager.enableOutput2()
        self.tmp_managers.append(manager)
        return manager     
   
    def resetCurrentPrivateManager(self, task: BaseTask, man):
        self.manager.curr_task = task
        self.manager.info['actions'] = man['actions']
        # self.manager.initInfo(self.loadExtProject, task, self.getPath(), man['actions'], man['repeat'] )
        # self.addTasksByInfo(self.manager,man)

    def addTasksByInfo(self,manager):
        man = manager.info
        if man and 'task_names' in man and len(man['task_names']) > 0:
            for code in man['task_names']:
                task = self.std_manager.getTaskByName(code)
                if task is not None:
                    manager.addTask(task)
            manager.info['task_names'] = man['task_names']
            # print('List for', manager.getName(),':',[t.getName() for t in manager.task_list])
            if manager.curr_task == None:
                manager.curr_task = manager.task_list[0]
            manager.saveInfo()


    def addPrivateManagerForTaskByName(self, man) ->Manager.Manager:
        print('Add priv manager for info', man)
        # Проверяем создавались ли раньше менеджеры
        for manager in self.tmp_managers:
            if man['task'] == manager.getName():
                return None
        # Создаем менеджера
        manager = self.createPrivateManagerForTaskByName(man)
        # Добавляем менеджера
        if manager is not None:
            self.tmp_managers.append(manager)
            # Устанавливаем начальные условия: текущая активная задача
            # task = manager.getTaskByName(manager.getName())
            # print('Start ', task.getName())
            # manager.curr_task = task
        return manager
    
    def addSavedScriptToCurTask(self, name: str):
        pack = self.manager.info['script']
        for man in pack['managers']:
            if name == man['task']:
                man['task'] = self.manager.curr_task.getName()
                return self.addPrivateManagerForTaskByName(man)
        return None
 
    def addSavedScript(self, name: str):
        pack = self.manager.info['script']
        for man in pack['managers']:
            if name == man['task']:
                return self.addPrivateManagerForTaskByName(man)
        return None
    

    def addEmptyScript(self, param):
        if self.manager.curr_task:
            param['task'] = self.manager.curr_task.getName()
            man_info = param
            print('Add priv manager for info', man_info)
            # Проверяем создавались ли раньше менеджеры
            # for manager in self.tmp_managers:
            #     if man_info['task'] == manager.getName():
            #         return None
            # Создаем менеджера
            task = self.manager.getTaskByName(man_info['task'])
            # for manager in self.tmp_managers:
            #     if task.getName() == manager.getName():
            #         return None
            manager = Manager.Manager(RequestHelper(), TestRequester(), GoogleApiSearcher())
            manager.initInfo(
                            method =self.loadExtProject, 
                            task = task,
                            path = self.getPath(), 
                            act_list= man_info['actions'],
                            repeat = man_info['repeat'],
                            params=man_info
                            )
            self.addTasksByInfo(manager)
            # Добавляем менеджера
            if manager is not None:
                self.tmp_managers.append(manager)
            return manager
        return None

    
    def exeTmpManagers(self):
        pack = self.manager.info['script']
        for man in pack['managers']:
            self.addPrivateManagerForTaskByName(man)
        for manager in self.tmp_managers:
            self.setManager(manager)
            self.exeComList(manager.info['actions'])
    
    def clearTmpManagers(self):
        tmp = self.tmp_managers.copy()
        for man in tmp:
            self.removeTmpManager(man, self.std_manager)
        self.setManager(self.std_manager)

    def getTmpManagersList(self):
        return [t.getName() for t in self.tmp_managers]

    def exeProgrammedCommand(self):
        pack = self.manager.info['script']
        # Читаем команды из файла проекта
        for man in pack['managers']:
            self.addPrivateManagerForTaskByName(man)
        # Выполняем заданные команды
        idx = 0
        all_done = False
        limits = self.manager.info['limits']
        while( not all_done and idx < limits):
            all_done = True
            for manager in self.tmp_managers:
                if not manager.info['done']:
                    self.setManager(manager)
                    self.exeComList(manager.info['actions'])
                    all_done = False
            idx +=1
        tmp = self.tmp_managers.copy()
        for man in tmp:
            self.removeTmpManager(man, self.std_manager)
        self.setManager(self.std_manager)
        
    def makeSavedAction(self, pack):
        print(10*"----------")
        print('Make saved actions')
        print(10*"----------")

        prompt = pack['prompt']
        act_type = pack['type']
        param = pack['param']
        tag = pack['tag']
        action = pack['action']
        print('Task info', pack)
        self.makeTaskAction(prompt, act_type, action, tag, param, save_action=False)

    def saveActionsToCurrTaskAutoCommand(self, type_name : str):
        task = self.manager.getCurrentTask()
        actions = self.manager.info['actions']
        task.setAutoCommand(type_name, actions)

    def createTmpManagerForCommandExe(self):
        man = self.manager
        tmpman_json = {'actions':[],'repeat':3,
                       'task_names':[t.getName() for t in man.getMultiSelectedTasks()],
                       'name': man.getCurrentTask().getName()}
        tmpman = self.addEmptyScript(tmpman_json)
        start = man.getCurrentTask()
        if tmpman != None:
            self.setCurrentManager(tmpman)
            project_chain = self.updateAll(update_task=False)
            print('Chain:')
            for elem in project_chain:
                print('idx',elem['idx'], 'task',elem['task'].getName())
            # for task in tmpman.getTasks():
            #     if task != start:
            #         man.addTaskToSelectList(start)
            #         res, actions = task.getAutoCommand()
            #         if res:
            #             for act in actions:
            #                 self.makeSavedAction(act)


    def exeCurManagerSmpl(self):
        idx = 0
        # print(self.manager.info['repeat'])
        while(idx < self.manager.info['repeat']):
            self.exeActions()
            if self.manager.info['done']:
                break

    def getTasksWithActions(self):
        names = []
        for task in self.manager.getTasks():
            res, _ = task.getParamStruct("autoactioner", True)
            if res:
                names.append(task.getName())
        return names
    
    def checkChildExeTasks( self, task : BaseTask ) -> bool:
        for child in task.getAllChildChains():
            if child != task:
                res, param = child.getParamStruct("autoactioner", True)
                if res and "idx" in param and "len" in param and param['idx'] < param['len']:
                    return True
        return False
    
    def exeTasks(self):
        man = self.getCurrentManager()
        cnt = man.getFrozenTasksCount()
        if cnt > 0:
            return
        for task in man.getTasks():
            res, actions = task.getAutoActCmds()
            if res and self.checkChildExeTasks(task):
                print('Exe commands by', task.getName())
                self.getCurrentManager().setCurrentTask(task)
                self.getJsonCmd(actions)
    
    def exeTasksByName(self, names):
        for name in names:
            task = self.getCurrentManager().getTaskByName(name)
            if task != None:
                res, actions = task.getAutoActCmds()
                if res:
                    print('Exe commands by', task.getName())
                    self.getCurrentManager().setCurrentTask(task)
                    self.getJsonCmd(actions)
                # for action in actions:
                    # self.makeSavedAction(action)

    def getCurrentMangerTasksByRange( self, range = "all") -> list[BaseTask]:
        man = self.getCurrentManager()
        tasks = []
        if range == "all":
            tasks = man.getTasks()
        elif range == "multi":
            tasks = man.getMultiSelectedTasks()
        elif range == "selected":
            tasks = [man.getSelectedTask()]
        elif range == "current":
            tasks = [man.getCurrentTask()]
        elif range == "childs":
            tasks = man.getCurrentTask().getAllChildChains()
        else:
            tasks = man.getTaskByType( range )
        return tasks


    def exeCmdsOfTasks(self, range = "all"):
        for task in self.getCurrentMangerTasksByRange( range ):
            if task:
                res, actions = task.getAutoActCmds()
                if res:
                    print('Exe commands by', task.getName())
                    self.getCurrentManager().setCurrentTask(task)
                    self.getJsonCmd(actions)

    def clearCmdsOfTasks(self, range = "all"):
        for task in self.getCurrentMangerTasksByRange( range ):
            task.clearAutoCommand2param()

    def clearDictBuffers(self, range = "all"):
        for task in self.getCurrentMangerTasksByRange( range ):
            task.clearDictBuffer()


    def exeActions(self):
        if self.manager is not self.std_manager:
            return self.exeComList(self.manager.info['actions'])
        return False

    def exeComList(self, pack) -> bool:
       # return True
        # Выполняем задачи
        for input in pack:
            self.makeSavedAction(input)
        success = True
        # Ищем задачи, помеченные для проверки
        for task in self.manager.task_list:
            res, val = task.getParamStruct('check')
            if res and val:
                if not task.checkTask():
                    success = False
        if success:
            self.manager.info['done'] = True
        else:
            self.manager.info['idx'] += 1
            if self.manager.info['repeat'] > 0 and self.manager.info['idx'] > self.manager.info['repeat']:
                self.manager.info['done'] = True


        return success
    
    def getActionList(self):
        out = []
        out.append({"action":"TakeFewSteps","param":{'dir':'child', 'times':3}})
        out.append({"action":"GoToNextChild","param":{}})
        out.append({"action":"GoToParent","param":{}})
        out.append({"action":"GoBackByLink","param":{}})
        out.append({"action":"InitSavdManager","param":{'task':'task_name'}})
        out.append({"action":"InitSavdManagerToCur","param":{'task':'task_name'}})
        out.append({"action":"EditPrivManager","param":{}})
        out.append({"action":"ExecuteManager","param":{}})
        out.append({"action":"InitPrivManager","param":{}})
        out.append({"action":"StopPrivManager","param":{}})
        out.append({"action":"RmvePrivManager","param":{}})
        
        if self.manager and self.manager.getCurrentTask() == None:
            out.append({"action":"SetCurrTask","param":{'task':'task_name'}})
        else:
            out.append({"action":"SetCurrTask","param":{'task':self.manager.getCurrentTask().getName()}})
        if self.manager and self.manager.getSelectedTask() == None:
            out.append({"action":"SetSlctTask","param":{'task':'task_name'}})
        else:
            out.append({"action":"SetSlctTask","param":{'task':self.manager.getSelectedTask().getName()}})
        if self.manager:
            multi_tasks = [task.getName() for task in self.manager.getMultiSelectedTasks()]

            out.append({"action":"SetMultiTask","param":{'tasks':','.join(multi_tasks)}})
        else:
            out.append({"action":"SetMultiTask","param":{'tasks':'name1,name2'}})

        return out
 
    def makeTaskAction(self, prompt, type1, creation_type, creation_tag, param = {}, save_action = True):
        # print(f"Make task action:\nprompt={prompt}\n{type1}\n{creation_type}\n{creation_tag}\n{param}\n{save_action}")
        onlysave = False
        if 'dont' in param and param['dont']:
            onlysave = True
        if save_action and creation_type != "StopPrivManager" and creation_type != "SavePrivManToTask":
            self.manager.addActions(action = creation_type, prompt = prompt, act_type = type1, param = param, tag=creation_tag)
        if onlysave:
            return
        
        if type1 == "Garland":
            return self.manager.createTreeOnSelectedTasks(creation_type,'Garland')
        elif creation_type == "Divide" and 'extedit' in param and param['extedit']:
            self.divideActions(prompt, param)
        elif 'extedit' in param and param['extedit']:
            if 'upd_cp' in param and param['upd_cp']:
                self.manager.updateEditToCopyBranch(self.manager.curr_task)
                return 

            self.editBasicActions(prompt, param)

        elif creation_type == "TakeFewSteps":
            self.manager.takeFewSteps(param['dir'], param['times'])
        elif creation_type == "GoToNextChild":
            self.manager.goToNextChild()
        elif creation_type == "GoToParent":
            self.manager.goToParent()
        elif creation_type == "GoBackByLink":
            self.manager.goBackByLink()
        elif creation_type == "InitSavdManagerToCur":
            man = self.addSavedScriptToCurTask(param['task'])
            if man is not None:
                self.setManager(man)
        elif creation_type == "InitSavdManager":
            man = self.addSavedScript(param['task'])
            if man is not None:
                self.setManager(man)
        elif creation_type == "EditPrivManager":
            self.setParamToManagerInfo(param, self.manager)
        elif creation_type == "ExecuteManager":
            self.exeActions()
        elif creation_type == "InitPrivManager":
            man = self.addEmptyScript(param)
            if man is not None:
                self.setManager(man)
        elif creation_type == "SavePrivManToTask":
            # print(self.manager.info)
            self.manager.curr_task.setManagerParamToTask({'type':'manager', 'info': self.manager.info})
        elif creation_type == "StopPrivManager":
            if self.manager == self.std_manager:
                return 
            # trg = self.tmp_managers[-2] if len(self.tmp_managers) > 1 else self.std_manager
            trg = self.std_manager
            self.removeTmpManager(self.manager, trg, copy=True)
            print('New manager is', self.manager.getName())
            if save_action:
                self.manager.addActions(action = creation_type, prompt = prompt, act_type = type1, param = param, tag=creation_tag)
        elif creation_type == "RmvePrivManager":
            if self.manager == self.std_manager:
                if len(self.tmp_managers):
                    self.setManager(self.tmp_managers[-1])
                else:
                    return 
            # trg = self.tmp_managers[-2] if len(self.tmp_managers) > 1 else self.std_manager
            trg = self.std_manager
            if save_action:
                self.manager.remLastActions()
            self.removeTmpManager(self.manager, trg, copy=False)
           
        elif creation_type == "SetCurrTask":
            self.setCurManTaskByName( name=param['task'] )
        elif creation_type == "SetSlctTask":
            self.setManSelectTaskByName(name=param['task'])
        elif creation_type == "SetMultiTask":
            self.setManMultiSelectTasksByNames( param['tasks'] )
        elif creation_type == "NewExtProject":
            self.manager.createExtProject(type1, prompt, None)
        elif creation_type == "SubExtProject":
            self.manager.createExtProject(type1, prompt, self.manager.curr_task)
        elif creation_type == "InsExtProject":
            if self.manager.curr_task != None and self.manager.curr_task.parent != None:
                trg = self.manager.curr_task
                par = self.manager.curr_task.parent
                if self.manager.createExtProject(type1, prompt, par):
                    param = {'select': self.manager.curr_task.getName()}
                    self.manager.curr_task = trg
                    self.makeTaskAction("","","Parent","", param=param, save_action=False)
        elif creation_type in self.manager.getMainCommandList() or creation_type in self.manager.vars_param:
            if 'curr' in param:
                self.manager.selected_tasks = []
                self.manager.selected_tasks.append(self.manager.curr_task)
                self.manager.curr_task = self.manager.getTaskByName(param['curr'])
            if 'select' in param:
                self.manager.selected_tasks = []
                self.manager.selected_tasks.append(self.manager.getTaskByName(param['select']))
            return self.manager.makeTaskActionBase(prompt, type1, creation_type, creation_tag, param.get("task_params",[]))
        elif creation_type in self.manager.getSecdCommandList():
            return self.manager.makeTaskActionPro(prompt, type1, creation_type, creation_tag, param.get("task_params",[]))
        elif creation_type == "MoveCurrTaskUP":
            return self.manager.moveTaskUP(self.manager.curr_task)
        elif creation_type == "MoveCurrTaskDown":
            return self.getCurrentManager().moveTaskDown(self.getCurrentManager().getCurrentTask())
        elif creation_type == "EdCp1":
            return self.manager.copyChildChains(edited_prompt=prompt, apply_link= True, remove_old_link=True)
        elif creation_type == "EdCp2":
            return self.manager.copyChildChains(change_prompt = True,edited_prompt=prompt, apply_link= True, remove_old_link=False)
        elif creation_type == "EdCp3":
            return self.manager.copyChildChains(change_prompt = True,edited_prompt=prompt, apply_link= False, remove_old_link=False)
        elif creation_type == "EdCp4":
            return self.manager.copyChildChains(change_prompt = True,edited_prompt=prompt, apply_link= True, copy=True)
        elif creation_type == "AppendNewParam":
            return self.manager.appendNewParamToTask(param['name'])
        elif creation_type == "RemoveTaskParam":
            return self.manager.removeParamFromTask(param['name'])
        elif creation_type == "SetParamValue":
            return self.manager.setTaskKeyValue(param['name'], param['key'], param['manual'])
        elif creation_type == "SetCurrentExtTaskOptions":
            self.setCurrentExtTaskOptions(param['names'])
        elif creation_type == "ResetAllExtTaskOptions":
            self.resetAllExtTaskOptions()
        elif creation_type == "RelinkToCurrTask":
            task = self.manager.getTaskByName(param['name'])
            start = self.manager.curr_task
            print('selected:',task.getName())
            print('current:', start.getName())
            if task is not None or task == start:
                if task.checkType('Collect') or task.checkType('GroupCollect') or task.checkType('Garland'):
                    if start.checkType('Collect') or start.checkType('GroupCollect') or start.checkType('Garland'):
                        intask = task
                        outtask = start
                        task.removeLinkToTask()
                        self.manager.makeLink(intask, outtask)
                else:
                    if start.checkType('Collect') or start.checkType('GroupCollect') or start.checkType('Garland'):
                        return 
                    # В противном случае ищем связанные объекты
                    garls = task.getHoldGarlands()
                    if len(garls) == 0:
                        return 
                    task.removeLinkToTask()
                    for garl in garls:
                        intask = garl
                        outtask = start
                        self.manager.makeLink(intask, outtask)
            self.manager.curr_task = start
        return 

    def fromActionToScript(self, trg: Manager, src : Manager):
        # print('From',src.info['task'], 'to', trg.info['task'])
        script = trg.info['script']['managers']
        man2 = src.info.copy()
        found = None
        for man in script:
            if src.getName() == man['task']:
                found = man
                break 
        if found is None:
            script.append(man2)
        else:
            script.remove(found)
            script.append(man2)
        # trg.info['script'] = script.copy()
        trg.saveInfo()

    def removeTmpManager(self, man : Manager, next_man: Manager, copy = True):
        print('Remove tmp manager', man.getName())
        if man is next_man:
            print('Reject nex manager == deleted manager')
            return
        # проверяем целевой
        if next_man is None:
            print('Reject nex manager == None')
            return
        if man is self.std_manager:
            print('Reject next manager == start manager')
            return
        # print('Cur task list', [t.getName() for t in man.task_list])
        # print('Nxt task list', [t.getName() for t in next_man.task_list])
        if copy:
            self.tmp_managers.remove(man)
            # копировать все задачи
            print('Copy task',[task.getName() for task in man.task_list])
            for task in man.task_list:
                if task not in next_man.task_list:
                    next_man.addTask(task)
                    task.setManager(next_man)
            man.beforeRemove(remove_folder=True, remove_task=False)
            # сохранить все действия в скрипт
            self.fromActionToScript(next_man, man)
        else:
            all_managers = [self.std_manager]
            all_managers.extend(self.tmp_managers)
            all_managers.remove(man)
            del_tasks = man.task_list
            notdel_tasks = []
            for manager in all_managers:
                for task in del_tasks:
                    if task in manager.task_list:
                        notdel_tasks.append(task)
                        # print(task.getManager().getName())
            for task in notdel_tasks:
                if task in del_tasks:
                    del_tasks.remove(task)
            print('Task to delete:',[t.getName() for t in del_tasks])
            print('Retarget task:',[t.getName() for t in notdel_tasks])
            # Вытаскиваем задачи из цепей
            man.removeTaskList(del_tasks)
            # Удаляем задачи полностью
            for task in del_tasks:
                man.curr_task = task
                man.makeTaskActionBase('', '', "Delete", '')
                    # task.beforeRemove()
                    # man.task_list.remove(task)
                    # del task

            man.beforeRemove(remove_folder=True, remove_task=False)
            self.tmp_managers.remove(man)

        del man
        # установить следущий менедежер
        self.setManager(next_man)

    def getTasksByName(self, name : str) -> list[BaseTask]:
        mans = [t for t in self.tmp_managers]
        mans.append(self.std_manager)
        print('Search task by name', name,'in', [t.getName() for t in mans])
        out = []
        for man in mans:
            task = man.getTaskByName(name)
            if task != None and task not in out:
                out.append(task)
        return out
    
    def setCurManTaskByName(self, name):
        self.getCurrentManager().setCurrentTaskByName( name )

    def setManSelectTaskByName( self, name ):
        self.getCurrentManager().setSelectedTaskByName( name )

    def setManMultiSelectTasksByNames( self, names_txt ):
        names = TextTool.convert_text_with_names_to_list( names_txt )
        for name in names:
            self.manager.addTaskToMultiSelectedByName(name)

    def getCurrentTaskName(self):
        return self.manager.curr_task.getName()

    def getCurrentTaskBranchNames(self):
        return [t.getName() for t in self.manager.curr_task.getAllParents()]

    def getTaskBranchNamesByTaskName(self, name : str):
        task = self.manager.getTaskByName(name)
        if task != None:
            return [t.getName() for t in task.getAllParents()]
        return []

    def getTmpManagerInfo(self):
        # print('Get temporary manager',self.manager.getName(),'info')
        saved_man = [t['task'] for t in self.manager.info['script']['managers']]
        saved_man.append('None')
        param = self.manager.info.copy()
        del param['script']
        del param['actions']
        # del param['task']
        del param['idx']
        del param['done']
        tmp_mannames = [t.getName() for t in self.tmp_managers]
        tmp_man = tmp_mannames
        tmp_man.append(self.std_manager.getName())
        if len(tmp_man) == 0:
            name = self.manager.getName()
        else:
            if self.manager == self.std_manager:
                name = self.manager.getName() + ' [' +'|'.join(tmp_mannames) + ']'
            else:
                name = self.std_manager.getName() + '->' + self.manager.getName()
        mangetname = self.manager.getName()
        tmpmannames = [m.getName() for m in self.tmp_managers]
        return saved_man, tmp_man, mangetname, name, tmpmannames
    


    def setParamToManagerInfo(self, param : dict, manager : Manager):
        for key, value in param.keys():
            manager.info[key] = value
        manager.saveInfo()

    # Получить информацию о состоянии ExtProjectTask и выполнить соответствующие действия
    # Collect:__init__ -> ExtProject:haveMsgsAction                         = init_loaded
    # Что делать после загрузки задачи из файла
    # Collect:__init__ -> ExtProject:haveNoMsgsAction                       = init_created
    # Что делать после инициализации новой задачи
    # Base:update->ExtProject:updateInternal-> if there is input            = update_input
    # Что делать, если новые вводные в задачу
    # Base:update->ExtProject:updateInternal-> if there is no direct change = update
    # Что делать, если обновлены родительские задачи

    def callScript(self, state: str):
        # print(10*"----------")
        # print("Call script")
        # print(10*"----------")
        # try:
            scripts = [t for t in self.manager.info['script']['managers']]
            # Убрать и сделать выполнение скриптов в зависимости от настроек скриптов?
            for script in scripts:
                print('Script:', script['ext_states'])
                print('Type:', script['type'])
                print('Task:', script['task'])
                # если скрипт относится к данному состоянию
                for st in script['ext_states']:
                    if st == state:
                        # Проверить тип скрипта
                        if script['type'] == 'simple':
                            # обычный вариант
                            # установить начальное состояние
                            self.makeTaskAction("","","InitSavdManager","", {'task': script['task']},save_action=False)
                            # Выполнить скрипт несколько раз
                            self.exeCurManagerSmpl()
                            # Сохранить результаты скрипта
                            self.makeTaskAction("","","StopPrivManager","",{}, save_action=False)
                            return
        # except Exception as e:
            # print('Cant exe script', e)


    def updateInit(self):
        man = self.manager
        man.sortTreeOrder(True)
        self.update_state = 'start tree'
        self.update_tree_idx = 0
        printGreenCmd(f"Initiate data for Update:{man.getTreeNames()}")


    def updateStepInternal(self, update_task = True, step_options = {}):
        man = self.manager
        start = self.manager.curr_task
        # print('Update step internal',start.getName())
        res, act_param = self.manager.curr_task.getExeCommands()
        if res:
            print('Execute actions')
            if not self.is_executing:
                self.is_executing = True
                self.executing_man = self.manager
            # if self.manager is self.std_manager:
                t_manager = self.createPrivateManagerForTask(start, act_param)
                self.tmp_managers.append(t_manager)
                self.setManager(t_manager)
            self.resetCurrentPrivateManager(start, act_param)
            self.exeCurManagerSmpl()
            start.confirmExeCommands(act_param)
            # ничего не меняем
            self.manager.curr_task = start
            return
        else:
            # if self.manager is not self.std_manager:
            if self.is_executing:
                self.is_executing = False
                print('End execution')
                self.setManager(self.executing_man)
             
        prev = man.getCurrentTask()
        next = man.updateSteppedSelectedInternal(update_task=update_task)

        prev.afterActionerUpdateStep(step_options)
        # if next:
            # print('Next task', next.getName(),'cur task', man.curr_task.getName())


        if next is None:
            self.update_state = 'next tree'
        elif self.root_task_tree == next:
            self.update_state = 'next tree'
            # print('Complete tree', self.root_task_tree.getName())
        # elif next == start:
        #     print("Stop cause identical task")
        #     self.update_state = 'next tree'
        else:
            self.update_state = 'step'
            self.update_processed_chain.append(next.getName())
        # if next:
        #     if len(next.getChilds()) == 0:
        #         print('Branch complete:', self.root_task_tree.getName(), '-', next.getName())

    def resetUpdate(self, force_check = False):
        self.update_state = 'init'
        man = self.manager
        if len(man.tree_arr) == 0:
            # if not force_check and man == self.std_manager:
                # man.updateTreeArr()
            # else:
                man.updateTreeArr(check_list=True)
        if len(man.tree_arr) == 0:
            return
        man.curr_task = man.tree_arr[0]
        for task in man.tree_arr:
            task.resetTreeQueue()
    
    def setStartParamsForUpdate(self, man : Manager.Manager, task : BaseTask):
        self.root_task_tree = task
        man.curr_task = task
        # man.curr_task.resetTreeQueue()
        self.update_processed_chain = [self.root_task_tree.getName()]

    def getProcessedChain(self, count = 3, plus_next_task = True):
        out = []
        chain_len = len(self.update_processed_chain)
        next_task = self.getCurrentManager().getCurrentTask().checkNextFromQueue()
        count = count - 1
        for idx in range(count):
            pt = chain_len - count + idx
            if pt < 0:
                out.append("...")
            else:
                out.append( self.update_processed_chain[pt])
        if plus_next_task and next_task == None:
            out.append("...")
        else:
            out.append(next_task.getName())
        return out
      
    def update(self, update_task = True, step_options = {}):
        man = self.manager
        # print(f"Curr state:{self.update_state}|task:{man.getCurrentTask().getName()}")
        # printGreenCmd(f"Tree order:{man.getTreeNames()}")
        if self.update_state == 'init':
            self.updateInit()
        elif self.update_state == 'start tree':
            self.time_marker = datetime.datetime.now()
            task = man.tree_arr[self.update_tree_idx]
            # print(f"Start tree {task.getName()}[{self.update_tree_idx}]:{man.getTreeNames()}")
            self.setStartParamsForUpdate(man, task)
            self.updateStepInternal(update_task=update_task, step_options=step_options)
        elif self.update_state == 'step':
            dt2 = datetime.datetime.now()  
            delta = dt2 - self.time_marker
            milisec = delta.microseconds / 1000
            step_options["time"] = milisec
            self.updateStepInternal(update_task=update_task, step_options=step_options)
        elif self.update_state == 'next tree':
            self.time_marker = datetime.datetime.now()
            if self.update_tree_idx + 1 < len(man.tree_arr):
                self.update_tree_idx += 1
                self.update_state = 'start tree'
            else:
                self.stopUpdate()
                self.update_tree_idx = 0

        # cnt = 0
        # for task in man.task_list:
        #     if task.is_freeze:
        #         cnt += 1
        # print('Frozen tasks cnt:', cnt)

        # out = self.updateUIelements()
        # return out

    def stopUpdate( self ):
        self.update_state = 'done'

    def updateCurrentTree(self):
        man = self.manager
        init_task = man.curr_task
        if len(man.tree_arr) <= man.tree_idx:
            man.updateTreeArr()
        start_task = man.getCurrentTreeRootTask()
        start_task.resetTreeQueue()
        self.update_state = 'start tree'
        self.update_tree_idx = man.tree_idx

        for task in start_task.getAllChildChains():
            for linked in task.getGarlandPart():
                linked.update()
        # self.resetUpdate()
        idx = 0
        while(idx < 1000):
            self.update()
            if self.update_state == 'next tree':
                break
            idx += 1

        man.curr_task = init_task
        return 
    
    def updateSession( self, n : int, check : bool = False, max_files_count : int = 10, update_if_only_frozen : bool = False ):
        print(f"Update session: {self.getPath()}")
        if update_if_only_frozen and self.getFrozenTasksCount() == 0 :
            print("Reset cz no frozen tasks")
            return
 
        self.setManager(self.std_manager)
        man = self.getCurrentManager()
       
        self.getCurrentManager().disableOutput2()
        for i in range(n):

            man.setUpdateSessionId(Ids.generateKey())
            name = self.getManagerSpaceName( man )
            session_id = man.getUpdateSessionId()
            logger.info("UAT[%s]: %s", i, session_id)
            self.saveManToTmp(man = man,
                suffix = session_id, 
                temp_folder = ["tt_temp",f"{self.session_prefix}{name}{self.session_suffix}"], 
                check_oldest=True, max_files= max_files_count)

            self.updateAll(force_check=check)
            if update_if_only_frozen and self.getFrozenTasksCount() == 0 :
                logger.info("Stop on %s time cz no frozen", i)
                break
            if self.force_update_stop:
                logger.info("Force stop on %s time", i)
                break
        self.getCurrentManager().enableOutput2()

    def clearSessionArchives( self ):
        man = self.getCurrentManager()
        name = self.getManagerSpaceName( man )
        folder = finder.findByKey("[[manager:path:fld]]", man, man.curr_task, man.helper )
        session_tmp_fld = ["tt_temp",f"{self.session_prefix}{name}{self.session_suffix}"]
        session_fld_path = Loader.Loader.getUniPath( FileManager.addFolderToPath(folder, session_tmp_fld))
        FileManager.deleteFiles( session_fld_path )

    def getSavedArchives(self):
        files = []
        man = self.getCurrentManager()
        name = self.getManagerSpaceName( man )
        folder = finder.findByKey("[[manager:path:fld]]", man, man.curr_task, man.helper )
        session_tmp_fld = ["tt_temp",f"{self.session_prefix}{name}{self.session_suffix}"]
        session_fld_path = Loader.Loader.getUniPath( FileManager.addFolderToPath(folder, session_tmp_fld))
        files.extend(FileManager.getFilesPathInFolder(session_fld_path))
        reserved_temp_folder = ["tt_temp",f"{self.rsrvd_tmp_prefix}{name}{self.rsrvd_tmp_suffix}"]
        reserved_fld_path = Loader.Loader.getUniPath( FileManager.addFolderToPath(folder, reserved_temp_folder))
        files.extend(FileManager.getFilesPathInFolder(reserved_fld_path))
        old_reserved_fld_path = Loader.Loader.getUniPath( FileManager.addFolderToPath(folder, ["tt_temp"]))
        filename = finder.findByKey("[[manager:path:spc:name]]", man, man.curr_task, man.helper )
        filename += "_reserved.7z"
        old_path_to_reserved = FileManager.addFolderToPath(old_reserved_fld_path, [filename])
        if Archivator.Archivator.checkPathToArchive(old_path_to_reserved):
            files.append(old_path_to_reserved)
        return files

    def restoreSession( self, session_id : str):
        man = self.getCurrentManager()
        name = self.getManagerSpaceName( man )
        temp_folder = ["tt_temp",f"{self.session_prefix}{name}{self.session_suffix}"]
        folder = finder.findByKey("[[manager:path:fld]]", man, man.curr_task, man.helper )
        fld_path = Loader.Loader.getUniPath( FileManager.addFolderToPath(folder, temp_folder))
        trg_path = Loader.Loader.getUniPath( FileManager.addFolderToPath(fld_path, [name + "_" + session_id + ".7z"]))
        self.loadManagerProjectFromFile(trg_path)
  
    def updateAllUntillTargetTask(self, name: str, force_check=False, count: int = 1, interval: float = 2.0):
        logger.debug("updateAllUntillTargetTask")
        task = self.getCurrentManager().getTaskByAnyName(name)
        
        if task is not None:  # Using 'is not None' is idiomatic Python
            self.getCurrentManager().setCurrentTask(task)
            logger.info("Update to %s", self.getCurrentManager().getCurrentTask().getName())
            
            for i in range(count):
                logger.info("Executing update loop %d of %d", i + 1, count)
                self.updateAllUntillCurrTask(force_check)
                
                # Sleep after each update, except the last one
                if i < count - 1:
                    time.sleep(interval)

    def updateAllnTimes2(self, n : int = 1, check_frozen : bool = False, check : bool = False, interval: float = 0.5):
        if check_frozen and self.getFrozenTasksCount() == 0:
            return
        self.getCurrentManager().disableOutput2()
        self.getCurrentManager().resetTaskReports()
        for i in range(n):
            logger.info('UAT: %s', i)
            self.updateAll(force_check=check)
            if self.force_update_stop:
                logger.info("Force stop on %s time", i)
                break
            if check_frozen and self.getFrozenTasksCount() == 0:
                return
            if i < n - 1:
                time.sleep(interval)

        self.getCurrentManager().enableOutput2()


    def updateAllnTimes(self, n : int, check : bool = False):
        self.getCurrentManager().disableOutput2()
        self.getCurrentManager().resetTaskReports()
        for i in range(n):
            logger.info('UAT: %s', i)
            self.updateAll(force_check=check)
            if self.force_update_stop:
                print(f"Force stop on {i} time")
                break
        self.getCurrentManager().enableOutput2()

    def updateIFfrozentasks(self, n : int = 10, check : bool = False ):
        frozen_tasks_cnt = self.getFrozenTasksCount() 
        if frozen_tasks_cnt > 0:
            self.updateAllnTimes( n , check)

    def updateToUnFreeze(self, max_times : int = 10, check : bool = False ):
        for index in range( max_times ):
            self.updateAll(force_check=check)
            frozen_tasks_cnt = self.getFrozenTasksCount() 
            if self.force_update_stop:
                break
            if frozen_tasks_cnt == 0:
                break
        return index, self.getFrozenTaskNames()

    def updateChildTasks(self, force_check = False):
        man = self.getCurrentManager()
        act = self
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
        logger.info('Frozen tasks cnt: %s', man.getFrozenTasksCount())
        man.curr_task = start_task

    def updateFromFork(self, force_check = False):
        man = self.getCurrentManager()
        start_task = man.getCurrentTask()
        print(f"Update from fork {start_task.getName()}")
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
        man.setCurrentTask( fork_root )
        self.updateChildTasks(force_check)
        man.setCurrentTask( start_task )


    def updateAll(self, force_check = False, update_task = True, max_update_idx = 10000):
        if self.is_updating:
            print('Abort',self.getPath(),'cause: already updating')
            return
        else:
            self.is_updating = True
        dt1 = datetime.datetime.now()     
        man = self.manager
        logger.info("Update all tasks of %s\n%s",man.getName(),self.getPath())
        start_task = man.getCurrentTask()
        self.resetUpdate(force_check=force_check)
        if len(man.tree_arr) == 0:
            self.is_updating = False
            return
        idx = 0
        project_chain = [{'idx':idx, 'task': man.getCurrentTask()}]
        tasks_chain = []
        while(idx < max_update_idx):
            self.update(update_task=update_task, step_options={"tasks_chain":tasks_chain})
            current_task = man.getCurrentTask()
            tasks_chain.append(current_task.getName())
            project_chain.append({'idx':idx, 'task': current_task})
            # print(f"Set struct for {current_task.getName()}: {idx}")
            current_task.setParamStruct({"type":"update_chain","chain_idx":idx})
            if self.update_state == 'done' or self.force_update_stop:
                break
            idx += 1

        cnt = man.getFrozenTasksCount()
        logger.info(
            "Act [%s] made %s step(s)\nFrozen: %s of %s task(s)",
            man.getName(),
            idx,
            cnt,
            len(man.task_list),
        )
        man.saveInfo()
        man.curr_task = start_task

        self.updateallcounter += 1
        # out = man.getCurrTaskPrompts()
        # return out
        self.is_updating = False
        dt2 = datetime.datetime.now()
        delta = dt2- dt1
        printGreenCmd(f"Update all {idx} times: {int(delta.seconds / 60)} min | {delta.seconds} second(s)")     
        return project_chain
    

    def setCurrentTaskAndUpdateAllUntillCurrTask(self, name : str, force_check=False):
        logger.info("setCurrentTaskAndUpdateAllUntillCurrTask")
        task = self.getCurrentManager().getTaskByName( name )
        if task != None:
            self.getCurrentManager().setCurrentTask( task )
            logger.info("Update to %s",self.getCurrentManager().getCurrentTask().getName())
            self.updateAllUntillCurrTask(force_check)

    def updateAllUntillCurrTask(self, force_check=False):
        man = self.manager
        start_task = man.getCurrentTask()
        self.resetUpdate(force_check=force_check)
        if len(man.tree_arr) == 0:
            return
        idx = 0
        while(idx < 1000):
            self.update()
            if self.update_state == 'done' or man.curr_task == start_task:
                break
            idx += 1
        logger.info('Frozen tasks cnt: %s', man.getFrozenTasksCount())
        man.setCurrentTask(start_task)

    def getRelatedTasks(self, task :BaseTask, lnk_in = True, lnk_out= True):
        if lnk_in:
            trg_tasks = task.getAllParents()
        else:
            trg_tasks = []
        if lnk_out:
            childs = task.getAllChildChains()
        else:
            childs = []
        related_in = []
        if lnk_in:
            for t in trg_tasks:
                related_in.extend( t.getGarlandPart())
        related_out = []
        if lnk_out:
            for t in childs:
                related_out.extend(t.getHoldGarlands())
        if lnk_out:
            if task in trg_tasks:
                trg_tasks.remove(task)
            trg_tasks.extend(childs)
        return trg_tasks, related_in, related_out
    
    def getRelationTasksChain(self):
        man = self.manager
        chain, preds, posts = self.getRelatedTasks(man.curr_task)
        idx = 0
        while (idx < 1000):
            n_preds = []
            for pred in preds:
                n_chain, a, b = self.getRelatedTasks(pred, True, False)
                n_preds.extend(a)
                chain.extend(n_chain)
            n_posts = []
            for post in posts:
                n_chain, a, b = self.getRelatedTasks(post, False, True)
                n_posts.extend(b)
                chain.extend(n_chain)

            posts = n_posts
            preds = n_preds
            
            if len(preds) == 0 and len(posts) == 0:
                break

            idx += 1
        
        man.multiselect_tasks = chain

        return 

    def setName(self, name : str):
        idx = 0
        self.std_manager.setName('_'.join(name,'base'))
        for man in self.tmp_managers:
            man.setName( '_'.join(name, str(idx)) )
            idx += 1

   

    def drawGraph(self, only_current= True, max_index = -1, path = "output/img", hide_tasks = True, add_multiselect = False, max_childs = 3, add_linked=False, add_garlands=False, all_tree_task = False, out_childtask_max = -1, hide_mono_childs = False):
        # print('Draw graph')
        man = self.manager
        tmpman_list = []
        if man == self.std_manager:
            for manager in self.tmp_managers:
                if manager != self.std_manager:
                    tmpman_list.extend(manager.task_list)
        else:
            manbase_color = 'blueviolet'
            if 'color' in man.info:
                manbase_color = man.info['color']
            tmpman_list.extend(self.std_manager.task_list)
 
        if only_current:
            if man.curr_task.isRootParent() or all_tree_task:
                target_chain = man.curr_task.getAllParents()
                target_chain.extend(man.curr_task.getAllChildChains(max_childs=1))
                trg_list = man.curr_task.getTree(max_childs=10)
                for t in target_chain:
                    if t not in trg_list:
                        trg_list.append(t)
            else:
                trg_list = man.curr_task.getAllParents(max_index = max_index)
                for task in man.curr_task.getAllChildChains(max_index=max_index, max_childs=max_childs):
                    if task not in trg_list:
                        trg_list.append(task)
                if add_linked:
                    linked_task_list = []
                    for task in trg_list:
                        linkeds = task.getGarlandPart()
                        if len(linkeds):
                            for l in linkeds:
                                linked_task_list.append(l)
                    trg_list.extend(linked_task_list)
                if add_multiselect:
                    for t in man.multiselect_tasks:
                        if t not in trg_list:
                            trg_list.append(t)
        else:
            trg_list = man.getTasks()
        # print('Target tasks:',[t.getName() for t in trg_list])
        if len(trg_list) > 0:
            f = graphviz.Digraph(comment='The Test Table',
                                  graph_attr={'size':"7.75,10.25",'ratio':'fill'})
            
            # Скрываем задачи не этого менеджера
            if hide_tasks:
                # print('Hide tasks')
                rm_tasks = []
                for task in trg_list:
                    if task not in man.task_list:
                        rm_tasks.append(task)
                for task in rm_tasks:
                    trg_list.remove(task)

            # if self.curr_task:
            #         f.node ("Current",self.curr_task.getInfo(), style="filled", color="skyblue", shape = "rectangle", pos = "0,0")
            trgs_rsm = []
            if add_garlands:
                for task in trg_list:
                    if len(task.getHoldGarlands()) > 0:
                        trgs = task.getHoldGarlands()
                        for trg in trgs:
                            if trg not in trg_list:
                                trgs_rsm.append(trg)
                trg_list.extend(trgs_rsm)
            special_tasks_list = []
            if hide_mono_childs:
                rm_tasks = []
                for task in trg_list:
                    if task != man.getCurrentTask() and len(task.getChilds()) == 1 and task.getParent() != None and len(task.getParent().getChilds()) == 1:
                        if man.getCurrentTask().getParent() != None and man.getCurrentTask().getParent() == task:
                            special_tasks_list.append(task)
                        elif task in man.getCurrentTask().getChilds():
                            special_tasks_list.append(task)
                        else:
                            rm_tasks.append(task)
                for task in rm_tasks:
                    trg_list.remove(task)

            task_nodes = []

            for task in trg_list:
                task_nodes.append({"name":task.getName(), "edges":0,"task":task})
                task_name_for_draw = task.getNameForDrawing()
                # shape
                if task in special_tasks_list:
                    if man.getCurrentTask().getParent() != None and man.getCurrentTask().getParent() == task:
                        task_name_for_draw = f"{task.getDistanceToNearestParentFork()}"
                    elif task in man.getCurrentTask().getChilds():
                        task_name_for_draw = f"{task.getDistanceToNearestChildrenFork()}"
                shape = "ellipse" #rectangle,hexagon
                if task.checkType('Response'):
                    shape = 'rectangle'
                elif task.drawAsRootTaskSymbol():
                    shape = 'invhouse'
                elif task.checkType('OutExtTree'):
                    shape = 'house'
                elif task.checkType('SetOption'):
                    shape = 'doubleoctagon'
                elif len(task.getAffectedTasks()) > 0:
                    shape = 'polygon'
                # color
                
                if task in tmpman_list:
                    color = 'blueviolet'
                    # shape = "ellipse" #rectangle,hexagon
                    if man == self.std_manager:
                        for manager in self.tmp_managers:
                            if manager != self.std_manager:
                                if task in manager.task_list:
                                    if 'color' in manager.info:
                                        color = manager.info['color']
                                    break
                    else:
                        color = manbase_color
                else:
                    color = man.getTaskNodeColor( task, trgs_rsm )
                f.node( task.getIdStr(), task_name_for_draw,style="filled",color=color, shape = shape)


                # print("info=",task.getIdStr(),"   ", task.getName())
            
            for node_info in task_nodes:
                task = node_info["task"]
                if task.checkType('IterationEnd'):
                    if task.iter_start:
                        f.edge(task.getIdStr(), task.iter_start.getIdStr())
                parent_task = task.getNearestParent(trg_list)
                if parent_task != None:
                    edge_count = 0
                    for n_i in task_nodes:
                        if n_i["task"] == parent_task:
                            n_i["edges"] += 1
                            edge_count = n_i["edges"]
                    if out_childtask_max > 0 and edge_count < out_childtask_max:
                        f.edge(parent_task.getIdStr(), task.getIdStr())
                    else:
                        f.edge(parent_task.getIdStr(), task.getIdStr())
                # for child in task.getChilds():
                #     if child not in trg_list:
                #         if child in man.task_list:
                #             if out_childtask_max > 0 and draw_child_cnt < out_childtask_max:
                #                 f.edge(task.getIdStr(), child.getIdStr())
                #                 draw_child_cnt += 1
                #         #     f.edge(task.getIdStr(), child.getIdStr())
                #     else:
                #         f.edge(task.getIdStr(), child.getIdStr())
                    # print("edge=", task.getIdStr(), "====>",child.getIdStr())
                if not add_linked:
                    for info in task.getGarlandPart():
                        f.edge(info.getIdStr(), task.getIdStr(), color = "darkorchid3", style="dashed")
                if not add_garlands:
                    for info in task.getHoldGarlands():
                        f.edge(task.getIdStr(), info.getIdStr(), color = "darkorchid3", style="dashed")
               

            img_path = path
            f.render(filename=img_path,view=False,format='png')
            img_path += ".png"
            return img_path
        return "output/img.png"

    def moveTaskFromManagerToAnother(self, tasks : list[BaseTask], cur_man : Manager.Manager, next_man: Manager.Manager):
        print('Move',len(tasks),'task(s) from', cur_man.getName(),'to', next_man.getName())
        t_to_rem = [t for t in tasks if t not in cur_man.task_list]
        for task in t_to_rem:
            tasks.remove(task)
        print('Move tasks from',cur_man.getName(),'to',next_man.getName(),':',[t.getName() for t in tasks])

        for task in tasks:
            if len(task.getGarlandPart()) > 0:
                for resp in task.getGarlandPart():
                    if resp not in tasks:
                        print(f"Move to tmp error: task[{task.getName()}] has link from {resp.getName()}[not in list]")
                        return
            if len(task.getHoldGarlands()) > 0:
                for recv in task.getHoldGarlands():
                    if recv not in tasks:
                        print(f"Move to tmp error: task[{task.getName()}] has link to {recv.getName()}[not in list]")
                        return
            for child in task.getChilds():
                if child not in tasks:
                    print('Move to tmp error: task[',task.getName(),'] is moving, but child[',child.getName(),'] is not')
                    return
                if child not in cur_man.task_list and child not in tasks:
                    print('Move to tmp error: task[',task.getName(),'] is std man task, but child[',child.getName(),'] is tmp man task and not copied')
                    return

        print('cur=',len(cur_man.task_list))
        rm_ext_tasks = []
        for task in tasks:
            if task not in next_man.task_list:
                next_man.addTask(task)
                task.setManager(next_man)
                cur_man.rmvTask(task)
            else:
                next_man.addTask(task)
                task.setManager(next_man)
                cur_man.rmvTask(task)
                rm_ext_tasks.append(task)
        if len(rm_ext_tasks):
            self.rmvExtTasksForManager(next_man, rm_ext_tasks)
        ext_tasks = []
        for task in tasks:
            par = task.getParent()
            if par and par not in next_man.task_list:
                ext_tasks.append(task)
        if len(ext_tasks):
            self.addExtTasksForManager(next_man, ext_tasks)
        
        next_man.fixTasks()

    def getExtTaskNamesOfManager(self, manager : Manager.Manager):
        return manager.info['task_names'].copy()
    
    def setExtTaskNamesToManager(self, task_names : list[str], manager : Manager.Manager):
        manager.info['task_names'] = task_names

    def addExtTasksForManager(self, manager : Manager.Manager, tasks : list[BaseTask]):
        task_names = manager.info['task_names'].copy()
        for task in tasks:
            if task not in manager.task_list:
                manager.addTask(task)
                task_names.append(task.getName())
        manager.info['task_names'] = task_names
        manager.saveInfo()
        
    def rmvExtTasksForManager(self, manager : Manager.Manager, tasks : list[BaseTask]):
        task_names = manager.info['task_names'].copy()
        for task in tasks:
            if task.getName() in task_names:
                to_delete = True
                for child in task.getChilds():
                    if child in manager.task_list:
                        to_delete = False
                        break
                if to_delete:
                    task_names.remove(task.getName())
                    manager.rmvTask(task)
        manager.info['task_names'] = task_names
        manager.saveInfo()

    def beforeRemove(self, rm_fld = True, rm_tasks = True):
        print(f"Preparing for remove {self.getPath()}")
        for man in self.tmp_managers:
            man.beforeRemove(remove_folder = rm_fld, remove_task = rm_tasks)
        self.tmp_managers.clear()
        if self.std_manager != None:
            self.std_manager.beforeRemove(remove_folder = rm_fld, remove_task = rm_tasks)

 
    def editBasicActions(self, prompt, param):
        # tasks_chains = self.manager.curr_task.getTasksFullLinks(param)
        trg_parent = None
        ignore_conv = []
        man = self.getCurrentManager()
        if 'sel2par' in param and param['sel2par'] and len(self.manager.selected_tasks) == 1:
            trg_parent = self.manager.getSelectedTask()
        if 'trg_tasks' in param:
            if 'AllTasks' in param['trg_tasks']:
                print('Get all tasks key code')
                param['trg_tasks'] = [t.getName() for t in man.getTasks()]
        tasks_chains = self.manager.getTasksChainsFromCurrTask(param)
        if len(self.manager.multiselect_tasks) > 0:
            if 'ignrlist' in param and param['ignrlist']:
                ignore_conv = self.manager.multiselect_tasks.copy()
            elif 'wishlist' in param and param['wishlist']:
                for chain in tasks_chains:
                    for task in chain['branch']:
                        if task not in self.manager.multiselect_tasks and task not in ignore_conv:
                            ignore_conv.append(task)
        # print('Ignore list:', [t.getName() for t in ignore_conv])
        if 'step' in param and param['step']:
            self.manager.copyTasksByInfoStart(
                                    tasks_chains=tasks_chains,
                                        edited_prompt=prompt, 
                                        change_prompt=param['copy_editbranch'], 
                                        switch=param['switch'],
                                        new_parent=trg_parent,
                                        ignore_conv=ignore_conv,
                                        param= param
            )
        else:
            branches_info = self.manager.copyTasksByInfo(tasks_chains=tasks_chains,
                                        edited_prompt=prompt, 
                                        change_prompt=param['copy_editbranch'],
                                        switch=param['switch'],
                                        new_parent=trg_parent,
                                        ignore_conv=ignore_conv,
                                        param = param
                                        )
            # print("Edit results:", branches_info)
            try:
                task_by_edit = branches_info[0]['created'][0]
                convert_branch_info = []
                for idx, info in enumerate(branches_info):
                    convert_branch_info.append(
                        {
                            "idx": idx,
                            "source":[t.getName() for t in info['branch']],
                            "created":[t.getName() for t in info['created']]
                        }
                    )
                edit_parameter =    {
                        "type":"onedit_result",
                        "time": SaveData.getTimeForSaving(),
                        "branches": convert_branch_info
                    }

                man.setCurrentTask( task_by_edit )
                task_by_edit.setParamStruct( edit_parameter )
            except:
                pass

    def divideTaskBasedOnPrompt( self, taskname : str, text_before : str, text_after : str):
        target = self.getCurrentManager().getTaskByName( taskname)
        if target == None:
            return
        found_max_score = 0
        divided_parts = []
        found_task = None
        for task in target.getAllParents():
            text = task.getLastMsgContentRaw()
            tag = task.getLastMsgRole()
            res, parts, score = TextTool.divide_based_on_texts_above_below(  text, text_before, text_after )
            print(f"Task {task.getName()} score: {score}")
            if res and score > found_max_score:
                found_max_score = score
                divided_parts = parts
                found_task = task
        if found_task != None and found_max_score > 0:
            print(f"Divide {found_task.getName()} with score {found_max_score}")
            self.getCurrentManager().setCurrentTask( found_task)
            self.makeTaskAction(divided_parts[0], "Request","Insert", tag)
            self.makeTaskAction(divided_parts[1], "Request","Edit", tag)

    def divideActions(self, prompt, param):
        text = prompt
        start_task = self.getCurrentManager().getCurrentTask()
        start_task_params = start_task.getAllParams()
        tag = start_task.getLastMsgRole()
        verticaldiv = text.split('[[---]]')
        horizontaldiv = text.split('[[+++]]')
        
        if len(verticaldiv) > 1:
            last = verticaldiv.pop()
            for batch in verticaldiv:
                self.makeTaskAction(batch, "Request","Insert", tag, param={"task_params": start_task_params})
                # self.manager.makeTaskAction(batch, "Request", "Insert", tag)
            return self.manager.makeTaskAction(last, "Request", "Edit", tag)
        elif len(horizontaldiv) > 1:
            for batch in horizontaldiv:
                self.manager.curr_task = start_task
                self.editBasicActions(batch, param)

    def getTaskReport( self, hide_tasks= True, max_symbols=-1):
        man = self.getCurrentManager()
        report = {}
        report["cnt"] = len(man.task_list)
        report["frozen"] = man.getFrozenTasksCount()
        gettreenameforradio_names, gettreenameforradio_trg = man.getTreeNamesForRadio()
        report["curr_tree_name"] = gettreenameforradio_trg
        report["curr_tree_branches"] = man.getBranchEnds()
        report["trees_list"] = gettreenameforradio_names
        task = man.getCurrentTask()
        if task != None:
            report["msgs"] = task.getMsgs(hide_task=hide_tasks, max_symbols=max_symbols)
            report["name"] = task.getName()
            pars = task.getAllParentNames()
            report["branch"] = "->".join(pars)
            report["prompt"] = self.getCurrentManager().getCurTaskLstMsg()
        return report

    def getCurrTaskPrompts2(self, set_prompt = "", hide_tasks = True):
        man = self.getCurrentManager()
        if man.no_output:
            return
        if man.getCurrentTask() is None:
            if len(man.task_list) > 0:
                man.curr_task = man.task_list[0]
            else:
                logger.debug('No current task')
                return
        msgs = man.curr_task.getMsgs(hide_task=hide_tasks, max_symbols=10000)
        # print('Msgs num:', len(msgs))
        # out_prompt = ""
        # if msgs:
            # out_prompt = msgs[-1]["content"]
        # saver = SaveData()
        # chck = gr.CheckboxGroup(choices=saver.getMessages())
        in_prompt, in_role, out_prompt22 = man.curr_task.getMsgInfo()

        r_msgs = man.convertMsgsToChat(msgs=msgs)
        bud_msgs = man.convertMsgsToChat(man.getBranchEndTask().getMsgs(hide_task=hide_tasks))



        
        rawinfo_msgs = man.convertMsgsToChat(man.curr_task.getRawMsgsInfo())

        task_params = man.curr_task.getAllParams()
        for param in task_params:
            if 'type' in param and param['type'] == 'response' and 'logprobs' in param:
                del param['logprobs']
            if 'type' in param and param['type'] == 'model' and 'api_key' in param:
                del param['api_key']
        res_params = {'params': task_params, 'queue':man.curr_task.getQueueList()}
        update_info = ""
        ures, uparam = man.getCurrentTask().getParamStruct("onupdate_result", True)
        if ures:
            update_info += f"Frozen: {uparam.get('frozen',False)}\n"
            update_info += f"Blocked: {uparam.get('blocked',False)}\n---\n"
            update_info += uparam.get("info","")


        cnt = 0
        cnt = man.getFrozenTasksCount()
        if cnt == 0:
            status_color = '#a3ffa7'
        else:
            status_color = '#2d50ff'
        status_msg = 'Frozen tasks: ' + str(cnt) + '/' + str(len(man.task_list)) + ':' + str(self.updateallcounter)

        gettreenameforradio_names, gettreenameforradio_trg = man.getTreeNamesForRadio()
        mancurtaskgetname = man.curr_task.getName()
        mangettasklist = man.getTaskNamesList()
        mangetcurtaskparamlist = man.getByTaskNameParamListInternal(man.curr_task)
        curtaskallpars = [t.getName() for t in man.curr_task.getAllParents()]
        mancurtaskgetbranchsum = man.curr_task.getBranchSummary()
        mangetbranchend = man.getBranchEnds()
        mangetbranchendname = man.getBranchEndName()

        mangetbranchlist = man.getBranchList()
        mangetbranchmessages = man.getBranchMessages()
        manholdgarlands = [t.getName() for t in man.getCurrentTask().getHoldGarlands()]
        mangarlandparts = [t.getName() for t in man.getCurrentTask().getGarlandPart()]
        mangetname = man.getName()
        mangetcolor = man.getColor()
        multitasks = ', '.join(["\""+t.getName() + "\"" for t in man.multiselect_tasks]) + " : "
        multitasks += ', '.join([t.getName() for t in man.multiselect_tasks])
        # return self.convToGradioUI(
        return (
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
                        mangarlandparts,
                        mangetname,
                        mangetcolor,
                        multitasks,
                        bud_msgs,
            ','.join(self.manager.getSelectList()),
            self.manager.getSelectedContent()

        )


   

   
    def setCurrentExtTaskOptions(self, names : list):
        man = self.manager
        full_names = finder.getExtTaskSpecialKeys()
        for name in full_names:
            if name not in names:
                man.curr_task.updateParam2({'type': name, name : False})
            else:
                man.curr_task.updateParam2({'type': name, name : True})

        man.curr_task.saveAllParams()
    
    def resetAllExtTaskOptions(self):
        man = self.manager
        full_names = finder.getExtTaskSpecialKeys()
        full_names.remove('input')
        for task in man.task_list:
            for name in full_names:
                task.updateParam2({'type': name, name : False})
            task.saveAllParams()
   
    def getTaskKeyValueInternal(self, param_name, param_key):
        man = self.getCurrentManager()
        # print('Get task key value:',param_name,'|', param_key)
        interacttive_drd = True
        multiselect_drd = False
        choices = []
        cur_val = 'None'
        if param_key == 'path_to_read':
            # print("Get path to read")
            res, fnames = man.getCurrentTask().getPathToRead()
            if res and len(fnames):
                filename = fnames[0]
                return fnames, filename, interacttive_drd, multiselect_drd, filename, True
        elif param_name == 'script' and param_key == 'path_to_trgs':
            filename = "[[project:RunScript:python]] "
            filename += Loader.Loader.getFilePathFromSystem(manager_path=man.getPath())
            multiselect_drd = True
            res, data = man.curr_task.getParamStruct(param_name)
            choices.append(filename)
            if res and param_key in data:
                choices.append(str(data[param_key]))
            return filename, filename, interacttive_drd, multiselect_drd, str(filename), True
            # return (gr.Dropdown(choices=filename, value=filename,multiselect=True, interactive=True),
            #         gr.Textbox(str(filename)))
        elif param_name == 'array' and param_key == 'array':
            res, data = man.getCurrentTask().getParamStruct(param_name, only_current=True)
            if res and param_key in data:
                filename = Loader.Loader.convJsonToText(data[param_key], indent=1)
            return [filename], filename, interacttive_drd, multiselect_drd, filename, True
        elif param_name == 'autocommander':
            value, choices = self.getCurrentManager().getCurrentTask().getParamStructChoices(param_name, param_key)
            return choices, value, interacttive_drd, multiselect_drd, value, True

        elif param_key == 'path_to_write':
            res, fnames = man.getCurrentTask().getPathToRead()
            if res and len(fnames) > 0:
                filename = fnames[0]
                return fnames, filename, interacttive_drd, multiselect_drd, filename, True
            # else:
            #     filename = Loader.Loader.getDirPathFromSystem(man.getPath())
            #     choices.append(filename)
            #     res, data = man.curr_task.getParamStruct(param_name)
            #     if res and param_key in data:
            #         choices.append(str(data[param_key]))
            #     return choices, os.path.join(filename,'insert_name'), interacttive_drd, multiselect_drd, filename, True
            # return gr.Dropdown(choices=[filename], value=os.path.join(filename,'insert_name'), interactive=True), gr.Textbox(value=filename, interactive=True)
        elif param_key == 'model':
            res, data = man.curr_task.getParamStruct(param_name)
            if res:
                manager_keys = [f"[[manager:global:{t}]]" for t in man.getGlobalKeys() if t.endswith('odel')]
                cur_val = data[param_key]
                path_to_config = os.path.join('config','models.json')
                values = []
                with open(path_to_config, 'r') as config:
                    models = json.load(config)
                    for _, vals in models.items():
                        values.extend([opt['name'] for opt in vals['prices']])
                values.extend( manager_keys )
                return values, cur_val, interacttive_drd, multiselect_drd, "", True
                # return (gr.Dropdown(choices=values, value=cur_val, interactive=True, multiselect=False),
                        #  gr.Textbox(value=''))
           
        task_man = TaskManager()
        res, data = man.getCurrentTask().getParamStruct(param_name, only_current=True)
        # print('Get param',param_name,' struct', res, data)
        if res and param_key in data:
            cur_val = data[param_key]
            # print('cur val:',cur_val)
            if param_key == 'idx' and (param_name.startswith('child') or param_name == 'tree_step'):
                values = range(50)
                if cur_val not in values:
                    values.append(cur_val)
            else:
                values = task_man.getOptionsBasedOptionsDict(param_name, param_key)
            # print('Update with [',cur_val,'] from', values)
            if len(values):
                if cur_val not in values:
                    values.append(cur_val)
                return values, cur_val, interacttive_drd, multiselect_drd, cur_val, True
                    # return (gr.Dropdown(choices=values, value=cur_val, interactive=True, multiselect=False),
                        #  gr.Textbox(value=''))
            else:
                    # str_cur_val = str(cur_val)
                    if isinstance(cur_val, dict):
                        str_cur_val = json.dumps(cur_val, indent=1)
                    elif isinstance(cur_val, str):
                        str_cur_val = cur_val
                    else:
                        str_cur_val = ""
                    return [cur_val], cur_val, interacttive_drd, multiselect_drd,str_cur_val, True
                    # return (gr.Dropdown(choices=cur_val, value=cur_val, interactive=True, multiselect=False),
                        #  gr.Textbox(value=str_cur_val))
        return [cur_val], cur_val, interacttive_drd, multiselect_drd,"", True
        # return (gr.Dropdown(choices=[cur_val], value=cur_val, interactive=True, multiselect=False), 
        #         gr.Textbox(value=''))
    def selectManagerByName(self, name):
        if self.std_manager.getName() == name:
            self.setManager(self.std_manager)
        else:
            for man in self.tmp_managers:
                if man.getName() == name:
                    self.setManager(man)
                    break
    def goToTreeByName(self, name):
        self.manager.goToTreeByName(name)

    def setCurrTaskByBranchEndName(self, name):
        self.manager.setCurrTaskByBranchEndName(name)


    def moveTaskFromTMPmanToSTDman(self, tasks : list[BaseTask], cur_man : Manager.Manager, next_man: Manager.Manager):
        t_to_rem = [t for t in tasks if t in next_man.task_list] # Уже там, не копировать
        t_to_rem.extend([t for t in tasks if t not in cur_man.task_list])
        for task in t_to_rem:
            tasks.remove(task)

        task_to_exttask = []
        for task in tasks:
            if len(task.getGarlandPart()) > 0:
                for resp in task.getGarlandPart():
                    if resp not in tasks and resp not in next_man.task_list:
                        print(f"Move to std error: task[{task.getName()}] has link from {resp.getName()}[not in list]")
                        return
            # if len(task.getHoldGarlands()) > 0:
            #     for recv in task.getHoldGarlands():
            #         if recv not in tasks:
            #             print(f"Move to std error: task[{task.getName()}] has link to {recv.getName()}[not in list]")
            #             return
            for child in task.getChilds():
                if child not in tasks:
                    if child in next_man.task_list:
                        pass
                    else:
                        task_to_exttask.append(task)
            if task.getParent() != None and task.getParent() not in tasks and task.getParent() not in next_man.task_list:
                print(f"Move to std error: task[{task.getName()}] has parent {task.getParent().getName()}[not in list]")
                return

        
        print('Move tasks from',cur_man.getName(),'to',next_man.getName(),':',[t.getName() for t in tasks])

        for task in tasks:
                next_man.addTask(task)
                task.setManager(next_man)
                cur_man.rmvTask(task)
                task.saveAllParams()

        if len(tasks):
            self.addExtTasksForManager(cur_man, tasks)
        
        cur_man.fixTasks()

    def afterLoading(self):
        # TODO: запуск кастомных команд после загрузки акционера
        task_manager = TaskManager()
        task_manager.clearTasksCache()

    def getRelatedActionersPaths( self, actpaths_list : list[str]):
        for task in self.getCurrentManager().getTasks():
            actpaths_list = task.getRelatedActionersPaths( actpaths_list )
        return actpaths_list

    def getLoadedActionerPath( self, actpaths_list : list[str] ):
        for task in self.getCurrentManager().getTasks():
            actpaths_list = task.getLoadedActionerPath( actpaths_list )
        return actpaths_list

    def getExtTreeTasks( self ):
        return [t for t in self.getCurrentManager().getTasks() if t.isExternalProjectTask()]

    def autoUpdateExtTreeTaskActs(self, actioners: list):
        # print(f"Auto load ext tree act for {self.getPath()}")
        man = self.std_manager
        if not isinstance(man, Manager.Manager):
            print("Current manager is temporary: target manager is executing")
            return
        for task in man.getTasks():
            if task.isExternalProjectTask():
                # print(f"Load for task {task.getName()}")
                task.loadActionerTasks(actioners)
 
    def getCurManInExtTreeTasks(self):
        man = self.manager
        out = []
        out_paths = []
        for task in man.task_list:
            if task.isExternalProjectTask():
                out.append(task.getName())
                out_paths.append(task.getTargetActionerPath())
        return out, out_paths
    
    def getCurrentManager(self) -> Manager.Manager:
        return self.manager


    def updateManagerStepInternal(self, man: Manager.Manager, update_task = True):
        start = self.manager.curr_task
        next = man.updateSteppedSelectedInternal(update_task=update_task)
        if next is None:
            self.update_state = 'next tree'
        elif self.root_task_tree == next:
            self.update_state = 'next tree'
        else:
            self.update_state = 'step'
            self.update_processed_chain.append(next.getName())
        # if next:
        #     if len(next.getChilds()) == 0:
        #         print('Branch complete:', self.root_task_tree.getName(), '-', next.getName())

    def updateManager(self, man : Manager.Manager, update_task = True):
        # printGreenCmd("Update manager")
        # print('Curr state:', self.update_state,'|task:',man.curr_task.getName())
        if self.update_state == 'init':
            man.sortTreeOrder(True)
            self.update_state = 'start tree'
            self.update_tree_idx = 0
        elif self.update_state == 'start tree':
            task = man.tree_arr[self.update_tree_idx]
            # print('Start tree', task.getName(),'[',self.update_tree_idx,']')
            self.setStartParamsForUpdate(man, task)
            self.updateManagerStepInternal(man, update_task=update_task)
        elif self.update_state == 'step':
            self.updateManagerStepInternal(man, update_task=update_task)
                # self.root_task_tree = next
        elif self.update_state == 'next tree':
            if self.update_tree_idx + 1 < len(man.tree_arr):
                self.update_tree_idx += 1
                self.update_state = 'start tree'
            else:
                self.stopUpdate()
                self.update_tree_idx = 0

    def resetUpdateManager(self, man : Manager.Manager, param = {}):
        self.update_state = 'init'
        if len(man.tree_arr) == 0:
            # if not force_check and man == self.std_manager:
                # man.updateTreeArr()
            # else:
                man.updateTreeArr(check_list=True)
        if len(man.tree_arr) == 0:
            return
        man.curr_task = man.tree_arr[0]
        for task in man.tree_arr:
            task.resetTreeQueue()
 
    def updateManagerAll(self, params = {
                          'force_check' : False, 'update_task' : True, 'max_update_idx' : 10000
                          }):
        if self.is_updating:
            print('Abort',self.getPath(),'cause: already updating')
            return
        else:
            self.is_updating = True
        man = self.manager
        man.is_executing = True
        exe_manager = BaseMan.Jun(None, None, None)
        man.syncManager(exe_manager)
        self.setCurrentManager(exe_manager)
        logger.info("Update all tasks of %s\n%s",man.getName(),self.getPath())
        start_task = man.curr_task
        self.resetUpdateManager(man, params)
        if len(man.tree_arr) == 0:
            self.is_updating = False
            return
        idx = 0
        project_chain = [{'idx':idx, 'task': man.getCurrentTask()}]
        while(idx < params['max_update_idx']):
            self.updateManager(man, update_task=params['update_task'])
            project_chain.append({'idx':idx, 'task': man.getCurrentTask()})
            if self.update_state == 'done':
                break
            idx += 1

        cnt = man.getFrozenTasksCount()
        logger.info(
            "Act [%s] made %s step(s)\nFrozen: %s of %s task(s)",
            man.getName(),
            idx,
            cnt,
            len(man.task_list),
        )
        man.saveInfo()
        man.curr_task = start_task

        self.updateallcounter += 1
        # out = man.getCurrTaskPrompts()
        # return out
        self.is_updating = False
        man.is_executing = False
        self.removeManager(exe_manager)
        self.setCurrentManager(man)
        return project_chain

    def getFrozenTasksCount(self) -> int:
        frozen_tasks = self.getCurrentManager().getFrozenTasksCount()
        for task in self.getCurrentManager().getTasks():
            res, param = task.getParamStruct('array', only_current=True)
            if res and isinstance(param['idx'], int) and param['idx'] < param['len'] - 1:
                frozen_tasks += 1
        return frozen_tasks
    
    def getFrozenTaskNames(self) -> list:
        man = self.getCurrentManager()
        names = []
        for task in man.getTasks():
            if task.isFrozen():
                names.append(task.getName())
        for task in self.getCurrentManager().getTasks():
            res, param = task.getParamStruct('array', only_current=True)
            if res and isinstance(param['idx'], int) and param['idx'] < param['len'] - 1:
                names.append(task.getName())
        return names
    
    def getNearestExtTreeTask ( self ) -> BaseTask:
        target = self.getCurrentManager().getCurrentTask()
        found = None
        found_distance = 0
        for task in target.getAllChildChains():
            if task.isExternalProjectTask():
                if found == None:
                    found = task
                    found_distance = task.getDistance(target)
                else:
                    if found_distance > task.getDistance( target ):
                        found = task
                        found_distance = task.getDistance(target)
        return found
    
    def getExtTreeCmdTrgSessions(self, task : BaseTask):
        output = []
        for action_str in task.getExtTreeTaskCmds():
            res, action = Loader.Loader.loadJsonFromText( action_str )
            if res and "action" in action and "session_id" in action:
                s_id = action["session_id"]
                if s_id not in output:
                    output.append(s_id) 
        return output
 
    
    def getExtTreeCmdsListOfTask( self, task : BaseTask ):
        output = []
        for action_str in task.getExtTreeTaskCmds():
            res, action = Loader.Loader.loadJsonFromText( action_str )
            if res and "action" in action:
                header = action["action"]
                if "kwargs" in action:
                    if "taskname" in action["kwargs"]:
                        header += " |" + action["kwargs"]["taskname"]
                        output.append([header , action_str])
                    elif "marker" in action["kwargs"]:
                        header += " |" + action["kwargs"]["marker"]
                        output.append([header , action_str])
                    elif "task_marker1" in action["kwargs"] and "task_marker1" in action["kwargs"]:
                        header += " |" + action["kwargs"]["task_marker1"]
                        header += " |" + action["kwargs"]["task_marker2"]
                        output.append([header , action_str])
                    else:
                        output.append([action_str, action_str])
        return output

    def getExtTreeCmdsListOfCurrentTask( self ):
        task = self.getCurrentManager().getCurrentTask()
        return task.getExtTreeTaskCmds()
 
    def getJsonCmd(self, json_cmds):
        cmds = json.loads(json_cmds) # parse the JSON array
        return self.getJsonCustomCmd( cmds )

    def getJsonCustomCmd(self, cmds : list):

        logger.info("Get json command for %s", self.getPath())
        results = [] # list to hold results of each command
        try:

            if not isinstance(cmds, list):
                return "Error: Input must be a JSON array."
            
            logger.info("Cmds count: %s",len(cmds))


            for cmd in cmds:
                action = cmd.get("action")
                printGreenCmd(f"Run {action} cmd")
                args = cmd.get("args", [])
                kwargs = cmd.get("kwargs", {})

                if action:
                    method = getattr(self, action, None)
                    if method and callable(method):
                        # print('Args:', args)
                        # print('Kwargs', kwargs)
                        # print('Method', method)
                        self.getCurrentManager().setCurrentCommandInfo( cmd )
                        result = method(*args, **kwargs)
                        results.append({"action": action, "result": result})  # Append the result of each action
                    else:
                        results.append(f"Error: Action '{action}' not found or not callable.")

                else:
                    results.append("Error: Missing 'action' key in JSON.")
            logger.debug("Actioner(%s):\n%s", self.getPath(), results)
            return results # return a list of results

        except json.JSONDecodeError:
            return "Error: Invalid JSON format."
        
    def goToChildTaskbyTag( self, tags : str ):
        man = self.getCurrentManager()
        tasks = man.getCurrentTask().getAllChildChains()
        tasks.remove(man.getCurrentTask())
        tags_list =[t.replace(" ","") for t in tags.split(',')]
        for task in tasks:
            if task.checkTags( tags_list ):
                man.setCurrentTask( task )
                break

    def switchCurrentTaskType( self, trg_type : str, toraw = False ):
        man = self.getCurrentManager()
        task = man.getCurrentTask()
        parent = task.getParent()
        children = copy.deepcopy( task.getChilds() )
        inlinks = task.getHoldGarlands()
        outlinks = task.getGarlandPart()
        if toraw:
            prompt=task.getPromptContentForCopyConverted() 
        else:
            prompt=task.getPromptContentForCopy() 
        prompt_tag=task.getLastMsgRole()
        param_task = task.copyAllParams(True)
        prio = task.getPrio()
        man.setCurrentTask( parent )
        self.makeTaskAction(prompt, trg_type, "SubTask", prompt_tag, param_task)
        # man.createOrAddTask(prompt, trg_type, prompt_tag, parent, param_task)

        cr_task = man.getCurrentTask()
        cr_task.setPrio(prio)

        print(task.getName())
        print(cr_task.getName())

        for child in children:
            man.addTaskToSelectList( cr_task)
            param = {'curr':child.getName(),'select': cr_task.getName()}
            print(param)
            man.setCurrentTask( child )
            self.makeTaskAction("","","Parent","", param)
            # child.setParent( cr_task)
        
        man.setCurrentTask( task )
        self.makeTaskAction("","","Delete","")
        man.setCurrentTask( cr_task )

        for link in inlinks:
            man.makeLink( link, cr_task )
        
        for link in outlinks:
            man.makeLink( cr_task, link )

    def getTasksByRange( self, range = "Current" ):
        tasks  = []
        if range == "Current":
            tasks = [self.getCurrentManager().getCurrentTask()]
        elif range == "Multi":
            tasks = self.getCurrentManager().getMultiSelectedTasks()
        else:
            names = TextTool.convert_text_with_names_to_list( range )
            for name in names:
                task = self.getCurrentManager().getTaskByName( name )
                if task != None:
                    tasks.append( task )
                else:
                    print(f"Can\'t find \"{name}\"")
            if len(tasks) == 0:
                tasks = self.getCurrentManager().getAllTasksByTagFromTaskList(range, self.getCurrentManager().getTasks())
        return tasks
    
    def applyNewParameterValues( self, range : str, param : dict):
        tasks  = self.getTasksByRange( range )
        for task in tasks:
            task.rewriteParamStruct( param )
    
    def setForcedBlockedStatus ( self, range = "Current", block_status = True):
        tasks  = self.getTasksByRange( range )
        for task in tasks:
            task.setForcedBlockStatus( block_status )
            
 
    def cleanTaskParameters( self, range : str = "Current", target : str = "clean"):
        tasks  = self.getTasksByRange( range )
        for task in tasks:
            logger.debug("Apply to %s task ",task.getName())
            if target == "hash":
                task.forceResetHash()
            elif target == "array":
                task.forceResetArray()
            elif target == "clean":
                task.forceCleanChat()

    def cleanLastMessageCurrentTask(self):
        man = self.getCurrentManager()
        task = man.getCurrentTask()
        task.forceCleanChat()
    
    def cleanLastMessageForMulti(self):
        for task in self.getCurrentManager().getMultiSelectedTasks():
            task.forceCleanChat()

    def cleanTasksChat(self, task_names = ""):
        print('Clean task chats for', task_names)
        man = self.getCurrentManager()
        if task_names == "":
            tasks = man.getTasks()
        else:
            tasks_list = task_names.split(",")
            tasks = [man.getTaskByName(name.replace(" ","")) for name in tasks_list]
        man.cleanTasksChat(tasks)


    def branchingAction( self, prompt ):
        print ("Execute branching action")
        self.makeTaskAction( 
            prompt=prompt,
            type1='Request',
            creation_type='Edit',
            creation_tag='user',
            param={
                "extedit": True,
                "copy_editbranch": False,
                "resp2req": False,
                "coll2req": False,
                "read2req": False,
                "run2req": False,
                "in": True,
                "out": True,
                "link": True,
                "av_cp": True,
                "sel2par": False,
                "ignrlist": False,
                "wishlist": False,
                "upd_cp": False,
                "onlymulti": False,
                "reqSraw": False,
                "forcecopyresp": False,
                "check_man": False,
                "dont": False,
                "switch": [],
                "trg_tasks": [
                "AllTasks"
                ]
                },
            save_action=True                
            )

    def editingAction( self, prompt ):
        self.makeTaskAction( 
            prompt=prompt,
            type1='Request',
            creation_type='Edit',
            creation_tag='user',
            param={
                "extedit": False,
                "copy_editbranch": False,
                "resp2req": False,
                "coll2req": False,
                "read2req": False,
                "run2req": False,
                "in": False,
                "out": False,
                "link": False,
                "av_cp": False,
                "sel2par": False,
                "ignrlist": False,
                "wishlist": False,
                "upd_cp": False,
                "onlymulti": False,
                "reqSraw": False,
                "forcecopyresp": False,
                "check_man": False,
                "dont": False,
                "switch": [],
                "trg_tasks": [
                "AllTasks"
                ]
                },
            save_action=True                
            )
        return f"Execute editing action for {self.getCurrentManager().getCurrentTask().getName()}"

    def getTaskByTag( self, tags : str):
        man = self.getCurrentManager()
        task = man.getTaskByTagFromTasks(tags, man.getTasks())
        if task:
            print(f"Select {task.getName()} by {tags}")
            man.setCurrentTask(task)

    def filterJsonCommands( self, cmds_list : list[dict]):
        trg_tasks = []
        updated_cmds_list = []
        for cmd in cmds_list:
            if "action" in cmd:
                if cmd["action"] == "editMarkeredText":
                    marker = cmd.get("kwargs",{}).get("marker","")
                    task = self.getCurrentManager().getTaskByAnyName( marker )
                    if task != None:
                        if task not in trg_tasks:
                            trg_tasks.append( task )
                            updated_cmds_list.append( cmd )
                        else:
                            cmd["action"] = "insertTextAfterMarker"
                            cmd["kwargs"]["marker"] = f"[{task.getShortName()}]"
                            # Если ключа нет, ничего не произойдет
                            if "edited_text" in cmd["kwargs"]:
                                cmd["kwargs"]["inserted_text"] = cmd["kwargs"].pop("edited_text")
                                updated_cmds_list.append( cmd )
                else:
                    updated_cmds_list.append( cmd )

        return updated_cmds_list

    def insertTextAfterMarker(self, inserted_text, marker, justification = ""):
        return self.insertingToTaskAction( prompt=inserted_text, taskname=marker)

    def editMarkeredText( self, edited_text : str, marker : str ):
        return self.editingToTaskAction( edited_text, marker )

    def editMarkedText( self, text_fragment : str, marker : str, justification = "" ):
        return self.editMarkeredText( text_fragment, marker )
    
    def moveMarkedText (self, moving_direction, marker, justification = ""):
        task = self.getCurrentManager().getTaskByAnyName( marker )
        if task == None:
            return
        if moving_direction == "Up":
            self.getCurrentManager().moveTaskUP(task)
        elif moving_direction == "Down":
            self.getCurrentManager().moveTaskDown(task)

    def deleteMarkedText( self, marker, justification = ""):
        return self.deleteTask(marker)

    def splitMarkedText(self, marker : str, fragments : list[str], justification = "" ):
        if len(fragments) > 0:
            first = True
            for text in fragments:
                if first:
                    self.editMarkedText(text, marker, justification)
                    first = False
                else:
                    self.insertTextAfterMarker( text, marker, justification )
                    marker = self.getCurrentManager().getCurrentTask().getName()

    def mergeMarkedText(self, target_marker, source_marker, text_fragment : str, justification = "" ):
        man = self.getCurrentManager()
        trg_task = man.getTaskByAnyName(target_marker)
        src_task = man.getTaskByAnyName( source_marker )
        if trg_task and src_task:
            self.editMarkedText( text_fragment, target_marker, justification)
            self.deleteMarkedText( source_marker, justification)
        

    def insertingToTaskAction( self, prompt : str, taskname : str, task_type = "Request", role = "user", task_params = [] ):
        man = self.getCurrentManager()
        task = man.getTaskByAnyName(taskname)
        if task:
            if len(task.getChilds()):
                task = task.getChilds()[0]
            man.setCurrentTask( task )
            return self.insertingAction(prompt, task_type, role, task_params)
        return f"No task found with {taskname}"

    def editingToTaskAction( self, prompt : str, taskname : str ):
        man = self.getCurrentManager()
        task = man.getTaskByAnyName(taskname)
        if task:
            man.setCurrentTask( task )
            return self.editingAction(prompt)
        else:
            return f"No task found with {taskname}"
 
    def insertingAction( self, prompt, task_type = "Request", role = "user", task_params = [] ):
        param = {}
        if isinstance(task_params, list) and len(task_params) > 0:
            param["task_params"] = task_params
        self.makeTaskAction( 
            prompt=prompt,
            type1=task_type,
            creation_type='Insert',
            creation_tag = role,
            param=param ,
            save_action=True                
            )
        return f"Execute inserting action for {self.getCurrentManager().getCurrentTask().getName()}"

    def createGarlandTree(self, prompt, out_prompt = "[[parent:code]]", root_type = "SetOptions", receivroot_type = "SetOptions", receiver_type = "Listener"):
        man = self.getCurrentManager()
        # trg = man.getCurrentTask()
        role = "user"
        self.makeTaskAction("",root_type,"New",role)
        tree_root_task = man.getCurrentTask()
        task_type = "Request"
        child_action = "SubTask"
        self.makeTaskAction(prompt=prompt,type1= task_type,creation_type= child_action,creation_tag= role)
        self.makeTaskAction(prompt= out_prompt,type1= task_type,creation_type= child_action,creation_tag= role)
        output_task = man.getCurrentTask()
        man.addTaskToSelectList(man.getCurrentTask())
        man.setCurrentTask(tree_root_task)
        self.makeTaskAction("",receivroot_type,child_action,role)
        man.createTreeOnSelectedTasks(child_action, receiver_type)
        # man.setCurrentTask(output_task)

    def iterrateArrayForced( self ):
        man = self.getCurrentManager()
        task = man.getCurrentTask()
        task.iterrateArrayForced()

    def getMainOutput( self, task : BaseTask ) -> BaseTask:
        if len(task.getHoldGarlands()):
            return task
        return None
    
    def checkOnSrcMarkerToChoiser( self, break_task : BaseTask, target : BaseTask) -> bool:
        # if break_task.checkType("Listener"):
        #     return False
        for task in target.getAllParents():
            if task.checkType("ExternalInput"):
                return True
        return False
    
    def runSteppedDocTreeAllStages(self,
                                     input_answer: str = "input_answer",
                                     cmd_list_key: str = "text_edits",
                                     text_batch_key: str = "proposed_text_batch",
                                     marker_key: str = "reference_marker",
                                     edit_key: str = "edit_type",
                                     text_batch_reason_key: str = "justification_for_edit",
                                     direct_cmd_update: bool = True,
                                     copy_to_dict: bool = False,
                                     steps: int = 1,
                                     reset: bool = False):
        """
        Run updateDocTreeAllStagesStep repeatedly until all stages are processed.

        Args: same as updateDocTreeAllStagesStep; `steps` is the chunk size per call.
        Returns a dict with:
        - total_processed: total number of stage actions processed
        - iterations: number of updateDocTreeAllStagesStep calls made
        - finished: True if completed normally (no remaining stages)
        - remaining: number of actions left on the internal stack (0 if finished)
        - stalled: True if loop stopped because no progress was made (possible bug)
        - last_result: the last dict returned by updateDocTreeAllStagesStep
        """
        if steps is None or steps < 1:
            raise ValueError("steps must be an integer >= 1")

        total_processed = 0
        iterations = 0
        stalled = False
        last_result = None

        # Ensure the stepper is initialized (reset will force re-init)
        # First call will initialize internal stack if needed.
        # Pass the provided reset flag to start fresh if requested.
        last_result = self.runDocTreeStageStep(
            input_answer=input_answer,
            cmd_list_key=cmd_list_key,
            text_batch_key=text_batch_key,
            marker_key=marker_key,
            edit_key=edit_key,
            text_batch_reason_key=text_batch_reason_key,
            direct_cmd_update=direct_cmd_update,
            copy_to_dict=copy_to_dict,
            steps=0 if reset else 1,  # if reset=True we want to initialize but not consume; a step=0 is invalid, so instead call with reset behavior below
            reset=reset
        )
        # Note: some callers prefer to initialize without consuming any steps.
        # If the above call returned a processed_count (because reset was False), include it.
        if last_result is not None and isinstance(last_result, dict):
            # If reset=True and the implementation of updateDocTreeAllStagesStep honored reset
            # and returned no processing, processed_count may be 0.
            total_processed += int(last_result.get("processed_count", 0))
            iterations += 1

        # Now loop until finished
        while True:
            # Call the stepper to process `steps` actions (normal stepping)
            last_result = self.runDocTreeStageStep(
                input_answer=input_answer,
                cmd_list_key=cmd_list_key,
                text_batch_key=text_batch_key,
                marker_key=marker_key,
                edit_key=edit_key,
                text_batch_reason_key=text_batch_reason_key,
                direct_cmd_update=direct_cmd_update,
                copy_to_dict=copy_to_dict,
                steps=steps,
                reset=False
            )
            iterations += 1

            if not isinstance(last_result, dict):
                # Unexpected return type — abort to avoid infinite loop
                stalled = True
                break

            processed = int(last_result.get("processed_count", 0))
            total_processed += processed
            remaining = int(last_result.get("remaining", 0))
            finished = bool(last_result.get("finished", False))

            # If nothing was processed but not finished -> stalled (avoid infinite loop)
            if processed == 0 and not finished:
                stalled = True
                break

            if finished:
                stalled = False
                break

            # otherwise continue looping

        return {
            "total_processed": total_processed,
            "iterations": iterations,
            "finished": (not stalled) and bool(last_result.get("finished", False)),
            "remaining": int(last_result.get("remaining", 0)) if isinstance(last_result, dict) else None,
            "stalled": stalled,
            "last_result": last_result
        }


    def runDocTreeStageStep(self,
                                input_answer: str = "input_answer",
                                cmd_list_key: str = "text_edits",
                                text_batch_key: str = "proposed_text_batch",
                                marker_key: str = "reference_marker",
                                edit_key: str = "edit_type",
                                text_batch_reason_key: str = "justification_for_edit",
                                direct_cmd_update: bool = True,
                                copy_to_dict: bool = False,
                                steps: int = 1,
                                reset: bool = False):
        """
        Advance the update tree algorithm `steps` times (default 1). Call repeatedly
        to step through the stages in depth-first order.

        Returns a dict:
        - processed_actions: list of stage_action items that were processed this call
        - processed_count: number of actions processed this call
        - total_processed: total actions processed across this session
        - remaining: number of actions still on the stack
        - finished: True if no more actions remain after this call
        - stack_preview: small preview of next actions on the stack (up to 10)
        """
        print("Run stage step of Document Tree")
        # Validate steps
        if steps < 1:
            raise ValueError("steps must be >= 1")

        # Pack current args to detect arg changes
        current_args = (input_answer, cmd_list_key, text_batch_key, marker_key,
                        edit_key, text_batch_reason_key, direct_cmd_update, copy_to_dict)

        # Initialize state storage on self if missing
        if not hasattr(self, "_udtas_state"):
            self._udtas_state = {
                "stack": [],            # LIFO stack of pending stage actions
                "total_processed": 0,   # total processed across this session
                "args": None            # last used args tuple
            }

        # If reset requested or args changed, re-initialize the stack
        if reset or self._udtas_state["args"] != current_args:
            tasks = self.getCurrentManager().getAllTasksByTagFromTaskList("input_summary", self.getCurrentManager().getTasks())
            for task in tasks:
                print(f"Unlink {task.getName()}")
                self.getCurrentManager().setCurrentTask(task)
                self.makeTaskAction("","","Unlink","")
            tasks = self.getCurrentManager().getAllTasksByTagFromTaskList("marker", self.getCurrentManager().getTasks())
            prio = 0
            taskname= ""
            for task in tasks:
                if task.getTreeIdx() > prio or taskname == "":
                    taskname = task.getName()
                    prio = task.getTreeIdx()
            if taskname == "":
                print(f"Can't get prio in {len(tasks)} task(s)")
                return {}
            self.createSecondStageLink(taskname=taskname,input_summary="input_summary")
            # call the single-step internal to get top-level next_stages
            top_next = self.runDocTreeStageInternal(
                input_answer, cmd_list_key, text_batch_key, marker_key,
                edit_key, text_batch_reason_key, direct_cmd_update, copy_to_dict
            ) or []
            # use reversed order on stack so first returned child is processed first (depth-first)
            self._udtas_state["stack"] = list(reversed(list(top_next)))
            self._udtas_state["total_processed"] = 0
            self._udtas_state["args"] = current_args

        stack = self._udtas_state["stack"]
        processed_actions = []

        # Run up to `steps` stage-actions
        for _ in range(steps):
            if not stack:
                print("Nothing to process")
                break  # nothing left to process
            else:
                print(f"Stack:\n{stack}")

            stage_action = stack.pop()
            # Apply the action (side effects expected)
            self.getJsonCustomCmd(stage_action)
            processed_actions.append(stage_action)
            self._udtas_state["total_processed"] += 1

            # After applying, get immediate children for this new state (single-step internal)
            new_next = self.runDocTreeStageInternal(
                input_answer, cmd_list_key, text_batch_key, marker_key,
                edit_key, text_batch_reason_key, direct_cmd_update, copy_to_dict
            ) or []

            # push children onto stack reversed so first child is processed first next time
            if new_next:
                stack.extend(reversed(list(new_next)))

        result = {
            "processed_actions": processed_actions,
            "processed_count": len(processed_actions),
            "total_processed": self._udtas_state["total_processed"],
            "remaining": len(stack),
            "finished": len(stack) == 0,
            "stack_preview": list(reversed(stack[-10:]))  # show next up to 10 in processing order
        }
        return result



    def runDocTreeStageInternal(self,
                                   input_answer: str = "input_answer",
                                   cmd_list_key: str = "text_edits",
                                   text_batch_key: str = "proposed_text_batch",
                                   marker_key: str = "reference_marker",
                                   edit_key: str = "edit_type",
                                   text_batch_reason_key: str = "justification_for_edit",
                                   direct_cmd_update: bool = True,
                                   copy_to_dict: bool = False,
                                   update_times : int = 1
                                   ):
        """
        Single-step function: calls updateTreeUsingAnswer(...) once and returns the
        next stages (list). DOES NOT recurse. This makes it handy for stepping
        through the algorithm manually.
        """
        print("Run Doc Tree Stage internal")
        self.updateAllnTimes(update_times)
        next_stages = self.getDocTreeCommands(
            input_answer, cmd_list_key, text_batch_key, marker_key,
            edit_key, text_batch_reason_key, direct_cmd_update, copy_to_dict
        )
        # ensure a list (caller expects iterable)
        if next_stages is None:
            return []
        return list(next_stages)
    

    
    def getDocTreeCommands( self, input_answer : str = "input_answer", cmd_list_key : str = "text_edits",
                                text_batch_key : str = "proposed_text_batch", marker_key : str = "reference_marker", 
                                edit_key : str = "edit_type",
                                text_batch_reason_key : str = "justification_for_edit",
                                direct_cmd_update : bool = True,
                                copy_to_dict : bool = False
                              ):
        print("Update tree using answer")
        next_stage_actions = []
        man = self.getCurrentManager()

        exttree = self.getMainExternalTree()

        target = exttree

        answer_task = None
        answers = man.getAllTasksByTagFromTaskList( input_answer, target.getAllChildChains())
        if len(answers) == 1:
            answer_task = answers[0]
        elif len(answers) == 0:
            print(f"No task with tag {input_answer} for {target.getName()}")
            return next_stage_actions
        else:
            answer_task = answers[0]
            distance = answer_task.getDistance( target )
            for task in answers:
                if not task.is_freeze:
                    temp_d = task.getDistance( target )
                    if distance > temp_d:
                        distance = temp_d
                        answer_task = task
        if not answer_task:
            print("No answers")
            return next_stage_actions
        try:
            # answer_data = json.loads( answer_task.getLastMsgContent() )
            print(f"Answer task: {answer_task.getName()}")
            ares, answer_data = Loader.Loader.loadJsonFromText( answer_task.getLastMsgContent2() )
            if not ares:
                print(f"Break:\n{answer_task.getLastMsgContent2()}")
                return next_stage_actions
        except:
            print(f"Break:\n{answer_task.getLastMsgContent2()}")
            return next_stage_actions
        # command_to_execute = []
        # listener_to_up = []
        if isinstance(answer_data, dict) and cmd_list_key in answer_data and isinstance(answer_data[cmd_list_key], list):
            print(f"Check {len(answer_data)} updates in document")
            for update in answer_data[cmd_list_key]:
                if edit_key in update and text_batch_key in update  and marker_key in update:
                    edit_type = update[edit_key]
                    batch = update[text_batch_key]
                    reason = ""
                    if text_batch_reason_key in update:
                        reason = update[text_batch_reason_key]
                    if len(update[marker_key]) and update[marker_key][0] == "[":
                        shortname = update[marker_key][1:-1]
                    else:
                        shortname = update[marker_key]
                    res, targettaskname = man.getLongNameUsingShortName( shortname )
                    if res:
                        CommandTool.parseEditInsert( targettaskname, man, edit_type, direct_cmd_update, copy_to_dict, reason, batch, next_stage_actions)
                    else:
                        print(f"No task with {shortname} name")
                else:
                # if edit_key in update and text_batch_key in update  and marker_key in update:
                    print("No valid json for cmd:")
                    print(f"edit_key({edit_key}):{edit_key in update}")
                    print(f"text_batch_key({text_batch_key}):{text_batch_key in update}")
                    print(f"marker_key({marker_key}):{marker_key in update}")
        else:
            print(f"No json data in {answer_task.getName()}:\n{answer_data}")
        return next_stage_actions
    
    
    def extendQuestionRoute( self, man : Manager.Manager, question_tree : BaseTask, input_summary = "input_summary", input_dir = "input_dir" ):
        print("Start Extending")
        target = None
        for task in man.getAllTasksByTagFromTaskList(input_dir, question_tree.getAllChildChains() ):
            if len(task.getChilds()) == 0:
                target = task
        if not target:
            print(f"No target for {question_tree.getName()}:\n{[t.getName() for t in man.getAllTasksByTagFromTaskList(input_dir, question_tree.getAllChildChains() )]}")
            return
        summary_task = None
        inputs = man.getAllTasksByTagFromTaskList( input_summary, target.getAllParents())
        if len(inputs) == 1:
            summary_task = inputs[0]
        elif len(inputs) == 0:
            print("No input")
            return
        else:
            summary_task = inputs[0]
            distance = summary_task.getDistance( target )
            for task in inputs:
                temp_d = task.getDistance( target )
                if distance > temp_d:
                    distance = temp_d
                    summary_task = task
                print(f"{task.getName()}: {distance} node(s)")

        print(f"Select {target.getName()}")

        man.setCurrentTask(target)
        man.addCurrTaskToSelectList()
        print(f"Select {summary_task.getName()}")
        man.setCurrentTask( summary_task )
        self.makeTaskAction( 
                prompt="",
                type1='Request',
                creation_type='Edit',
                creation_tag='user',
                param={
                    "extedit": True,
                    "copy_editbranch": False,
                    "resp2req": False,
                    "coll2req": False,
                    "read2req": False,
                    "run2req": False,
                    "in": True,
                    "out": True,
                    "link": True,
                    "av_cp": False,
                    "sel2par": True,
                    "ignrlist": False,
                    "wishlist": False,
                    "upd_cp": False,
                    "onlymulti": False,
                    "reqSraw": False,
                    "forcecopyresp": False,
                    "check_man": False,
                    "dont": False,
                    "switch": [],
                    "trg_tasks": [
                    "AllTasks"
                    ]
                    },
                save_action=True                
                )



    def breakBranchOnParts(self, taskname : str, treestarttask = "SetOptions", listener = "Listener", 
                           summary = "summary,output", marker="marker", node = "node", input_summary = "input_summary", input_dir = "input_dir"):
        man = self.getCurrentManager()
        trg = man.getTaskByName( taskname )

        mainoutputtasktree = None

        for task in man.getTasks():
            if task.checkType("ExternalInput"):
                mainoutputtasktree = task
        if not mainoutputtasktree:
            return

        tree_param = {"task_params":[]}
        srctree = trg.getRootParent()
        tres, tparam = srctree.getParamStruct("tree_step", True)
        if tres:
            trg_idx = tparam.get("idx", 6)
            eres, eparam = mainoutputtasktree.getParamStruct("tree_step", True)
            if eres and eparam["idx"] < (trg_idx + 3):
                mainoutputtasktree.updateParamStruct(param_name='tree_step',key='idx', val=(trg_idx + 3))

            srcdoctree_idx = { "type": "tree_step", "idx": trg_idx, "target": ""}
            intertree_idx = { "type": "tree_step", "idx": trg_idx + 1, "target": ""}
            intertree2_idx = { "type": "tree_step", "idx": trg_idx + 2, "target": ""}

 
        trg_childs = trg.getAllChildChains()
        summary_task = man.getTaskByTagFromTasks(summary, trg_childs)
        marker_task = man.getTaskByTagFromTasks(marker, trg_childs)
        node_task = man.getTaskByTagFromTasks(node, trg_childs)

        if not summary_task or not marker_task or not node_task:
            return

        

        newbud : BaseTask = trg.getParent()
        outtask = self.getMainOutput(marker_task)
        if not outtask:
            # or check summary task
            outtask = self.getMainOutput(summary_task)
            if not outtask:
                return
            if trg.checkType("Listener"):
                tree_param['task_params'].append({ "type":"tag","text": "intertree","key": ""})
                tree_param['task_params'].append(intertree_idx)
            else:
                tree_param['task_params'].append({ "type":"tag","text": "srcdoctree","key": ""})
                tree_param['task_params'].append(srcdoctree_idx)

            self.makeTaskAction(prompt="", type1=treestarttask, creation_type="New",creation_tag="user", param=tree_param, save_action=True)

            if not trg.checkType("Listener"):
                self.makeTaskAction("","Listener","SubTask","user",[{ "type":"tag","text": "additional, context","key": ""}])
                man.setTaskKeyValue("listener","onupdate","none")


            man.addCurrTaskToSelectList()
            man.setCurrentTask(trg)
            self.makeTaskAction("","","Parent","",{"select": man.getSelectedTask().getName()})
            man.setCurrentTask(newbud)
            man.addCurrTaskToSelectList()
            man.setCurrentTask(node_task)
            self.copyBranchToSelectedTask()
            if trg.checkType("Listener"):
                self.extendQuestionRoute(man, mainoutputtasktree, input_summary, input_dir)
            return
        
        intask = None
        for task in outtask.getHoldGarlands():
            intask = task
            break
        if self.checkOnSrcMarkerToChoiser( trg, intask ):
            tree_param['task_params'].append(intertree2_idx)
            tree_param['task_params'].append({ "type":"tag","text": "intertree","key": ""})
            tree_param['task_params'].append({ "type":"summary","text": "intermediate"})
            print(f"Create midtree as {treestarttask}")
            self.makeTaskAction(prompt="", type1=treestarttask, creation_type="New",creation_tag="user", param=tree_param, save_action=True)
            intertree = man.getCurrentTask()
            self.makeTaskAction(prompt="", type1=listener, creation_type="SubTask",creation_tag="user", param={}, save_action=True)
            interINtask = man.getCurrentTask()
            
            man.addCurrTaskToSelectList()

            man.setCurrentTask(node_task)

            print(f"Copy from Current task: {man.getCurrentTask().getName()}")
            print(f"To Selected task: {man.getSelectedTask().getName()}")
 

            self.makeTaskAction( 
                prompt="",
                type1='Request',
                creation_type='Edit',
                creation_tag='user',
                param={
                    "extedit": True,
                    "copy_editbranch": False,
                    "resp2req": False,
                    "coll2req": False,
                    "read2req": False,
                    "run2req": False,
                    "in": False,
                    "out": False,
                    "link": False,
                    "av_cp": False,
                    "sel2par": True,
                    "ignrlist": False,
                    "wishlist": False,
                    "upd_cp": False,
                    "onlymulti": False,
                    "reqSraw": False,
                    "forcecopyresp": False,
                    "check_man": False,
                    "dont": False,
                    "switch": [],
                    "trg_tasks": [
                    "AllTasks"
                    ]
                    },
                save_action=True                
                )


            # self.makeTaskAction(prompt="", type1=request, creation_type="SubTask",creation_tag="user", param={}, save_action=True)

            interOUTtask = man.getTaskByTagFromTasks(marker, interINtask.getAllChildChains())

            man.setCurrentTask(intask)

            self.makeTaskAction("","","Unlink","")

            print(f"Link {summary_task.getName()} -> {interINtask.getName()}")

            self.makeTaskAction(prompt="", type1="", creation_type="Link", creation_tag= "" , param={
                "select":summary_task.getName(),
                "curr":interINtask.getName()}, save_action=True)

            print(f"Link {interOUTtask.getName()} -> {intask.getName()}")

            self.makeTaskAction(prompt="", type1="", creation_type="Link", creation_tag= "", param={
                "select":interOUTtask.getName(),
                "curr":intask.getName()}, save_action=True)
            
            man.setCurrentTask(interOUTtask)

            tst_param = {"task_params":[]}
            if trg.checkType("Listener"):
                tst_param['task_params'].append({ "type":"tag","text": "intertree","key": ""})
                tst_param['task_params'].append(intertree_idx)
                tst_param['task_params'].append({ "type":"summary","text": "intermediate"})
            else:
                tst_param['task_params'].append({ "type":"tag","text": "srcdoctree","key": ""})
                tst_param['task_params'].append(srcdoctree_idx)
                tst_param['task_params'].append({ "type":"summary","text": "source"})
            
            
            print(f"Create midtree as {treestarttask}")

            self.makeTaskAction(prompt="", type1=treestarttask, creation_type="New",creation_tag="user", param=tst_param, save_action=True)
            
            # newparttree = man.getCurrentTask()

            man.addCurrTaskToSelectList()

            man.setCurrentTask(trg)

            print(f"Set {man.getCurrentTask().getName()} as child of {man.getSelectedTask().getName()}")
            self.makeTaskAction("","","Parent","",{"select": man.getSelectedTask().getName()})

            man.addTaskToSelectList(newbud)

            print(f"Copy from Current task: {man.getCurrentTask().getName()}")
            print(f"To Selected task: {man.getSelectedTask().getName()}")
            man.setCurrentTask(node_task)

            self.copyBranchToSelectedTask()

            self.extendQuestionRoute(man, mainoutputtasktree, input_summary, input_dir)

            # newbud_summary = man.getTaskByTagFromTasks(summary, newbud.getAllChildChains())

    def copyBranchToSelectedTask( self ):
        self.makeTaskAction( 
                prompt="",
                type1='Request',
                creation_type='Edit',
                creation_tag='user',
                param={
                    "extedit": True,
                    "copy_editbranch": False,
                    "resp2req": False,
                    "coll2req": False,
                    "read2req": False,
                    "run2req": False,
                    "in": True,
                    "out": True,
                    "link": True,
                    "av_cp": True,
                    "sel2par": True,
                    "ignrlist": False,
                    "wishlist": False,
                    "upd_cp": False,
                    "onlymulti": False,
                    "reqSraw": False,
                    "forcecopyresp": False,
                    "check_man": False,
                    "dont": False,
                    "switch": [],
                    "trg_tasks": [
                    "AllTasks"
                    ]
                    },
                save_action=True                
                )

    def getMainExternalTree( self ):
        man = self.getCurrentManager()
        mainoutputtasktree = None

        for task in man.getTasks():
            if task.checkType("ExternalInput"):
                mainoutputtasktree = task
        return mainoutputtasktree


    def updateTaskAndTravel( self, info_tag = "travel_summary", answer_tag = "travel_answer", add_json_list_tag = "add", add_marker = "marker", edit_json_list_tag = "add", edit_marker = "marker", 
                            command = "[{\"action\": \"updateAllnTimes\", \"kwargs\": {\"n\": 1, \"check\": true}}]" ):
        man = self.getCurrentManager()
        mainoutputtasktree = None

        for task in man.getTasks():
            if task.checkType("ExternalInput"):
                mainoutputtasktree = task
        if not mainoutputtasktree:
            return
        
        
        info_task = man.getTaskByTag( info_tag )
        init_info_task = man.getTaskByTag( info_tag )
        answer_task = man.getTaskByTag ( answer_tag )

        # if mainoutputtasktree not in init_info_task.getAllParents():
            # return

        if len(init_info_task.getGarlandPart()) == 0:
            return
        
        currentlink_task = None
        
        for task in init_info_task.getGarlandPart():
            currentlink_task = task
            break

        if not currentlink_task:
            return
    
        self.getJsonCmd(command)

        ares, answer_result = Loader.Loader.loadJsonFromText( answer_task.getLastMsgAndParentMessage() )
        if not ares:
            return
        
        add_task_names = []
        if add_json_list_tag in answer_result and isinstance( answer_result[add_json_list_tag], list ):
            for answer_pack in answer_result[add_json_list_tag]:
                if add_marker in answer_pack:
                    short_name = answer_pack[add_marker]
                    fres, full_name = man.getAndCheckLongName( short_name )
                    if fres:
                        add_task_names.append(full_name)

    def createSecondStageLink ( self, taskname : str, summary = "marker", input_summary = "input_addlink" ):
        print(f"Create Second Stage Link with `{taskname}` name:\n{summary}\n{input_summary}")
        man = self.getCurrentManager()
        mainoutputtasktree = None

        for task in man.getTasks():
            if task.checkType("ExternalInput"):
                mainoutputtasktree = task
        if not mainoutputtasktree:
            return
        
        self.travelAndLink(taskname, mainoutputtasktree, man, summary, input_summary)
 

    def travelAndLink( self, taskname : str, previous_summary_task : BaseTask, man : Manager.Manager, 
                      marker = "marker", input_summary = "input_summary" 
                      ):
        linked_task = man.getTaskByName( taskname )
        if linked_task == None:
            print(f"No task with `{taskname}` name in manager ({man.getPath()})")
            return

        output_task = None

        for task in linked_task.getGarlandPart():
            output_task = task
            break

        if not output_task:
            print(f"No output task: try to find closest")
            marker_output_task = linked_task

        else:
        
            output_tree = output_task.getRootParent()

            marker_output_task = man.getTaskByTagFromTasks(marker, output_tree.getAllChildChains())

        summary_input_task = None

        for task in man.getAllTasksByTagFromTaskList(input_summary, previous_summary_task.getAllChildChains()):
            if len(task.getGarlandPart()) == 0:
                summary_input_task = task
                break

        if not summary_input_task:
            print(f"No summary task")
            return
        
        print(f"Link form {marker_output_task.getName()} to {summary_input_task.getName()}")

        self.makeTaskAction(prompt="", type1="", creation_type="Link", creation_tag= "" , param={
                "select":marker_output_task.getName(),
                "curr":summary_input_task.getName()}, save_action=True)
        
        man.setCurrentTask(marker_output_task)


    def updateDocTrees( self, single = False, update_copy = True, input_cmd = "srcdoctree", doc_tag = "full_doc", summary_task_tag = "insert, edit, summary, command", result_task_tag = "result, summary, command"):
        print(f"Update doc trees")
        man = self.getCurrentManager()
        cmdsummary_task = man.getTaskByTag( summary_task_tag )
        if not cmdsummary_task:
            return

        doctrees = man.getAllTasksByTagFromTaskList(input_cmd, man.getTasks())
        for start in doctrees:
            print(f"Get branch from {start.getName()}")
            init_tasks = start.getAllChildChains()
            full_doc_task = man.getTaskByTagFromTasks(doc_tag, init_tasks).getParent()
            for task in full_doc_task.getAllChildChains():
                if task != full_doc_task and task in init_tasks:
                    init_tasks.remove( task )
            print(f"Process tasks: {[t.getName() for t in init_tasks]}")
            for task in init_tasks:
                print(f"For {task.getName()} task")
                if task.checkDictBuffer():
                    print(f"Move task {cmdsummary_task.getName()} to {task.getName()} ")
                    man.setCurrentTask(cmdsummary_task)
                    self.makeTaskAction("","","Parent","",{"select": task.getName()})
                    man.setCurrentTask( cmdsummary_task )
                    if update_copy:
                        self.updateFromFork()
                        result_task = man.getTaskByTagFromTasks(result_task_tag, cmdsummary_task.getAllChildChains())
                        jres, jcmd = Loader.Loader.loadJsonFromText(result_task.getLastMsgContent2())
                        if jres and isinstance(jcmd, list):
                            print(f"Apply {len(jcmd)} commands")
                            task.clearAutoCommand2param()
                            for cmd in jcmd:
                                print(f"Copy command")
                                task.updateAutoCommand2param(cmd)
                        else:
                            print(f"No command")
                        task.clearDictBuffer()
                    if single:
                        print(f"Single step was executed")
                        return
                else:
                    print(f"Ignore")

    def createDocTreeTags( self, target = "current_task" ):
        print("Create Doc Tree")
        if target == "current_task":
            param_template = {"type":"tag","text":"","key":""}
            task = self.getCurrentManager().getCurrentTask()
            initial_node_task = task

            root = task.getRootParent()

            param_template["text"] = "srcdoctree"
            root.setParamStruct(param_template)

            param_template["text"] = "insert,autogenerate"
            task.setParamStruct(param_template)

            self.makeTaskAction("","SetOptions","SubTask","user")
            task = self.getCurrentManager().getCurrentTask()
            param_template["text"] = "full_doc"
            task.setParamStruct(param_template)
            start_doc_task = task

            self.makeTaskAction("","Request","SubTask","user")
            end_doc_task = self.getCurrentManager().getCurrentTask()

            self.getCurrentManager().setCurrentTask(initial_node_task)
            self.makeTaskAction("","SetOptions","SubTask","user")
            task = self.getCurrentManager().getCurrentTask()
            param_template["text"] = "node"
            task.setParamStruct(param_template)
            start_marker_task = task

            self.makeTaskAction("","Request","SubTask","user")
            task = self.getCurrentManager().getCurrentTask()
            param_template["text"] = "marker"
            task.setParamStruct(param_template)
            end_marker_task = task


            self.makeTaskAction("","ExternalInput","New","user")

            self.getCurrentManager().addTaskToSelectList(end_marker_task)

            self.getCurrentManager().createTreeOnSelectedTasks("SubTask","Listener")

            task = self.getCurrentManager().getCurrentTask()
            param_template["text"] = "input_summary"
            task.setParamStruct(param_template)
            input_summary_task = task
            
            
            self.makeTaskAction("","Request","SubTask","user")
            task = self.getCurrentManager().getCurrentTask()
            param_template["text"] = "input_dir"
            task.setParamStruct(param_template)
            input_dir_task = task

            self.getCurrentManager().setCurrentTask(input_summary_task)

            # self.getCurrentManager().setCurrentTask(input_dir_task)

            param_template["text"] = "input_answer"
            # self.makeTaskAction("","Request","SubTask","user")
            self.makeTaskAction("","Request","SubTask","user", {"task_params":[param_template]})
            task = self.getCurrentManager().getCurrentTask()
            # task.setParamStruct(param_template)
 
            self.makeTaskAction("[[current:param:format:result]]","Request","SubTask","user")
            task = self.getCurrentManager().getCurrentTask()
            task.setParamStruct({
                    "type":"format",
                    "target":"[[parent_2:msg_content]]",
                    "description":"{ \"proposed_text_batch\":{\"prefix\":\"# Proposal\n\",\"suffix\":\"\n\"}, \"justification_for_edit\":{\"prefix\":\"# Reason\n\",\"suffix\":\"\n\"}, \"target_field_key\":{\"reference_marker\":\"[Rq1637]\"} }"
                    })

            param_template["text"] = "input_cmd"
            self.makeTaskAction("","Request","SubTask","user", {"task_params":[param_template]})
            task = self.getCurrentManager().getCurrentTask()
            # task.setParamStruct(param_template)
            
            
            self.makeTaskAction("","SetOptions","New","user")
            self.getCurrentManager().addTaskToSelectList(end_doc_task)
            self.getCurrentManager().createTreeOnSelectedTasks("SubTask","Listener")
            param_template["text"] = "output_doc"
            self.makeTaskAction("","Request","SubTask","user", {"task_params":[param_template]})

    # def createTaskTreeBasedFromJsonFiles( self, jsonfiletype = "function"):
    #     paths = Loader.Loader.getFilePathsByBrowsing()
    #     for path in paths:
    #         self.createTaskTreeBasedOnJsonFile( path )

    def updateTreeTasksJsonFile (self):
        man = self.getCurrentManager()
        externalinput_task = man.getTaskByTag("main,external")
        if not externalinput_task:
            print("No external")
            return
        else:
            if not externalinput_task.checkType("ExternalInput"):
                print("Diff type")
                return
        jres, jparam = externalinput_task.getParamStruct("json_project_data", True)
        if jres and "path_to_json_file" in jparam and "path_to_archive" in jparam:
            # path_to_project_json = jparam["path_to_json_file"]
            # folderpath = Loader.Loader.getFileFolder(path_to_project_json)
            # name = self.getManagerSpaceName( man ) + "_gs"
            manager_path = self.getManagerFolderPath( man )
            # Archivator.Archivator.saveAllbyName(manager_path, folderpath, name)
            Archivator.Archivator.saveAllbyPath(manager_path, externalinput_task.findKeyParam( jparam["path_to_archive"] ))

    def saveGenslidesArchiveInFolder(self, path_to_folder: str): 
        man = self.getCurrentManager()
        manager_path = self.getManagerFolderPath( man )
        name = f"{self.getManagerSpaceName( man )}_gs"
        return Archivator.Archivator.saveAllbyName(manager_path, path_to_folder, name)
    
    def saveGenslidesArchiveByPath( self, path_to_file : str):
        man = self.getCurrentManager()
        manager_path = self.getManagerFolderPath( man )
        return Archivator.Archivator.saveAllbyPath( manager_path, path_to_file )
    
    def convertJsonFileToTemplateTreeTasks( self, path_to_default_7z, path_to_project_json ):
        path_to_default_7z = Loader.Loader.getUniPath( path_to_default_7z )
        path_to_project_json = Loader.Loader.getUniPath( path_to_project_json )
        data = ReadFM.ReadFileMan.readJson( path_to_project_json )
        if "version" not in data:
            print("No version")
            return ""
        body_tag = "body"
        if data.get("converted", False) and "genslides_project_file" in data and FileManager.checkExistPath(data["genslides_project_file"]):
            print(f"Load from project file: {data['genslides_project_file'] }")
            self.loadManagerProjectFromFile ( data["genslides_project_file"] )
            return data["genslides_project_file"]
        elif "targets" in data and isinstance(data["targets"], list): 
            print(f"Fisrt loading")
            # first loading
            self.loadManagerProjectFromFile ( path_to_default_7z )
            man = self.getCurrentManager()
            srctree_task = man.getTaskByTag("srcdoctree,start")
            if srctree_task == None:
                print("No src tree task")
                return
            start_task = man.getTaskByTagFromTasks("additional, context", srctree_task.getAllChildChains())
            externalinput_task = man.getTaskByTag("main,external")
            if not externalinput_task:
                print("No external")
                return
            else:
                if not externalinput_task.checkType("ExternalInput"):
                    print("Diff type")
                    return
            if start_task == None:
                print("No start task")
                return
                # param_template = {"type":"tag","text":"","key":""}
                # param_template["text"] = ",".join(["srcdoctree",data.get("filename","")])
                # self.makeTaskAction("","SetOptions","New","user", {"task_params":[param_template]})
                # start_task = man.getCurrentTask()
            else:
                man.setCurrentTask(start_task)
            prev_task_name = start_task.getName()
            for pack in data["targets"]:
                if body_tag in pack:
                    if len(start_task.getChilds()):
                        child = start_task.getChilds()[0]
                        man.setCurrentTask( child )
                        tags = [start_task.getName(),pack.get("type","")]
                        if "name" in pack:
                            tags.append(pack["name"])
                        if "parent_target" in pack:
                            tags.append(pack["parent_target"])
                        
                        task_tag_param = {"type":"tag",
                                          "text":",".join(tags),
                                          "key":""}

                        self.makeTaskAction(pack[body_tag],"Request","Insert","user",{"task_params":[task_tag_param]})
                        pack["parent_task"] = prev_task_name
                        prev_task_name = man.getCurrentTask().getName()
            folderpath = Loader.Loader.getFileFolder(path_to_project_json)
            name = Converter.getGenslidesArchiveFileNameBasedOnJson( path_to_project_json )
            manager_path = self.getManagerFolderPath( man )
            data["src_project_path"] = manager_path
            path_to_created_project_file = Archivator.Archivator.saveAllbyName(manager_path, folderpath, name)
            data["genslides_project_file"] = path_to_created_project_file
            data["converted"] = True
            externalinput_task.setParamStruct({
                "type":"json_project_data",
                "path_to_archive": Loader.Loader.getManRePath(path_to_created_project_file, manager_path),
                "path_to_json_file": Loader.Loader.getManRePath(path_to_project_json, manager_path),
                "path_to_json_file_raw": path_to_project_json,
                "path_to_template": Loader.Loader.getManRePath(path_to_default_7z, manager_path)
                })
            externalinput_task.saveAllParams()
            Writer.writeJsonToFile(path_to_project_json, data, indent=4)
            return path_to_created_project_file
        return ""



    def copyTaskFromManagerToManager( self, src : Manager.Manager, dst : Manager.Manager, tasks : list[BaseTask], param : dict ):
        for task in tasks:
            if param.get('reqSraw', False ):
                prompt=task.getPromptContentForCopyConverted() 
            else:
                prompt=task.getPromptContentForCopy() 
            prompt_tag=task.getLastMsgRole()
            trg_type = task.getType()
            param_task = task.copyAllParams(True)
            prio = task.getPrio()

            parent_name = task.getParent().getName()

            parent = dst.getTaskByName ( parent_name )

            start_task = dst.getCurrentTask()

            dst.createOrAddTask(prompt, trg_type, prompt_tag, parent, param_task)

            if start_task != dst.getCurrentTask():
                dst.getCurrentTask().setPrio(prio)
                if param.get('forcecopyresp', False ):
                    if dst.getCurrentTask().checkType('Response'):
                        dst.getCurrentTask().forceSetPrompt(prompt)


    def getManagerSpaceName( self, man : Manager.Manager):
        return finder.findByKey("[[manager:path:spc:name]]", man, man.curr_task, man.helper )
    def getManagerFolderPath( self, man : Manager.Manager):
        return Loader.Loader.getUniPath( finder.findByKey("[[manager:path:spc]]", man, man.curr_task, man.helper ) )

    def loadFromArchive( self, path_to_template, sync = True, archive_save_path = ""):
        path = Loader.Loader.getUniPath( path_to_template )
        autoload_result = self.loadManagerProjectFromFile( path )
        if autoload_result:
            if sync:
                self.syncRelatedActionersWithFolder()
            if archive_save_path != "":
                self.saveGenslidesArchiveByPath( archive_save_path )
        return autoload_result

    def loadManagerProjectFromFile(self, template_path, safe_load_tasks = True, load_managers_tasks = True):
        print("Load manager project from file")
        self.setManager(self.std_manager)
        man = self.getCurrentManager()
        target_path = man.getPath()
        name = self.getManagerSpaceName( man )
        # name = finder.findByKey("[[manager:path:spc:name]]", man, man.curr_task, man.helper )
        self.saveManToTmp(man, "tt_"+ SaveData.getTimeForProjectName(), ["tt_temp",f"{self.rsrvd_tmp_prefix}{name}{self.rsrvd_tmp_suffix}"], check_oldest=True, max_files= 10)
        if not FileManager.checkExistPath(template_path):
            print(f"Abort: path is not exist ({template_path})")
            return False
        FileManager.deleteFiles(target_path)
        if not Archivator.Archivator.extract7zFileToFolder(template_path, target_path):
            print("Abort: error on load archive")
            return False
        self.reset()
        self.setCurrentManager( self.std_manager )
        man = self.getCurrentManager()
        man.onStart()
        man.initInfo(method = self.loadExtProject, path = self.getPath())
        if load_managers_tasks:
            man.disableOutput2()
            man.loadTasksList(safe_load_tasks)
            man.enableOutput2()
            self.loadTmpManagers()
        return True
    
    def syncRelatedActionersWithFolder( self ):
        self.loadExtTreeTaskActioners()
        act_paths = self.getRelatedActionersPaths([])
        print(f"syncRelatedActionersWithFolder:{act_paths}")
        method_to_external_actioners = self.parameters.get("available_actioners",None)
        if method_to_external_actioners != None:
            for act in method_to_external_actioners():
                if act.getPath() in act_paths:
                    print(f"Sync with folder {act.getPath()}")
                    act.syncWithCurrentFolder()
            for act in method_to_external_actioners():
                if act.getPath() in act_paths:
                    act.loadExtTreeTaskActioners()
        else:
            print(f"No methods in {self.parameters}")

    def syncExtTreeTaskPath( self, path, init ):
        report = [f"syncExtTreeTaskPath:{self.getPath()}"]
        for task in self.getCurrentManager().getTasks():
            if task.checkActionerTaskPath( init ):
                report.append(f"Sync task {task.getName()} with {path}")
                task.setActionerTaskPath( path )
        return "\n".join(report)

    def moveFromCurrentToAnother( self, trg_path : str, autoload = True):
        self.setCurrentManager(self.std_manager)
        start_path = self.getCurrentManager().getPath()
        print(f"Move from {start_path} to {trg_path}")
        FileManager.copyFiles(start_path, trg_path)
        self.getCurrentManager().setPath( trg_path )
        self.setPath( trg_path )
        self.syncWithCurrentFolder()
        if autoload:
            self.syncRelatedActionersWithFolder()

    
    def syncWithCurrentFolder( self, safe_load_tasks = True, load_managers_tasks = True):
        self.reset()
        self.setCurrentManager( self.std_manager )
        man = self.getCurrentManager()
        man.onStart()
        man.initInfo(method = None, path = self.getPath())
        if load_managers_tasks:
            man.disableOutput2()
            man.loadTasksList(safe_load_tasks)
            man.enableOutput2()
            self.loadTmpManagers()
 

    def loadTreeDoc( self, path_to_template, path_to_file ):
        # print(SaveData.getTimeForProjectName())
        self.convertJsonFileToTemplateTreeTasks( path_to_template, path_to_file )

    def saveTemporaryArchiveWithCheck( self, path, name, max_files = 10):
        fld_path = Loader.Loader.getUniPath( path )
        if not FileManager.checkAndCreateFolder(fld_path):
            return
        man = self.getCurrentManager()
        suffix = SaveData.getTimeForProjectName()
        path = Loader.Loader.getUniPath( finder.findByKey("[[manager:path:spc]]", man, man.curr_task, man.helper ) )
        trg_path = Loader.Loader.getUniPath( FileManager.addFolderToPath(fld_path, [name + "_" + suffix + ".7z"]))
        FileManager.manageOldestFolderFiles(fld_path, max_files)
        Archivator.Archivator.saveAllbyPath(data_path=path, trgfile_path=trg_path)


    def get_TT_TemporaryArchiveFolder( self ):
        return self.getTemporaryArchiveFolder( temp_folder = ["tt_temp"] )

    def getTemporaryArchiveFolder( self, temp_folder ):
        man = self.getCurrentManager()
        folder = finder.findByKey("[[manager:path:fld]]", man, man.curr_task, man.helper )
        fld_path = Loader.Loader.getUniPath( FileManager.addFolderToPath(folder, temp_folder))
        return fld_path


    def saveManToTmp(self, man : Manager.Manager, suffix = "", temp_folder = ["tt_temp"], check_oldest = False, max_files = 3):
        path = Loader.Loader.getUniPath( finder.findByKey("[[manager:path:spc]]", man, man.curr_task, man.helper ) )
        # folder = finder.findByKey("[[manager:path:fld]]", man, man.curr_task, man.helper )
        name = finder.findByKey("[[manager:path:spc:name]]", man, man.curr_task, man.helper )
        # fld_path = Loader.Loader.getUniPath( FileManager.addFolderToPath(folder, temp_folder))
        fld_path = self.getTemporaryArchiveFolder(temp_folder)
        FileManager.createFolder(fld_path)
        trg_path = Loader.Loader.getUniPath( FileManager.addFolderToPath(fld_path, [name + "_" + suffix + ".7z"]))
        if check_oldest:
            FileManager.manageOldestFolderFiles(fld_path, max_files)
        Archivator.Archivator.saveAllbyPath(data_path=path, trgfile_path=trg_path)
        return trg_path

    def travelViaTextParts( self ):
        man = self.getCurrentManager()
        docstarttasks = man.getAllTasksByTagFromTaskList("srcdoctree,start", man.getTasks())
        docpartstasks = man.getAllTasksByTagFromTaskList("insert,autogenerate", man.getTasks())
        for docroot in docstarttasks:
            children = docroot.getAllChildChains()
            for task in docpartstasks:
                if task not in children:
                    pass

    def uniteTwoTaskByName(self, task_marker1, task_marker2):
        man = self.getCurrentManager()
        united = man.getTaskByAnyName( task_marker1 )
        removed = man.getTaskByAnyName( task_marker2 )
        if united != None and removed != None:
            if united in removed.getAllParents():
                text = united.getLastMsgContentRaw()
                text += removed.getLastMsgContentRaw()
            else:
                text = removed.getLastMsgContentRaw()
                text += united.getLastMsgContentRaw()
            man.setCurrentTask(united)
            selected_tag = united.getLastMsgRole()
            self.makeTaskAction(text, "Request", "Edit", selected_tag)
            man.setCurrentTask(removed)
            self.makeTaskAction("","","Remove","")
            return f"Union for {task_marker1} and {task_marker2} is done"
        return f"Error with {task_marker1} and {task_marker2}"
    
    def moveTask(self, marker, direction):
        man = self.getCurrentManager()
        start = man.getCurrentTask()
        target = man.getTaskByAnyName( marker )
        if target == None:
            return
        man.setCurrentTask(target)
        if direction == "UP":
            self.makeTaskAction("","","MoveCurrTaskUP","")
        elif direction == "DOWN":
            self.makeTaskAction("","","MoveCurrTaskDown","")
        man.setCurrentTask( start )
 
    def deleteTask( self, marker ):
        man = self.getCurrentManager()
        start = man.getCurrentTask()
        target = man.getTaskByAnyName( marker )
        if target == None:
            return
        man.setCurrentTask(target)
        self.makeTaskAction("","","Remove","")
        man.setCurrentTask( start )
 
    def getExtTreeTaskByNameExecuteJsonCmd( self, name : str, cmds_list : str ):
        task = self.getCurrentManager().getTaskByName(name)
        res, cmd = Loader.Loader.loadJsonFromText(cmds_list)
        if res and task != None:
            task.exeExTreeTaskCmds(cmd)

    def getExternalActionersList( self ):
        return self.parameters.get("available_actioners",None)

    def loadExtTreeTaskActioners(self):
        method_to_external_actioners = self.parameters.get("available_actioners",None)
        if method_to_external_actioners != None:
            for task in self.getCurrentManager().getTasks():
                task.loadActionerTasks(method_to_external_actioners())

    def loadExtTreeTaskActionersByTaskNames(self, names : str):
        method_to_external_actioners = self.parameters.get("available_actioners",None)
        if method_to_external_actioners != None:
            found = False
            for name in names:
                task = self.getCurrentManager().getTaskByName(name)
                if task != None:
                    task.loadActionerTasks(method_to_external_actioners())
                    found = True
            logger.info("Search for %s , found = %s", names, found)
        else:
            logger.critical("No method: %s ",method_to_external_actioners)

    def setSignToCurrentTask( self, currtaskname, trgtaskname ):
        man = self.getCurrentManager()
        task = man.getTaskByAnyName(currtaskname)
        if task != None:
            task.setSign(self.getPath(), trgtaskname)
    
    def resetSignOfCurrentTask( self, currtaskname ):
        man = self.getCurrentManager()
        task = man.getTaskByAnyName(currtaskname)
        if task != None:
            task.resetSign()

    def rejectSignedTaskReport( self, targettaskname = "", cmd = {}):
        man = self.getCurrentManager()
        task = man.getTaskByAnyName( targettaskname )
        if task != None:
            jres, jobj, jreport = Loader.Loader.loadJsonFromTextStr(task.getLastMsgContent())
            if jres and isinstance(jobj, list):
                jobj.append( cmd )
            else:
                jobj = [cmd]
            prompt = Loader.Loader.convJsonToText( jobj )
            init = man.getCurrentTask()
            man.setCurrentTask( task )
            self.editingAction( prompt )
            man.setCurrentTask( init )

    def getLabelDescriptions( self ):
        info = []
        for task in self.getCurrentManager().getTasks():
            res, data = task.getLabelDescription()
            if res:
                info.append({
                    "name":task.getName(),
                    "description": data
                })
        return info

    def exeExternalInputCommands( self, target : str = "", group_name : str = "updt"):
        if target == "":
            for task in self.getCurrentManager().getTasks():
                if task.isExternalInput():
                    self.getJsonCustomCmd( task.getJsonCmdGroup( group_name ) )
                    return
        else:
            task = self.getCurrentManager().getTaskByAnyName( target )
            if task != None and task.isExternalInput():
                self.getJsonCustomCmd( task.getJsonCmdGroup( group_name ) )

    def saveProjectByPath(self, path_to_file : str):
        path = self.getCurrentManager().getPath()
        path = Loader.Loader.getUniPath(path)
        trg_path = Loader.Loader.getUniPath( path_to_file )
        Archivator.Archivator.saveAllbyPath(data_path=path, trgfile_path=trg_path)

        return f"Save {path} to {trg_path}"

    def saveTargetExtTreeProjectToArchive( self, marker : str, path_to_file : str):
        task = self.getCurrentManager().getTaskByAnyName( marker )
        if task != None:
            return task.saveProjectByPath( path_to_file )
        return "Failed"

    def loadExtTreeProjectFromArchive( self, marker: str, path_to_template : str, sync :bool = True, archive_save_path : str = ""):
        task = self.getCurrentManager().getTaskByAnyName( marker )
        if task != None:
            return task.loadFromArchive( path_to_template, sync, archive_save_path)
        return "Failed"
 
