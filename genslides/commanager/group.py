from genslides.task.base import TaskManager, BaseTask
from genslides.commanager.jun import Manager

from genslides.utils.reqhelper import RequestHelper
from genslides.utils.testrequest import TestRequester
from genslides.utils.searcher import GoogleApiSearcher

import os

class Actioner():
    def __init__(self, manager : Manager) -> None:
        self.std_manager = manager
        self.manager = manager
        self.tmp_managers = []
        self.loadExtProject = manager.loadexttask

    def createPrivateManagerForTaskByName(self, man)-> Manager:
        # TODO: изменять стартовые задачи по правилам, которые следуют из названия
        # получаем имя задачи из текущего менеджера
        task = self.manager.getTaskByName(man['name'])
        return self.createPrivateManagerForTask(task, man)

    def createPrivateManagerForTask(self, task: BaseTask, man)-> Manager:
        print(10*"----------")
        print('Create private manager based on', task.getName())
        print(10*"----------")
        for manager in self.tmp_managers:
            if task.getName() == manager.getName():
                return None
        manager = Manager(RequestHelper(), TestRequester(), GoogleApiSearcher())
        manager.initInfo(self.loadExtProject, task, man['actions'], man['repeat'] )
        return manager
    
    def addPrivateManagerForTaskByName(self, man) ->Manager:
        # Проверяем создавались ли раньше менеджеры
        for manager in self.tmp_managers:
            if man['name'] == manager.getName():
                return None
        # Создаем менеджера
        manager = self.createPrivateManagerForTaskByName(man)
        # Добавляем менеджера
        if manager is not None:
            self.tmp_managers.append(manager)
        return manager
    
    def exeCurManager(self):
        self.exeComList(self.manager.info['actions'])

    def addSavedScript(self, name: str):
        pack = self.manager.info['script']
        for man in pack['managers']:
            if name == man['name']:
                return self.addPrivateManagerForTaskByName(man)
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

    def removeTmpManager(self, name : str):
        trg = None
        for man in self.tmp_managers:
            if name == man.getName():
                trg = man
        if trg is not None:
            self.tmp_managers.remove(trg)

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


    def exeComList(self, pack) -> bool:
        # Устанавливаем начальные условия: текущая активная задача
        for input in pack:
            self.makeSavedAction(input)
        success = True
        # Ищем задачи, помеченные для проверки
        for task in self.manager.task_list:
            res, val = task.getParamStruct('output')
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
 
    def makeTaskAction(self, prompt, type1, creation_type, creation_tag, param = {}, save_action = True):
        if save_action and creation_type != "StopPrivManager":
            self.manager.addActions(action = creation_type, prompt = prompt, act_type = type1, param = param, tag=creation_tag)
        if type1 == "Garland":
            return self.manager.createCollectTreeOnSelectedTasks(creation_type)
        elif creation_type == "InitSavdManager":
            man = self.addSavedScript(param['task_name'])
            if man is not None:
                self.manager = man
        elif creation_type == "ExecuteManager":
            self.exeCurManager()
        elif creation_type == "InitPrivManager":
            if self.manager.curr_task:
                man = self.addPrivateManagerForTaskByName(self.manager.curr_task.getName(), param['act_list'], param['repeat'])
                if man is not None:
                    self.manager = man
        elif creation_type == "StopPrivManager":
            if self.manager == self.std_manager:
                return self.manager.getCurrTaskPrompts()
            if len(self.tmp_managers) > 0:
                trg = self.tmp_manager[-1]
            else:
                trg = self.std_manager
            self.removeTmpManager(self.manager, trg)
            if save_action:
                self.manager.addActions(action = creation_type, prompt = prompt, act_type = type1, param = param, tag=creation_tag)
        elif creation_type == "RmvePrivManager":
            if self.manager == self.std_manager:
                return self.manager.getCurrTaskPrompts()
            man = self.manager
            self.tmp_managers.remove(man)
            # удалить все задачи
            man.beforeRemove(remove_folder=True, remove_task=True)
            del man
            # установить следущий менедежер
            if len(self.tmp_managers) > 0:
                # временный
                self.manager = self.tmp_managers[-1]
            else:
                # или базовый
                self.manager = self.std_manager
            if save_action:
                self.manager.remLastActions()
           
        elif creation_type == "ExeActions":
            self.exeProgrammedCommand()
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
            return self.manager.copyChildChains(edited_prompt=prompt, apply_link= True, remove_old_link=False)
        elif creation_type == "EdCp3":
            return self.manager.copyChildChains(edited_prompt=prompt, apply_link= False, remove_old_link=False)
        elif creation_type == "EdCp4":
            return self.manager.copyChildChains(edited_prompt=prompt, apply_link= True, copy=True)
        elif creation_type == "AppendNewParam":
            return self.manager.appendNewParamToTask(param['name'])
        elif creation_type == "SetParamValue":
            return self.manager.setTaskKeyValue(param['name'], param['key'], param['select'], param['manual'])
        return self.manager.getCurrTaskPrompts()

    def fromActionToScript(self, trg: Manager, src : Manager):
        if 'script' in trg.info:
            script = trg.info['script']
        else:
            script = {'managers':[]}
        man2 = src.info
        found = False
        for man in script['managers']:
            if src.getName() == man['task']:
                found = True
                man = man2
                break 
        if not found:
            script["managers"].append(man2)
        trg.info['script'] = script
        trg.saveInfo()

    def removeTmpManager(self, man : Manager, next_man: Manager):
        # проверяем целевой
        if next_man is None:
            return
        self.tmp_managers.remove(man)
        # копировать все задачи
        for task in man.task_list:
            if task not in next_man.task_list:
                next_man.task_list.append(task)
                task.setManager(next_man)
        man.beforeRemove(remove_folder=True, remove_task=False)
        # сохранить все действия в скрипт
        self.fromActionToScript(next_man, man)
        del man
        # установить следущий менедежер
        self.manager = next_man
