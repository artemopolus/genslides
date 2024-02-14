from genslides.task.base import TaskManager, BaseTask
# from genslides.commanager.jun import Manager
import genslides.commanager.jun as Manager

from genslides.utils.reqhelper import RequestHelper
from genslides.utils.testrequest import TestRequester
from genslides.utils.searcher import GoogleApiSearcher

import os
import json
import gradio as gr
import shutil

class Actioner():
    def __init__(self, manager : Manager.Manager) -> None:
        self.std_manager = manager
        self.manager = manager
        self.tmp_managers = []
        self.loadExtProject = manager.loadexttask
        # TODO: установить как значение по умолчанию
        self.path = 'saved'
        self.update_state = 'init'

    def setPath(self, path: str):
        self.path = path

    def getPath(self) -> str:
        return self.path

    def clearTmp(self):
        tmppath = os.path.join(self.getPath(),'tmp')
        if os.path.exists(tmppath):
            shutil.rmtree(tmppath)


    def createPrivateManagerForTaskByName(self, man)-> Manager.Manager:
        # TODO: изменять стартовые задачи по правилам, которые следуют из названия
        # получаем имя задачи из текущего менеджера
        task = self.manager.getTaskByName(man['task'])
        return self.createPrivateManagerForTask(task, man)

    def createPrivateManagerForTask(self, task: BaseTask, man)-> Manager.Manager:
        print(10*"----------")
        print('Create private manager based on', task.getName())
        print(10*"----------")
        for manager in self.tmp_managers:
            if task.getName() == manager.getName():
                return None
        manager = Manager.Manager(RequestHelper(), TestRequester(), GoogleApiSearcher())
        manager.initInfo(self.loadExtProject, task, self.getPath(), man['actions'], man['repeat'] )
        return manager
    
    def resetCurrentPrivateManager(self, task: BaseTask, man):
        self.manager.initInfo(self.loadExtProject, task, self.getPath(), man['actions'], man['repeat'] )
    
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
            return self.addPrivateManagerForTaskByName(param)
        return None

    
    def exeTmpManagers(self):
        pack = self.manager.info['script']
        for man in pack['managers']:
            self.addPrivateManagerForTaskByName(man)
        for manager in self.tmp_managers:
            self.manager = manager
            self.exeComList(manager.info['actions'])
    
    def clearTmpManagers(self):
        tmp = self.tmp_managers.copy()
        for man in tmp:
            self.removeTmpManager(man, self.std_manager)
        self.manager = self.std_manager

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
                    self.manager = manager
                    self.exeComList(manager.info['actions'])
                    all_done = False
            idx +=1
        tmp = self.tmp_managers.copy()
        for man in tmp:
            self.removeTmpManager(man, self.std_manager)
        self.manager = self.std_manager
        
    def makeSavedAction(self, pack):
        print(10*"----------")
        print('Make saved actions')
        print(10*"----------")

        prompt = pack['prompt']
        act_type = pack['type']
        param = pack['param']
        tag = pack['tag']
        action = pack['action']
        self.makeTaskAction(prompt, act_type, action, tag, param, save_action=False)

    def exeCurManagerSmpl(self):
        idx = 0
        # print(self.manager.info['repeat'])
        while(idx < self.manager.info['repeat']):
            self.exeCurManager()
            if self.manager.info['done']:
                break


    def exeCurManager(self):
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
            return self.manager.createCollectTreeOnSelectedTasks(creation_type)
        elif 'extedit' in param and param['extedit']:
            # tasks_chains = self.manager.curr_task.getTasksFullLinks(param)
            tasks_chains = self.manager.getTasksChainsFromCurrTask(param)
            if param['step']:
                self.manager.copyTasksByInfoStart(
                                        tasks_chains=tasks_chains,
                                         edited_prompt=prompt, 
                                         change_prompt=param['change'], 
                                         switch=param['switch']
                )
            else:
                self.manager.copyTasksByInfo(tasks_chains=tasks_chains,
                                         edited_prompt=prompt, 
                                         change_prompt=param['change'],
                                         switch=param['switch']
                                         )
            

            # return self.manager.copyChildChains(change_prompt = param['change'],
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
                self.manager = man
        elif creation_type == "InitSavdManager":
            man = self.addSavedScript(param['task'])
            if man is not None:
                self.manager = man
        elif creation_type == "EditPrivManager":
            self.setParamToManagerInfo(param, self.manager)
        elif creation_type == "ExecuteManager":
            self.exeCurManager()
        elif creation_type == "InitPrivManager":
            man = self.addEmptyScript(param)
            if man is not None:
                self.manager = man
        elif creation_type == "SavePrivManToTask":
            print(self.manager.info)
            self.manager.curr_task.setParamStruct({'type':'manager', 'info': self.manager.info})
        elif creation_type == "StopPrivManager":
            if self.manager == self.std_manager:
                return self.manager.getCurrTaskPrompts()
            trg = self.tmp_managers[-2] if len(self.tmp_managers) > 1 else self.std_manager
            self.removeTmpManager(self.manager, trg, copy=True)
            print('New manager is', self.manager.getName())
            if save_action:
                self.manager.addActions(action = creation_type, prompt = prompt, act_type = type1, param = param, tag=creation_tag)
        elif creation_type == "RmvePrivManager":
            if self.manager == self.std_manager:
                if len(self.tmp_managers):
                    self.manager = self.tmp_managers[-1]
                else:
                    return self.manager.getCurrTaskPrompts()
            trg = self.tmp_managers[-2] if len(self.tmp_managers) > 1 else self.std_manager
            if save_action:
                self.manager.remLastActions()
            self.removeTmpManager(self.manager, trg, copy=False)
           
        elif creation_type == "SetCurrTask":
            self.manager.setCurrentTaskByName(name=prompt)
        elif creation_type == "NewExtProject":
            self.manager.createExtProject(type1, prompt, None)
        elif creation_type == "SubExtProject":
            self.manager.createExtProject(type1, prompt, self.manager.curr_task)
        elif creation_type in self.manager.getMainCommandList() or creation_type in self.manager.vars_param:
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
        elif creation_type == "SetParamValue":
            return self.manager.setTaskKeyValue(param['name'], param['key'], param['select'], param['manual'])
        elif creation_type == "SetCurrentExtTaskOptions":
            self.manager.setCurrentExtTaskOptions(param['names'])
        elif creation_type == "ResetAllExtTaskOptions":
            self.manager.resetAllExtTaskOptions()
        elif creation_type == "RelinkToCurrTask":
            task = self.std_manager.getTaskByName(param['name'])
            start = self.manager.curr_task
            if task is not None or task == start:
                typename = task.getType()
                task.removeLinkToTask()
                if typename == 'Collect' or typename == 'GroupCollect' or 'Garland':
                    intask = task
                    outtask = start
                else:
                    intask = start
                    outtask = task
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
        # проверяем целевой
        if next_man is None:
            return
        if man is self.std_manager:
            return
        print('Cur task list', [t.getName() for t in man.task_list])
        print('Nxt task list', [t.getName() for t in next_man.task_list])
        if copy:
            self.tmp_managers.remove(man)
            # копировать все задачи
            print('Copy task',[task.getName() for task in man.task_list])
            for task in man.task_list:
                if task not in next_man.task_list:
                    next_man.task_list.append(task)
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
                        print(task.getManager().getName())
            for task in notdel_tasks:
                del_tasks.remove(task)
            print('Task to delete:',[t.getName() for t in del_tasks])
            print('Retarget task:',[t.getName() for t in notdel_tasks])
            for task in del_tasks:
                    task.beforeRemove()
                    man.task_list.remove(task)
                    del task

            man.beforeRemove(remove_folder=True, remove_task=False)
            self.tmp_managers.remove(man)

        del man
        # установить следущий менедежер
        self.manager = next_man

    def getTmpManagerInfo(self):
        saved_man = [t['task'] for t in self.manager.info['script']['managers']]
        saved_man.append('None')
        param = self.manager.info.copy()
        del param['script']
        del param['actions']
        # del param['task']
        del param['idx']
        del param['done']
        tmp_man = [t.getName() for t in self.tmp_managers]
        if len(tmp_man) == 0:
            name = self.manager.getName()
        else:
            n = [self.std_manager.getName()]
            n.extend(tmp_man)
            name = '->'.join(n)

        return (gr.Dropdown(choices= saved_man, value=None, interactive=True), 
                gr.Dropdown(choices= tmp_man, value=None, interactive=True), 
                json.dumps(param, indent=1), 
                gr.Text(value=name), 
                self.manager.getCurrentExtTaskOptions())

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
        res, iparam, actions = self.manager.curr_task.getExeCommands()
        if res:
            t_manager = self.createPrivateManagerForTask(start, iparam)
            self.tmp_managers.append(t_manager)
            self.manager = t_manager
            for act in actions:
                iparam['actions'] = act
                self.resetCurrentPrivateManager(start, iparam)
                self.exeCurManagerSmpl()
            self.manager = self.std_manager

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
        man = self.manager
        man.curr_task = man.tree_arr[0]
        for task in man.tree_arr:
            task.resetTreeQueue()
        return man.getCurrTaskPrompts()

       
    def update(self):
        man = self.manager
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
        man = self.manager
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
        man = self.manager
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
 
