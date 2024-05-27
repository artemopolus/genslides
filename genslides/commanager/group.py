from genslides.task.base import TaskManager, BaseTask
# from genslides.commanager.jun import Manager
import genslides.commanager.jun as Manager

from genslides.utils.reqhelper import RequestHelper
from genslides.utils.testrequest import TestRequester
from genslides.utils.searcher import GoogleApiSearcher

import genslides.utils.filemanager as FileManager

import os
import json
import gradio as gr
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

    def setManager(self, manager : Manager.Manager):
        if manager != self.std_manager and not manager.is_loaded:
            manager.disableOutput2()
            manager.loadTasksListFileBased()
            manager.enableOutput2()
 
        self.manager = manager

    def reset(self):
        self.setManager(self.std_manager)
        self.tmp_managers = []
        self.clearTmp()

    def setPath(self, path: str):
        self.path = path

    def getPath(self) -> str:
        return self.path

    def clearTmp(self):
        print('Clear temporary files')
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
        self.manager = self.std_manager
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

    def exeCurManagerSmpl(self):
        idx = 0
        # print(self.manager.info['repeat'])
        while(idx < self.manager.info['repeat']):
            self.exeActions()
            if self.manager.info['done']:
                break


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
        out.append({"action":"InitSavdManager","param":{'task':'task_name'}})
        out.append({"action":"InitSavdManagerToCur","param":{'task':'task_name'}})
        out.append({"action":"EditPrivManager","param":{}})
        out.append({"action":"ExecuteManager","param":{}})
        out.append({"action":"InitPrivManager","param":{}})
        out.append({"action":"StopPrivManager","param":{}})
        out.append({"action":"RmvePrivManager","param":{}})
        out.append({"action":"SetCurrTask","param":{}})
        return out
 
    def makeTaskAction(self, prompt, type1, creation_type, creation_tag, param = {}, save_action = True):
        if save_action and creation_type != "StopPrivManager" and creation_type != "SavePrivManToTask":
            self.manager.addActions(action = creation_type, prompt = prompt, act_type = type1, param = param, tag=creation_tag)
        if type1 == "Garland":
            return self.manager.createTreeOnSelectedTasks(creation_type,'Garland')
        elif 'extedit' in param and param['extedit']:
            if 'upd_cp' in param and param['upd_cp']:
                self.manager.updateEditToCopyBranch(self.manager.curr_task)
                return self.manager.getCurrTaskPrompts()

            # tasks_chains = self.manager.curr_task.getTasksFullLinks(param)
            trg_parent = None
            ignore_conv = []
            if 'sel2par' in param and param['sel2par'] and len(self.manager.selected_tasks) == 1:
                trg_parent = self.manager.selected_tasks[0]
            tasks_chains = self.manager.getTasksChainsFromCurrTask(param)
            if len(self.manager.multiselect_tasks) > 0:
                if 'ignrlist' in param and param['ignrlist']:
                    ignore_conv = self.manager.multiselect_tasks.copy()
                elif 'wishlist' in param and param['wishlist']:
                    for chain in tasks_chains:
                        for task in chain['branch']:
                            if task not in self.manager.multiselect_tasks and task not in ignore_conv:
                                ignore_conv.append(task)
            print('Ignore list:', [t.getName() for t in ignore_conv])
            if param['step']:
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
            

            # return self.manager.copyChildChains(change_prompt = param['copy_editbranch'],
            #                                     edited_prompt=prompt, 
            #                                     apply_link= param['apply_link'], 
            #                                     remove_old_link=param['remove_old'],
            #                                     copy=param['copy'],
            #                                     subtask=param['subtask'],
            #                                     trg_type= param['trg_type'] if 'trg_type' in param else '',
            #                                     src_type = param['src_type'] if 'src_type' in param else ''
            #                                     )

        elif creation_type == "TakeFewSteps":
            self.manager.takeFewSteps(param['dir'], param['times'])
        elif creation_type == "GoToNextChild":
            self.manager.goToNextChild()
        elif creation_type == "GoToParent":
            self.manager.goToParent()
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
                return self.manager.getCurrTaskPrompts()
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
                    return self.manager.getCurrTaskPrompts()
            # trg = self.tmp_managers[-2] if len(self.tmp_managers) > 1 else self.std_manager
            trg = self.std_manager
            if save_action:
                self.manager.remLastActions()
            self.removeTmpManager(self.manager, trg, copy=False)
           
        elif creation_type == "SetCurrTask":
            self.manager.setCurrentTaskByName(name=prompt)
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
            return self.manager.makeTaskActionBase(prompt, type1, creation_type, creation_tag)
        elif creation_type in self.manager.getSecdCommandList():
            return self.manager.makeTaskActionPro(prompt, type1, creation_type, creation_tag)
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
            return self.manager.setTaskKeyValue(param['name'], param['key'], param['select'], param['manual'])
        elif creation_type == "SetCurrentExtTaskOptions":
            self.manager.setCurrentExtTaskOptions(param['names'])
        elif creation_type == "ResetAllExtTaskOptions":
            self.manager.resetAllExtTaskOptions()
        elif creation_type == "RelinkToCurrTask":
            task = self.std_manager.getTaskByName(param['name'])
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
                        return self.manager.getCurrTaskPrompts()
                    # В противном случае ищем связанные объекты
                    garls = task.getHoldGarlands()
                    if len(garls) == 0:
                        return self.manager.getCurrTaskPrompts()
                    task.removeLinkToTask()
                    for garl in garls:
                        intask = garl
                        outtask = start
                        self.manager.makeLink(intask, outtask)
            self.manager.curr_task = start
        return self.manager.getCurrTaskPrompts()

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

        return (gr.Dropdown(choices= saved_man, value=None, interactive=True), 
                gr.Radio(choices= tmp_man, value=self.manager.getName(), interactive=True), 
                # json.dumps(param, indent=1), 
                gr.Text(value=name), 
                # self.manager.getCurrentExtTaskOptions(),
                gr.Dropdown(choices=[m.getName() for m in self.tmp_managers], value=None, interactive=True)
                )

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
        man.sortTreeOrder()
        self.update_state = 'start tree'
        self.update_tree_idx = 0

    def updateStepInternal(self):
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
             

        next = man.updateSteppedSelectedInternal()
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
            if not force_check and man == self.std_manager:
                man.updateTreeArr()
            else:
                man.updateTreeArr(check_list=True)
        if len(man.tree_arr) == 0:
            return
        man.curr_task = man.tree_arr[0]
        for task in man.tree_arr:
            task.resetTreeQueue()
    
       
    def update(self):
        man = self.manager
        # print('Curr state:', self.update_state,'|task:',man.curr_task.getName())
        if self.update_state == 'init':
            self.updateInit()
        elif self.update_state == 'start tree':
            task = man.tree_arr[self.update_tree_idx]
            print('Start tree', task.getName(),'[',self.update_tree_idx,']')
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

        # out = self.updateUIelements()
        # return out

    def updateCurrentTree(self):
        man = self.manager
        if len(man.tree_arr) <= man.tree_idx:
            man.updateTreeArr()
        man.tree_arr[ man.tree_idx ].resetTreeQueue()
        self.update_state = 'start tree'
        self.update_tree_idx = man.tree_idx

        start_task = man.curr_task
        # self.resetUpdate()
        idx = 0
        while(idx < 1000):
            self.update()
            if self.update_state == 'next tree':
                break
            idx += 1

        man.curr_task = start_task
        return man.getCurrTaskPrompts()

    def updateAll(self, force_check = False):
        man = self.manager
        print(f"Update all tasks of {man.getName()}")
        start_task = man.curr_task
        self.resetUpdate(force_check=force_check)
        if len(man.tree_arr) == 0:
            return
        idx = 0
        while(idx < 10000):
            self.update()
            if self.update_state == 'done':
                break
            idx += 1

        cnt = 0
        for task in man.task_list:
            if task.is_freeze:
                cnt += 1
        print(f"[{man.getName()}]Frozen: {cnt} of {len(man.task_list)} task(s)")
        man.saveInfo()
        man.curr_task = start_task
        # out = man.getCurrTaskPrompts()
        # return out

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
        print('Frozen tasks cnt:', man.getFozenTasksCount())

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

        return man.getCurrTaskPrompts()

    def setName(self, name : str):
        idx = 0
        self.std_manager.setName('_'.join(name,'base'))
        for man in self.tmp_managers:
            man.setName( '_'.join(name, str(idx)) )
            idx += 1

    def updateUIelements(self, prompt = ''):
        # print('std',self.std_manager)
        # print('tmp',self.tmp_managers)
        # print('man',self.manager)
        if self.std_manager == self.manager:
            hide_tasks = False
            maingraph = self.drawGraph(hide_tasks=True)
            stepgraph = self.std_manager.drawGraph(max_index= 1, path = "output/img2", hide_tasks=True, max_childs=-1,add_linked=True)
            rawgraph = self.std_manager.drawGraph(hide_tasks=hide_tasks, max_childs=1, path="output/img3", all_tree_task=True)

            out = self.manager.getCurrTaskPrompts2(set_prompt=prompt, hide_tasks=hide_tasks)
            out += (maingraph, stepgraph, rawgraph)
            # print('act:',out)
            return out
        else:
            hide_tasks = True
            maingraph = self.manager.drawGraph(hide_tasks=hide_tasks)
            stepgraph = self.manager.drawGraph(max_index= 1, path = "output/img2", hide_tasks=hide_tasks, max_childs=-1,add_linked=True)
            rawgraph = self.manager.drawGraph(hide_tasks=hide_tasks, max_childs=1, path="output/img3")
            out = self.manager.getCurrTaskPrompts2(set_prompt=prompt)
            if out == None:
                self.setManager(self.std_manager)
                out = self.manager.getCurrTaskPrompts2(set_prompt=prompt)
            out += (maingraph, stepgraph, rawgraph)
            return out
    
    def updateTaskManagerUI(self):
        out = self.updateUIelements()
        out += self.getTmpManagerInfo()
        return out
 
    def drawGraph(self, only_current= True, max_index = -1, path = "output/img", hide_tasks = True, add_multiselect = False, max_childs = 3, add_linked=False):
        # print('Draw graph')
        man = self.std_manager
        tmpman_list = []
        for manager in self.tmp_managers:
            if manager != self.std_manager:
                tmpman_list.extend(manager.task_list)
        if only_current:
            if man.curr_task.isRootParent():
                trg_list = man.curr_task.getTree(max_childs=10)
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
            for task in man.task_list:
                if len(task.getAffectedTasks()) > 0:
                    trgs = task.getAffectedTasks()
                    if trgs in trg_list:
                        trg_list.append(task)

            

            for task in trg_list:
                shape = "ellipse" #rectangle,hexagon
                if task.checkType('Response'):
                    shape = 'rectangle'
                elif task.checkType('InExtTree'):
                    shape = 'invhouse'
                elif task.checkType('OutExtTree'):
                    shape = 'house'
                elif task.checkType('SetOption'):
                    shape = 'doubleoctagon'
                if task in trgs_rsm:
                    if task == man.curr_task:
                        f.node( task.getIdStr(), task.getName(),style="filled",color="blueviolet")
                    else:
                        f.node( task.getIdStr(), task.getName(),style="filled",color="darkmagenta")
                elif task.readyToGenerate():
                    color = 'darkmagenta'
                    f.node( task.getIdStr(), task.getName(),style="filled", color = color, shape = shape)
                elif task in man.multiselect_tasks:
                    color = "lightsalmon3"
                    if task == man.curr_task:
                        color = "lightsalmon1"
                    if len(task.getHoldGarlands()) > 0:
                        color = 'crimson'
                    f.node( task.getIdStr(), task.getName(),style="filled", color = color, shape = shape)
                elif task == man.curr_task:
                    color = "skyblue"
                    if len(task.getHoldGarlands()) > 0:
                        color = 'skyblue4'
                    f.node( task.getIdStr(), task.getName(),style="filled", shape = shape, color = color)
                elif task in tmpman_list:
                    color = 'blueviolet'
                    # shape = "ellipse" #rectangle,hexagon
                    for manager in self.tmp_managers:
                        if manager != self.std_manager:
                            if task in manager.task_list:
                                if 'color' in manager.info:
                                    color = manager.info['color']
                                break
                    f.node( task.getIdStr(), task.getName(),style="filled", shape = shape, color = color)
                else:
                    color = 'antiquewhite1'
                    if man.getTaskParamRes(task, "block"):
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
                    f.node( task.getIdStr(), task.getName(),style="filled",color=color, shape = shape)


                # print("info=",task.getIdStr(),"   ", task.getName())
            
            for task in trg_list:
                if task.checkType('IterationEnd'):
                    if task.iter_start:
                        f.edge(task.getIdStr(), task.iter_start.getIdStr())
                draw_child_cnt = 0
                for child in task.childs:
                    if child not in trg_list:
                        draw_child_cnt += 1
                        if draw_child_cnt < 4:
                            f.edge(task.getIdStr(), child.getIdStr())
                    else:
                        f.edge(task.getIdStr(), child.getIdStr())
                    # print("edge=", task.getIdStr(), "====>",child.getIdStr())

                for info in task.getGarlandPart():
                    f.edge(info.getIdStr(), task.getIdStr(), color = "darkorchid3", style="dashed")
                for info in task.getHoldGarlands():
                    f.edge(task.getIdStr(), info.getIdStr(), color = "darkorchid3", style="dashed")
               

            img_path = path
            f.render(filename=img_path,view=False,format='png')
            img_path += ".png"
            return img_path
        return "output/img.png"

    def moveTaskFromManagerToAnother(self, tasks : list[BaseTask], cur_man : Manager.Manager, next_man: Manager.Manager, to_std = False):
        t_to_rem = [t for t in tasks if t not in cur_man.task_list]
        for task in t_to_rem:
            tasks.remove(task)
        print('Move tasks from',cur_man.getName(),'to',next_man.getName(),':',[t.getName() for t in tasks])
        if to_std:
            pass 
        else:#std->tmp
            for task in tasks:
                if len(task.getGarlandPart()) > 0:
                    print('Move to tmp error: task[',task.getName(),'] is linked')
                    return
                if len(task.getHoldGarlands()) > 0:
                    print('Move to tmp error: task[',task.getName(),'] is linked')
                    return
                for child in task.getChilds():
                    if child not in tasks:
                        print('Move to tmp error: task[',task.getName(),'] is moving, but child[',child.getName(),'] is not')
                        return
                    if child not in cur_man.task_list and child not in tasks:
                        print('Move to tmp error: task[',task.getName(),'] is std man task, but child[',child.getName(),'] is tmp man task and not copied')
                        return
            task_names = self.getExtTaskNamesOfManager(next_man)
            task_names_to_del = []
        print('cur=',len(cur_man.task_list))
        for task in tasks:
            if task not in next_man.task_list:
                next_man.addTask(task)
                task.setManager(next_man)
                cur_man.rmvTask(task)
            elif not to_std and task.getName() in task_names:
                task_names_to_del.append(task.getName())
                next_man.addTask(task)
                task.setManager(next_man)
                cur_man.rmvTask(task)
        print('cur=',len(cur_man.task_list))
        if to_std: #tmp->std
            ext_tasks = []
            for task in tasks:
                for child in task.getChilds():
                    if child in cur_man.task_list:
                        ext_tasks.append(task)
                        break
            if len(ext_tasks):
                self.addExtTasksForManager(cur_man, ext_tasks)
        else: #std->tmp
            for name in task_names_to_del:
                task_names.remove(name)
            self.setExtTaskNamesToManager(task_names, next_man)
            ext_tasks = []
            for task in tasks:
                par = task.getParent()
                if par and par not in next_man.task_list:
                    ext_tasks.append(task)
            if len(ext_tasks):
                self.addExtTasksForManager(next_man, ext_tasks)

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

 
