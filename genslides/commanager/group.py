from genslides.task.base import TaskManager, BaseTask
# from genslides.commanager.jun import Manager
import genslides.commanager.jun as Manager
import genslides.commanager.man as BaseMan

from genslides.utils.reqhelper import RequestHelper
from genslides.utils.testrequest import TestRequester
from genslides.utils.searcher import GoogleApiSearcher

import genslides.utils.filemanager as FileManager
import genslides.utils.finder as finder
import genslides.utils.loader as Loader
import genslides.task_tools.text as TextTool
import os
import json
import shutil
import graphviz

class Actioner():
    def __init__(self, manager : Manager.Manager) -> None:
        self.std_manager = manager
        self.setManager(manager)
        self.tmp_managers = []
        self.loadExtProject = manager.loadexttask
        # TODO: установить как значение по умолчанию
        self.path = 'saved'
        self.update_state = 'init'
        self.is_executing = False
        self.executing_man = None
        self.hide_task = True

        self.updateallcounter = 0

        self.is_updating = False

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

    def removeManager( self, manager : BaseMan.Jun):
        if manager in self.tmp_managers:
            manager.beforeRemove()
            self.tmp_managers.remove(manager)

    def reset(self):
        self.setManager(self.std_manager)
        self.tmp_managers : list[BaseMan.Jun] = []
        self.clearTmp()

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
            res, _ = task.getParamStruct("autocommander", True)
            if res:
                names.append(task.getName())
        return names
    
    def exeTasksByName(self, names):
        for name in names:
            task = self.manager.getTaskByName(name)
            res, actions = task.getAutoCommand()
            if res:
                for action in actions:
                    self.makeSavedAction(action)

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
            self.manager.setCurrentTaskByName(name=param['task'])
        elif creation_type == "SetSlctTask":
            self.manager.setSelectedTaskByName(name=param['task'])
        elif creation_type == "SetMultiTask":
            names = TextTool.convert_text_with_names_to_list(param['tasks'])
            for name in names:
                self.manager.addTaskToMultiSelectedByName(name)
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
            return self.manager.makeTaskActionBase(prompt, type1, creation_type, creation_tag, [])
        elif creation_type in self.manager.getSecdCommandList():
            return self.manager.makeTaskActionPro(prompt, type1, creation_type, creation_tag, [])
        elif creation_type == "MoveCurrTaskUP":
            return self.manager.moveTaskUP(self.manager.curr_task)
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
        print('From',src.info['task'], 'to', trg.info['task'])
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
        self.manager.setCurrentTaskByName(name)

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


    def updateStepInternal(self, update_task = True):
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
             

        next = man.updateSteppedSelectedInternal(update_task=update_task)
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
        if next:
            if len(next.getChilds()) == 0:
                print('Branch complete:', self.root_task_tree.getName(), '-', next.getName())

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
      
    def update(self, update_task = True):
        man = self.manager
        # print('Curr state:', self.update_state,'|task:',man.curr_task.getName())
        if self.update_state == 'init':
            self.updateInit()
        elif self.update_state == 'start tree':
            task = man.tree_arr[self.update_tree_idx]
            print('Start tree', task.getName(),'[',self.update_tree_idx,']')
            self.setStartParamsForUpdate(man, task)
            self.updateStepInternal(update_task=update_task)
        elif self.update_state == 'step':
            self.updateStepInternal(update_task=update_task)
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

        # out = self.updateUIelements()
        # return out

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
    def updateAllnTimes(self, n, check = False):
        self.getCurrentManager().disableOutput2()
        for i in range(n):
            print('UAT:', i)
            self.updateAll(force_check=check)
        self.getCurrentManager().enableOutput2()

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
        print('Frozen tasks cnt:', man.getFrozenTasksCount())
        man.curr_task = start_task

    def updateFromFork(self, force_check = False):
        man = self.getCurrentManager()
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


    def updateAll(self, force_check = False, update_task = True, max_update_idx = 10000):
        if self.is_updating:
            print('Abort',self.getPath,'cause: already updating')
            return
        else:
            self.is_updating = True
        man = self.manager
        print(f"Update all tasks of {man.getName()}")
        start_task = man.curr_task
        self.resetUpdate(force_check=force_check)
        if len(man.tree_arr) == 0:
            self.is_updating = False
            return
        idx = 0
        project_chain = [{'idx':idx, 'task': man.getCurrentTask()}]
        while(idx < max_update_idx):
            self.update(update_task=update_task)
            project_chain.append({'idx':idx, 'task': man.getCurrentTask()})
            if self.update_state == 'done':
                break
            idx += 1

        cnt = man.getFrozenTasksCount()
        print(f"Act [{man.getName()}] made {idx} step(s)\nFrozen: {cnt} of {len(man.task_list)} task(s)")
        man.saveInfo()
        man.curr_task = start_task

        self.updateallcounter += 1
        # out = man.getCurrTaskPrompts()
        # return out
        self.is_updating = False
        return project_chain


    def updateAllUntillCurrTask(self, force_check=False):
        man = self.manager
        start_task = man.curr_task
        self.resetUpdate(force_check=force_check)
        if len(man.tree_arr) == 0:
            return
        idx = 0
        while(idx < 1000):
            self.update()
            if self.update_state == 'done' or man.curr_task == start_task:
                break
            idx += 1
        print('Frozen tasks cnt:', man.getFrozenTasksCount())
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

   

    def drawGraph(self, only_current= True, max_index = -1, path = "output/img", hide_tasks = True, add_multiselect = False, max_childs = 3, add_linked=False, add_garlands=False, all_tree_task = False, out_childtask_max = -1):
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
            trg_list = man.task_list
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


            

            for task in trg_list:
                shape = "ellipse" #rectangle,hexagon
                if task.checkType('Response'):
                    shape = 'rectangle'
                elif task.drawAsRootTaskSymbol():
                    shape = 'invhouse'
                elif task.checkType('OutExtTree'):
                    shape = 'house'
                elif task.checkType('SetOption'):
                    shape = 'doubleoctagon'
                if task in trgs_rsm:
                    if task == man.curr_task:
                        f.node( task.getIdStr(), task.getNameForDrawing(),style="filled",color="blueviolet")
                    else:
                        f.node( task.getIdStr(), task.getNameForDrawing(),style="filled",color="darkmagenta")
                elif task.readyToGenerate():
                    color = 'darkmagenta'
                    f.node( task.getIdStr(), task.getNameForDrawing(),style="filled", color = color, shape = shape)
                elif task in man.multiselect_tasks:
                    color = "lightsalmon3"
                    if task == man.curr_task:
                        color = "lightsalmon1"
                    if len(task.getHoldGarlands()) > 0:
                        color = 'crimson'
                    f.node( task.getIdStr(), task.getNameForDrawing(),style="filled", color = color, shape = shape)
                elif task == man.curr_task:
                    color = "skyblue"
                    if len(task.getHoldGarlands()) > 0:
                        color = 'skyblue4'
                    f.node( task.getIdStr(), task.getNameForDrawing(),style="filled", shape = shape, color = color)
                elif task in tmpman_list:
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
                    f.node( task.getIdStr(), task.getNameForDrawing(),style="filled", shape = shape, color = color)
                else:
                    color = 'antiquewhite1'
                    if task.is_blocking():
                        color="gold2"
                    elif man.getTaskParamRes(task, "input"):
                        color="aquamarine"
                    elif man.getTaskParamRes(task, "output"):
                        color="darkgoldenrod1"
                    elif man.getTaskParamRes(task, "check"):
                        color="darkorchid1"
                    elif task.is_freeze:
                        color="cornflowerblue"
                        if len(task.getAffectedTasks()) > 0:
                            color = 'teal'
                    elif len(task.getAffectedTasks()) > 0:
                        color="aquamarine2"
                    else:
                        info = task.getInfo()
                        if task.prompt_tag == "assistant":
                            color="azure2"
                    f.node( task.getIdStr(), task.getNameForDrawing(),style="filled",color=color, shape = shape)


                # print("info=",task.getIdStr(),"   ", task.getName())
            
            for task in trg_list:
                if task.checkType('IterationEnd'):
                    if task.iter_start:
                        f.edge(task.getIdStr(), task.iter_start.getIdStr())
                draw_child_cnt = 0
                for child in task.childs:
                    if child not in trg_list:
                        if child in man.task_list:
                            if out_childtask_max > 0 and draw_child_cnt < out_childtask_max:
                                f.edge(task.getIdStr(), child.getIdStr())
                                draw_child_cnt += 1
                        #     f.edge(task.getIdStr(), child.getIdStr())
                    else:
                        f.edge(task.getIdStr(), child.getIdStr())
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

    def beforeRemove(self):
        for man in self.tmp_managers:
            man.beforeRemove(remove_folder = True, remove_task = True)
        self.tmp_managers.clear()
        if self.std_manager != None:
            self.std_manager.beforeRemove(remove_folder = True, remove_task = True)

 
    def editBasicActions(self, prompt, param):
        # tasks_chains = self.manager.curr_task.getTasksFullLinks(param)
        trg_parent = None
        ignore_conv = []
        if 'sel2par' in param and param['sel2par'] and len(self.manager.selected_tasks) == 1:
            trg_parent = self.manager.getSelectedTask()
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
            self.manager.copyTasksByInfo(tasks_chains=tasks_chains,
                                        edited_prompt=prompt, 
                                        change_prompt=param['copy_editbranch'],
                                        switch=param['switch'],
                                        new_parent=trg_parent,
                                        ignore_conv=ignore_conv,
                                        param = param
                                        )
            
    def divideActions(self, prompt, param):
        text = prompt
        tag = self.manager.curr_task.getLastMsgRole()
        verticaldiv = text.split('[[---]]')
        horizontaldiv = text.split('[[+++]]')
        
        if len(verticaldiv) > 1:
            last = verticaldiv.pop()
            for batch in verticaldiv:
                self.manager.makeTaskAction(batch, "Request", "Insert", tag)
            return self.manager.makeTaskAction(last, "Request", "Edit", tag)
        elif len(horizontaldiv) > 1:
            start_task = self.manager.curr_task
            for batch in horizontaldiv:
                self.manager.curr_task = start_task
                self.editBasicActions(batch, param)

    def getCurrTaskPrompts2(self, set_prompt = "", hide_tasks = True):
        man = self.manager
        if man.no_output:
            return
        if man.curr_task is None:
            if len(man.task_list) > 0:
                man.curr_task = man.task_list[0]
            else:
                print('No current task')
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

        cnt = 0
        cnt = man.getFrozenTasksCount()
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
        manholdgarlands = [t.getName() for t in man.curr_task.getHoldGarlands()]
        mangetname = man.getName()
        mangetcolor = man.getColor()
        multitasks = ','.join([t.getName() for t in man.multiselect_tasks])
        # return self.convToGradioUI(
        return (
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
            res, fnames = man.getCurrentTask().getPathToRead()
            if not res and len(fnames) == 0:
                filename = Loader.Loader.getFilePathFromSystem(manager_path=man.getPath())
                return [filename], filename, interacttive_drd, multiselect_drd, str(filename), True
            else:
                filename = fnames[0]
                return fnames, filename, interacttive_drd, multiselect_drd, filename, True
            # return (gr.Dropdown(choices=[filename], value=filename, interactive=True, multiselect=False),
                    # gr.Textbox(str(filename)))
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
        elif param_name == 'autocommander':
            value, choices = self.getCurrentManager().getCurrentTask().getParamStructChoices(param_name, param_key)
            return choices, value, interacttive_drd, multiselect_drd, value, True

        elif param_key == 'path_to_write':
            filename = Loader.Loader.getDirPathFromSystem(man.getPath())
            choices.append(filename)
            res, data = man.curr_task.getParamStruct(param_name)
            if res and param_key in data:
                choices.append(str(data[param_key]))
            return choices, os.path.join(filename,'insert_name'), interacttive_drd, multiselect_drd, filename, True
            # return gr.Dropdown(choices=[filename], value=os.path.join(filename,'insert_name'), interactive=True), gr.Textbox(value=filename, interactive=True)
        elif param_key == 'model':
            res, data = man.curr_task.getParamStruct(param_name)
            if res:
                cur_val = data[param_key]
                path_to_config = os.path.join('config','models.json')
                values = []
                with open(path_to_config, 'r') as config:
                    models = json.load(config)
                    for _, vals in models.items():
                        values.extend([opt['name'] for opt in vals['prices']])
                return values, cur_val, interacttive_drd, multiselect_drd, "", True
                # return (gr.Dropdown(choices=values, value=cur_val, interactive=True, multiselect=False),
                        #  gr.Textbox(value=''))
           
        task_man = TaskManager()
        res, data = man.getCurrentTask().getParamStruct(param_name, only_current=True)
        # print('Get param',param_name,' struct', res, data)
        if res and param_key in data:
            cur_val = data[param_key]
            print('cur val:',cur_val)
            if param_key == 'idx' and (param_name.startswith('child') or param_name == 'tree_step'):
                values = range(50)
                if cur_val not in values:
                    values.append(cur_val)
            else:
                values = task_man.getOptionsBasedOptionsDict(param_name, param_key)
            # print('Update with [',cur_val,'] from', values)
            if len(values):
                if cur_val in values:
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
        task_manager = TaskManager()
        task_manager.clearTasksCache()

    def autoUpdateExtTreeTaskActs(self, actioners: list):
        # print(f"Auto load ext tree act for {self.getPath()}")
        man = self.std_manager
        if not isinstance(man, Manager.Manager):
            print("Current manager is temporary: target manager is executing")
            return
        for task in man.getTasks():
            if task.isExternalProjectTask():
                print(f"Load for task {task.getName()}")
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
        if next:
            if len(next.getChilds()) == 0:
                print('Branch complete:', self.root_task_tree.getName(), '-', next.getName())

    def updateManager(self, man : Manager.Manager, update_task = True):
        # print('Curr state:', self.update_state,'|task:',man.curr_task.getName())
        if self.update_state == 'init':
            man.sortTreeOrder(True)
            self.update_state = 'start tree'
            self.update_tree_idx = 0
        elif self.update_state == 'start tree':
            task = man.tree_arr[self.update_tree_idx]
            print('Start tree', task.getName(),'[',self.update_tree_idx,']')
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
                self.update_state = 'done'
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
            print('Abort',self.getPath,'cause: already updating')
            return
        else:
            self.is_updating = True
        man = self.manager
        man.is_executing = True
        exe_manager = BaseMan.Jun(None, None, None)
        man.syncManager(exe_manager)
        self.setCurrentManager(exe_manager)
        print(f"Update all tasks of {man.getName()}")
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
        print(f"Act [{man.getName()}] made {idx} step(s)\nFrozen: {cnt} of {len(man.task_list)} task(s)")
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

