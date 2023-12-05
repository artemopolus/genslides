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

    def createPrivateManagerForTaskByName(self, name : str, act_list = [], repeat = 3)-> Manager:
        task = self.manager.getTaskByName(name)
        return self.createPrivateManagerForTask(task, act_list, repeat)

    def createPrivateManagerForTask(self, task: BaseTask, act_list = [], repeat = 3)-> Manager:
        for man in self.tmp_managers:
            if task.getName() == man.getName():
                return None
        manager = Manager(RequestHelper(), TestRequester(), GoogleApiSearcher())
        manager.loadexttask = self.loadExtProject
        manager.task_list =  task.getAllParents()
        manager.curr_task = task
        manager.setName(task.getName())
        manager.setPath(os.path.join('saved','tmp', manager.getName()))
        manager.saveInfo()
        manager.info['act_list'] = act_list
        manager.info['idx'] = 0
        manager.info['repeat'] = repeat
        return manager
    
    def addPrivateManagerForTaskByName(self, name : str, act_list = [], repeat = 3) ->Manager:
        manager = self.createPrivateManagerForTaskByName(name, act_list, repeat)
        if manager is not None:
            self.tmp_managers.append(manager)
        return manager

    def exeProgrammedCommand(self):
        pack = self.manager.info['script']
        # Изменяем и обновляем проект
        # self.exeComList(pack['Base'])
        # Читаем команды из файла проекта
        for man in pack['managers']:
            self.addPrivateManagerForTaskByName(man['task'], man['act_list'], man['repeat'])
        # Ищем задачи, помеченные для проверки
        # Устанавливаем начальные условия: текущая активная задача

        # Выполняем заданные команды
        idx = 0
        while( not all_done and idx < pack['limits']):
            all_done = True
            for manager in self.tmp_managers:
                if not manager.info['done']:
                    self.manager = manager
                    self.exeComList(manager.info['act_list'])
                    all_done = False
            idx +=1
        self.manager = self.std_manager
        self.tmp_managers = []
        
    def makeSavedAction(self, pack):
        prompt = pack['prompt']
        act_type = pack['type']
        param = pack['param']
        tag = pack['tag']
        action = pack['action']
        self.makeTaskAction(prompt, act_type, action, tag, param, save_action=False)


    def exeComList(self, pack) -> bool:
        for input in pack:
            self.makeSavedAction(input)
        success = True
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
        elif creation_type == "InitPrivManager":
            if self.manager.curr_task:
                self.manager = self.addPrivateManagerForTaskByName(self.manager.curr_task.getName(), param['act_list'], param['repeat'])
        elif creation_type == "StopPrivManager":
            if self.manager == self.std_manager:
                return
            man = self.manager
            self.tmp_managers.remove(man)
            # копировать все задачи
            for task in man.task_list:
                if task not in self.std_manager.task_list:
                    self.std_manager.task_list.append(task)
                    task.setManager(self.std_manager)
            man.beforeRemove(remove_folder=True, remove_task=False)
            self.fromActionToScript(self.std_manager, man, param['repeat'])
            del man
            # сохранить все действия в скрипт
            self.manager = self.std_manager
            if save_action:
                self.manager.addActions(action = creation_type, prompt = prompt, act_type = type1, param = param, tag=creation_tag)
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
        

    def fromActionToScript(self, trg: Manager, src : Manager, repeat = 3):
        if 'script' in trg.info:
            script = trg.info['script']
        else:
            script = {'managers':[]}
        man2 = {'task': src.getName(),'act_list': src.info['actions'],'repeat':repeat}
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

