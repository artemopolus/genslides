from genslides.task.base import TaskDescription
from genslides.task.base import TaskManager
from genslides.task.base import BaseTask

from genslides.utils.reqhelper import RequestHelper
from genslides.utils.request import Requester
from genslides.utils.searcher import WebSearcher
from genslides.utils.largetext import Summator
from genslides.utils.browser import WebBrowser

from genslides.utils.savedata import SaveData

import genslides.task.creator as cr
import genslides.commands.edit as edit
import genslides.commands.create as create
import genslides.commands.parent as parcmd
import genslides.commands.link as lnkcmd

from genslides.utils.largetext import SimpleChatGPT
import genslides.utils.writer as writer

import os
from os import listdir
from os.path import isfile, join

import json

import gradio as gr
import graphviz

import pprint

import pyperclip
import shutil


import datetime

import genslides.utils.finder as finder
from tkinter import Tk     # from tkinter import Tk for Python 3.x
from tkinter.filedialog import askopenfilename, askdirectory, askopenfilenames



class Manager:
    def __init__(self, helper: RequestHelper, requester: Requester, searcher: WebSearcher) -> None:
        self.helper = helper
        self.requester = requester
        self.searcher = searcher
        self.vars_param = ["stopped", "input", "output", "watched"]
        # TODO: все связанное с этим файлом необходимо перенести в проектер
        self.path_to_file = os.path.join("config","base.json")
        if os.path.exists(self.path_to_file):
            with open(self.path_to_file, 'r') as f:
                params = json.load(f)
        else:
            with open(self.path_to_file, 'w') as f:
                params = {}
                params["mode"] = "base"
                json.dump(params,f,indent=1)
        self.params = params
        self.onStart()
        self.loadexttask = None
        self.name = 'Base'

    def setName(self, name : str):
        self.name = name

    def getName(self) -> str:
        return self.name

# TODO: сменить место хранения параметров менеджера
    def setParam(self, param_name, param_value):
        if param_name in self.params:
            print("Set ",param_name," to ",param_value)
            self.params[param_name] = param_value
            with open(self.path_to_file, 'w') as f:
                json.dump(self.params,f,indent=1)
        else:
            print("Can\'t set param")

    def getParam(self, param_name):
        if param_name in self.params:
            return self.params[param_name]
        return None
    
    def getParamGradioInput(self, param_name):
        out = self.getParam(param_name + " lst")
        if not out:
            out = []
        return gr.Dropdown.update( choices= out, interactive=True)

    
    def getParamsLst(self):
        out = []
        for param in self.params:
            if not param.endswith(" lst"):
                out.append(param)
        return out

    def onStart(self):
        self.task_list = []
        self.task_index = 0
        self.curr_task = None
        self.slct_task = None
        self.cmd_list = []
        self.cmd_index = 0
        self.index = 0
        self.branch_idx = 0
        self.branch_lastpar = None
        self.branch_code = ''
        self.tree_arr = []
        self.tree_idx = 0

        self.endes = []
        self.endes_idx = 0

        self.browser = WebBrowser()

        self.need_human_response = False
        # TODO: установить как значение по умолчанию
        self.path = 'saved'
        self.proj_pref = ''
        self.return_points = []
        self.selected_tasks = []
        self.info = None
        self.tc_start = False
        self.tc_stop = False

    def getCurrentTask(self) -> BaseTask:
        return self.curr_task

    def addTaskToSelectList(self, task :BaseTask):
        self.selected_tasks.append(task)

    def clearSelectList(self):
        self.selected_tasks.clear()
        return ','.join( self.getSelectList())

    def addCurrTaskToSelectList(self):
        self.addTaskToSelectList(self.curr_task)
        return ','.join( self.getSelectList())

    def getSelectList(self) -> list:
        return [t.getName() for t in self.selected_tasks]
    
    def createCollectTreeOnSelectedTasks(self, action_type):
        self.createTreeOnSelectedTasks(action_type,"Collect")

    def createTreeOnSelectedTasks(self, action_type : str, task_type : str):
        first = True
        trg = self.curr_task
        task_list = self.selected_tasks.copy()
        for task in task_list:
            # TODO: Заменить на запрос к MakeAction
            self.curr_task = trg
            self.makeTaskAction("",task_type, action_type, 'user')
            # if first:
            #     parent = None
            #     if action_type == 'SubTask':
            #         parent = self.curr_task
            #     self.createOrAddTask("",task_type,"user",parent,[])
            #     first = False
            # else:
            #     parent = self.curr_task
            #     self.createOrAddTask("",task_type,"user",parent,[])
            self.makeLink(self.curr_task, task)
        self.clearSelectList()
        return self.getCurrTaskPrompts()
    
    def moveCurrentTaskUP(self):
        self.moveTaskUP(self.curr_task)
        return self.getCurrTaskPrompts()
    
    def moveTaskUP(self, task : BaseTask):
        info = TaskDescription(target=task)
        cmd = edit.MoveUpTaskCommand(info)
        self.cmd_list.append(cmd)
        return self.runIteration('')



    def getPath(self) -> str:
        return self.path
    
    def setPath(self, path : str):
        self.path = path

    def getTaskExtention(self) -> str:
        return '.json'

    def getProjPrefix(self) -> str:
        return self.proj_pref

    def loadTasksList(self):
        # print(10*"=======")
        # print('Load tasks from files')
        task_manager = TaskManager()
        links = task_manager.getLinks(self.getPath())
        self.createTask()

        # print('Links', links)

        for link in links:
            trgs = link['linked']
            affect_task = self.getTaskByName(link['name'])
            for trg in trgs:
                influense_task = self.getTaskByName(trg)
                self.makeLink(affect_task, influense_task)

        for task in self.task_list:
                task.completeTask()

        # for task in self.task_list:
        #     print("Task name=", task.getName(), " affected")
        #     for info in task.by_ext_affected_list:
        #         print("by ",info.parent.getName())
        #     print("influence")
        #     for info in task.affect_to_ext_list:
        #         print("to ",info.parent.getName())

    def goToNextTreeFirstTime(self):
        for task in self.task_list:
            if task.isRootParent():
                self.tree_arr.append(task)
        if len(self.tree_arr) > 0:
            self.curr_task = self.tree_arr[0]
            self.tree_idx = 1

    def getTreeNamesForRadio(self):
        names = []
        for task in self.tree_arr:
            names.append(task.getBranchSummary())
        trg = self.curr_task.getBranchSummary()
        return gr.Radio(choices=names, value=trg, interactive=True)
    
    def getCurrentTreeNameForTxt(self):
        return gr.Textbox(value=self.curr_task.getBranchSummary(), interactive=True)
    
    def goToTreeByName(self, name):
        for i in range(len(self.tree_arr)):
            trg = self.tree_arr[i].getBranchSummary()
            if trg == name:
                self.curr_task = self.tree_arr[i]
                self.tree_idx = i
                break
        return self.goToNextBranchEnd()


    def goToNextTree(self):
        # print('Current tree was',self.tree_idx,'out of',len(self.tree_arr))
        if len(self.tree_arr) > 0:
            for task in self.tree_arr:
                if not task.isRootParent():
                    self.goToNextTreeFirstTime()
                    return self.getCurrTaskPrompts()
                
            if self.tree_idx + 1 < len(self.tree_arr):
                self.tree_idx += 1
            else:
                self.tree_idx = 0
            self.curr_task = self.tree_arr[self.tree_idx]
        else:
            self.goToNextTreeFirstTime()
        # print('Current task is', self.curr_task.getName())
        return self.getCurrTaskPrompts()

    def takeFewSteps(self, dir:str, times : int):
        for idx in range(times):
            if dir == 'child':
                self.goToNextChild()
            elif dir == 'parent':
                self.goToParent()

    # Переключаться между наследованием со спуском вниз: от родителя к потомку. Потомков может быть несколько, поэтому существует неопределенность со следующим наследником.
    # Текущий вариант не отслеживает начальную ветку
    def goToNextChild(self):
        # Список направлений
        prev = self.curr_task
        chs = self.curr_task.getChilds()
        self.curr_task = None
        # Если есть потомки
        if len(chs) > 0:
            # Если потомков нескольно
            if len(chs) > 1:
                self.branch_lastpar = self.curr_task
                self.branch_idx = 0
                # С использованием кода
                # Запоминаем место ветвления
                for ch in chs:
                # Перебираем коды потомков
                    ch_tag = ch.getBranchCodeTag()
                    # Если код совпал с кодом в памяти
                    print('Check', ch_tag,'with',self.branch_code)
                    if ch_tag.startswith(self.branch_code):
                        # Установить новую текущую
                        self.curr_task = ch
        else:
            self.curr_task = prev

        # Обычный вариант
        if self.curr_task is None:
            # Выбираем просто нулевую ветку
            self.curr_task = chs[0]
        return self.getCurrTaskPrompts()
    
    def goToParent(self):
        if self.curr_task.parent is not None:
            self.curr_task = self.curr_task.parent
        return self.getCurrTaskPrompts()
    
    def getSceletonBranchBuds(self, trg_task :BaseTask):
        tree = trg_task.getTree()
        endes = []
        for task in tree:
            if len(task.getChilds()) == 0:
                endes.append(task)
        return endes
    
    # Перебираем все возможные варианты листьев/почек деревьев
    def goToNextBranchEnd(self):
        if len(self.endes) == 0:
            self.endes = self.getSceletonBranchBuds(self.curr_task)
            self.endes_idx = 0
        else:
            endes = self.getSceletonBranchBuds(self.curr_task)
            if endes == self.endes:
                if self.endes_idx + 1 < len(self.endes):
                    self.endes_idx += 1
                else:
                    self.endes_idx = 0
            else:
                self.endes = endes
                self.endes_idx = 0
        self.curr_task = self.endes[self.endes_idx]
        self.branch_code = self.curr_task.getBranchCodeTag()
        print('Get new branch code:', self.branch_code)
        return self.getCurrTaskPrompts()

    def goToNextBranch(self):
        trg = self.curr_task
        idx = 0
        while(idx < 1000):
            if trg.isRootParent():
                return self.getCurrTaskPrompts()
            if len(trg.parent.getChilds()) > 1:
                if self.branch_lastpar is not None and trg.parent == self.branch_lastpar:
                    self.curr_task = trg.parent.childs[self.branch_idx]
                    if self.branch_idx + 1 < len(trg.parent.getChilds()):
                        self.branch_idx += 1
                    else:
                        self.branch_idx = 0
                else:
                    self.branch_lastpar = trg.parent
                    self.curr_task = trg.parent.childs[0]
                    self.branch_idx += 1
                break
            else:
                trg = trg.parent
            idx += 1
        return self.getCurrTaskPrompts()


    def getTextFromFile(self, text, filenames):
        if filenames is None:
            return text
        print("files=",filenames.name)
        with open(filenames.name) as f:
            text += f.read()
        return text

    def createTask(self, prnt_task = None):
        # print(10*"=======")
        if prnt_task == None:
            parent_path = ""
        else:
            parent_path = prnt_task.path
            self.curr_task = prnt_task
            # print("task=", self.curr_task.path)
            # print("Parent task path=", parent_path)
        init_task_list = self.task_list.copy()
        task_manager = TaskManager()
        parent_prompt_list = task_manager.getTaskPrompts(self.getPath(), parent_path)

        # print("prompt count=",len(parent_prompt_list))

        for prompt in parent_prompt_list:
            self.curr_task = prnt_task
            # print("content=",prompt['content'])
            if parent_path == "":
                self.makeTaskAction(prompt['content'], prompt['type'], "New", prompt['role'])
            else:
                self.makeTaskAction(prompt['content'], prompt['type'], "SubTask",prompt['role'])

        trg_task_list = self.task_list.copy()

        # print("task count=",len(self.task_list),",exclude=",len(init_task_list))
        if len(parent_prompt_list):
            for task in trg_task_list:
                if task not in init_task_list:
                    # print("+++",parent_path)
                    self.createTask(task)
        

    def setNextTask(self, input):
        saver = SaveData()
        chck = gr.CheckboxGroup.update(choices=saver.getMessages())

        try:
            inc = int(input)
        except ValueError:
            print("Value error")
        #Try float.
            # ret = float(s)
            return self.getCurrTaskPrompts()
        print("Increment=",inc)
        self.task_index += inc

        if len(self.task_list) <= self.task_index:
            self.task_index = 0
        elif self.task_index < 0:
            self.task_index = len(self.task_list) - 1


        self.curr_task = self.task_list[self.task_index]

        # return self.drawGraph(), pprint.pformat((self.curr_task.msg_list))
        # tokens, price = self.curr_task.getCountPrice()
        # output = "Tokens=" + str(tokens) +"\n"
        # output += "Price=" + str(price) + "\n"
        output = ""
        output += pprint.pformat(self.curr_task.msg_list)
        in_prompt, in_role, out_prompt = self.curr_task.getMsgInfo()
        return self.getCurrTaskPrompts()

        # std_output_list = [info, output, graph_img, input, creation_tag_list]
        # next_task_btn.click(fn=manager.setNextTask, outputs=[graph_img, input, creation_tag_list, info], api_name='next_task')


    def updateGraph(self, image):
        print("Update graph")
        img = image['image']
        # img = {'mask' : None}
        return img
    
    def getActionTypes(self):
        return ["New", "SubTask","Edit","Delete", "Select", "Link", "Unlink", "Parent", "RemoveParent"]
    
    def getRoleTypes(self):
        return ["user","assistant"]

    def getTaskJsonStr(self):
        out = []
        for task in self.task_list:
            out.append(task.getJson())
        res = {"tasks" : out}
        types = [t for t in self.helper.getNames()]
        res['types'] = types
        res['roles'] = self.getRoleTypes()
        res['actions'] = self.getActionTypes()
        return res

        # return json.dumps(res)

    def getTaskParamRes(self, task, param) -> bool:
        r,v = task.getParam(param)
        return r and v
    
    def drawSceletonBranches(self):
        f = graphviz.Digraph(comment='The Test Table')
        sceleton_branches = []
        for sc_branch in self.tree_arr:
            task = sc_branch
            f.node( task.getIdStr(), task.getName(),style="filled",color="skyblue")
            buds = self.getSceletonBranchBuds(sc_branch)
            sc_br = {'root': sc_branch,'buds':[]}
            for bud in buds:
                f.node( bud.getIdStr(), bud.getName(),style="filled",color="skyblue")
                f.edge(task.getIdStr(), bud.getIdStr())
                branch = bud.getAllParents()
                garland_holders = []
                for t in branch:
                    garland_holders.extend(t.getHoldGarlands())
                sc_br['buds'].append({'bud':bud,'holds':garland_holders})

            sceleton_branches.append(sc_br)

        for trg_sceleton_branch in sceleton_branches:
            for sceleton_branch in sceleton_branches:
                if sceleton_branch is not trg_sceleton_branch:
                    for bud in sceleton_branch['buds']:
                        branch = bud['bud'].getAllParents()
                        for t in branch:
                            for trg_bud in trg_sceleton_branch['buds']:
                                if t in trg_bud['holds']:
                                    f.edge(trg_bud['bud'].getIdStr(), bud['bud'].getIdStr())


        img_path = "output/tree"
        f.render(filename=img_path,view=False,format='png')
        img_path += ".png"
        return img_path


    def drawGraph(self, only_current= True):
        # print('Draw graph')
        if only_current:
            if self.curr_task.isRootParent():
                trg_list = self.curr_task.getTree()
            else:
                trg_list = self.curr_task.getAllParents()
                trg_list.extend(self.curr_task.getAllChildChains()[1:])
        else:
            trg_list = self.task_list
        # print('Target tasks:',[t.getName() for t in trg_list])
        if len(trg_list) > 0:
            f = graphviz.Digraph(comment='The Test Table',
                                  graph_attr={'size':"7.75,10.25",'ratio':'fill'})

            # if self.curr_task:
            #         f.node ("Current",self.curr_task.getInfo(), style="filled", color="skyblue", shape = "rectangle", pos = "0,0")
            trgs_rsm = []
            for task in self.task_list:
                if len(task.getAffectedTasks()) > 0:
                    trgs = task.getAffectedTasks()
                    if trgs in trg_list:
                        trg_list.append(task)

            

            for task in trg_list:
                if task in trgs_rsm:
                    if task == self.curr_task:
                        f.node( task.getIdStr(), task.getName(),style="filled",color="blueviolet")
                    else:
                        f.node( task.getIdStr(), task.getName(),style="filled",color="darkmagenta")
                elif task == self.curr_task:
                    f.node( task.getIdStr(), task.getName(),style="filled",color="skyblue")
                    # f.node ("Current",task.getInfo(), style="filled", color="skyblue", shape = "rectangle", pos = "0,0")
                    # f.edge (task.getIdStr(), "Current", color = "skyblue", arrowhead = "dot")
                elif task ==self.slct_task:
                    f.node( task.getIdStr(), task.getName(),style="filled",color="darksalmon")
                else:
                    if self.getTaskParamRes(task, "block"):
                    # if task.getParam("stopped") == [True, True]:
                        f.node( task.getIdStr(), task.getName(),style="filled",color="gold2")
                    elif self.getTaskParamRes(task, "input"):
                    # elif task.getParam("input") == [True, True]:
                        f.node( task.getIdStr(), task.getName(),style="filled",color="aquamarine")
                    elif self.getTaskParamRes(task, "output"):
                    # elif task.getParam("output") == [True, True]:
                        f.node( task.getIdStr(), task.getName(),style="filled",color="darkgoldenrod1")
                    elif self.getTaskParamRes(task, "check"):
                        f.node( task.getIdStr(), task.getName(),style="filled",color="darkorchid1")
                    elif task.is_freeze:
                        f.node( task.getIdStr(), task.getName(),style="filled",color="cornflowerblue")
                    elif len(task.getAffectedTasks()) > 0:
                        f.node( task.getIdStr(), task.getName(),style="filled",color="aquamarine4")
                    else:
                        info = task.getInfo()
                        if task.prompt_tag == "assistant":
                            f.node( task.getIdStr(), task.getName(),style="filled",color="azure2")
                        else:
                            f.node( task.getIdStr(), task.getName())


                # print("info=",task.getIdStr(),"   ", task.getName())
            
            for task in trg_list:
                if task.getType() == "IterationEnd":
                    if task.iter_start:
                        f.edge(task.getIdStr(), task.iter_start.getIdStr())
                for child in task.childs:
                    f.edge(task.getIdStr(), child.getIdStr())
                    # print("edge=", task.getIdStr(), "====>",child.getIdStr())

                for info in task.by_ext_affected_list:
                    # print("by ",info.parent.getName())
                    f.edge(info.parent.getIdStr(), task.getIdStr(), color = "darkorchid3", style="dashed")

            img_path = "output/img"
            f.render(filename=img_path,view=False,format='png')
            img_path += ".png"
            return img_path
        return "output/img.png"
    
    # def updatePromptForTask(self, input):
        # print("in=",input)
    def updatePromptForTask(self, task_name, task_prompt):
        print(20*"====")
        print("Update prompt for ", task_name)
        print(20*"====")
        task = self.getTaskByName(task_name)
        self.curr_task = task
        creation_tag = task.prompt_tag
        info = TaskDescription(prompt=task_prompt,prompt_tag=creation_tag, manual=True)
        self.curr_task.update(info)
        return self.getOutputDataSum()

    def getOutputDataSum(self):
        out = ""
        for task in self.task_list:
            r,v = task.getParam("output")
            if r and v:
                out += "Response from " + task.getName()  + "\n"
                out += 10*"=====" + "\n"
                out += task.getInfo(short=False)
                out += "\n"

        i = 0
        sum = len(self.task_list)
        for task in self.task_list:
            if not task.is_freeze:
                i += 1

        out += "\n Done: " + str(i) + " of " + str(sum)
        return out

    def updateAndGetOutputDataSum(self):
        self.update()
        return self.getOutputDataSum()

    def getFlagTaskLst(self):
        out = []
        for task in self.task_list:
            r,v = task.getParam("input")
            if r and v:
                out.append({"name" : task.getName(), "type" : "input"})
            r,v = task.getParam("output")
            if r and v:
                out.append({"name" : task.getName(), "type" : "output"})
        return out
    
    def getMainCommandList(self):
        return ["New", "SubTask","Edit","Delete", "Select", "Link", "Unlink", "Parent", "RemoveParent","EditAndStep","EditAndStepTree"]
    def getSecdCommandList(self):
        return ["MoveUp","RemoveBranch", "RemoveTree", "Insert","Remove","ReqResp"]
    
    def makeRequestAction(self, prompt, selected_action, selected_tag):
        print('Make',selected_action,'Request')
        if selected_action == "New" or selected_action == "SubTask":
            return self.makeTaskAction(prompt, "Request", selected_action, "user")
        if selected_action == "Edit":
            return self.makeTaskAction(prompt, "Request", selected_action, selected_tag)
        
       
        
    def makeResponseAction(self, selected_action):
        return self.makeTaskAction("", "Response",selected_action, "assistant")
        
 
    def makeTaskAction(self, prompt, type, creation_type, creation_tag):
        if creation_type in self.getMainCommandList() or creation_type in self.vars_param:
            return self.makeTaskActionBase(prompt, type, creation_type, creation_tag)
        elif creation_type in self.getSecdCommandList():
            return self.makeTaskActionPro(prompt, type, creation_type, creation_tag)
        saver = SaveData()
        chck = gr.CheckboxGroup.update(choices=saver.getMessages())
        return "", "" ,self.drawGraph(),"" , "user", chck
    
 
    def makeTaskActionPro(self, prompt, type, creation_type, creation_tag):
        if creation_type == "RemoveBranch":
            tasks = self.curr_task.getChainBeforeBranching()
            for task in tasks:
                self.curr_task = task
                self.makeTaskActionBase(prompt, type, "Delete", creation_tag)
        elif creation_type == "RemoveTree":
            tasks = self.curr_task.getTree()
            for task in tasks:
                self.curr_task = task
                self.makeTaskActionBase(prompt, type, "Delete", creation_tag)
        elif creation_type == "Insert":
            task1 = self.curr_task.parent
            task2 = self.curr_task
            if task1:
                # self.makeTaskActionBase(prompt, type, "RemoveParent", creation_tag)
                self.curr_task = task1
                self.makeTaskActionBase(prompt, type, "SubTask", creation_tag)
            else:
                self.makeTaskActionBase(prompt, type, "New", creation_tag)
            task_12 = self.curr_task
            self.slct_task = self.curr_task
            self.selected_tasks = [self.curr_task]
            self.curr_task = task2
            if task1 is not None:
                task1.addChild(task_12)
                task2.removeParent()
                task_12.addChild(task2)
                task1.saveAllParams()
                task2.saveAllParams()
                task_12.saveAllParams()
            # self.makeTaskActionBase(prompt, type, "Parent", creation_tag)
            try:
            # if task1 is not None:
                print('Parents\nFirst', task1.parent.getName() if task1.parent is not None else 'None','=',task1.getName())
                print('Childs')
                for ch in task1.getChilds():
                    print(ch.getName())
            
                # print(task1.queue)
            # if self.slct_task is not None:
                print('Middle', self.slct_task.parent.getName() if self.slct_task.parent is not None else 'None','=',self.slct_task.getName())
                print('Childs')
                for ch in self.slct_task.getChilds():
                    print(ch.getName())
                # print(self.slct_task.queue)
                print('Last', self.curr_task.parent.getName() if self.curr_task.parent is not None else 'None','=', self.curr_task.getName())
                print('Childs')
                for ch in self.curr_task.getChilds():
                    print(ch.getName())
            except Exception as e:
                print('Error:', e)
            # print(self.curr_task.queue)
            # if task1 is not None:
            #     task1.update()
            # else:
            #     self.slct_task.update()
            self.curr_task = self.slct_task
            print('Selected',self.slct_task.getName())
            print('Current', self.curr_task.getName())

        elif creation_type == "Remove":
            task1 = self.curr_task.parent
            task2 = self.curr_task
            task3_list = task2.getChilds()
            for task in task3_list:
                task.removeParent()
                if task1 is not None:
                    task1.addChild(task)
            self.curr_task = task2
            self.makeTaskActionBase(prompt, type, "Delete", creation_tag)
           
        elif creation_type == "ReqResp":
            if self.curr_task is not None:
                self.makeTaskActionBase(prompt,"Request","SubTask","user")
            else:
                self.makeTaskActionBase(prompt,"Request","New","user")
            self.makeTaskActionBase(prompt,"Response","SubTask","assistant")
        elif creation_type == "MoveUp":
            return self.moveCurrentTaskUP()
            
        return self.getCurrTaskPrompts()

    def updateTaskParam(self, param):
        self.curr_task.setParam(param)
        return self.getCurrTaskPrompts()
    
    def makeTaskActionBase(self, prompt, type, creation_type, creation_tag):
        # print(10*"==")
        # print("Create new task")
        # print("type=",type)
        # print("prompt=", prompt)
        # print("creation type=", creation_type)
        out = ""
        log = "Nothing"
        img_path = "output/img.png"
        # print(10*"====")
        # print("Make action", creation_type)
        # print(10*"====")

        if type is None or creation_type is None:
            print('Abort maske action')
            return self.getCurrTaskPrompts()
        if creation_type == "Edit":
            info = TaskDescription(prompt=prompt,prompt_tag=creation_tag)
            info.target = self.curr_task
            cmd = edit.EditCommand(info)
            self.cmd_list.append(cmd)
            return self.runIteration()
        elif creation_type == "EditAndStep":
            info = TaskDescription(prompt=prompt,prompt_tag=creation_tag, manual=True, stepped=True)
            self.updateSteppedSelectedInternal(info)
            return self.getCurrTaskPrompts()
        elif creation_type == "EditAndStepTree":
            info = TaskDescription(prompt=prompt,prompt_tag=creation_tag, manual=True, stepped=True)
            self.updateSteppedTree(info)
            return self.getCurrTaskPrompts()
        vars_param = self.vars_param
        for param in vars_param:
            input_params= {"name" :param, "value" : True,"prompt":None}
            if creation_type == param:
                input_params["value"] = True
            elif creation_type == "un" + param:
                input_params["value"] = False
            else:
                continue
            if creation_type == "watched":
                # input_params["prompt"] = {"message": prompt, "options":["good","bad"]}
                res, cparam = self.curr_task.getParamStruct("watched")
                w_list = []
                if res and "targets" in cparam and self.slct_task.getName() not in cparam["targets"]:
                    w_list = cparam["targets"]
                    w_list.append(self.slct_task.getName())
                    input_params["prompt"] = {"targets":w_list}
                elif self.slct_task:
                    input_params["prompt"] = {"targets":[self.slct_task.getName()]}

            info = TaskDescription( prompt=self.curr_task.getLastMsgContent(), prompt_tag=self.curr_task.getLastMsgRole(), params=[input_params], target=self.slct_task)
            # info = TaskDescription(prompt=self.curr_task.prompt,prompt_tag=self.curr_task.prompt_tag, params=[input_params])
            self.curr_task.update(info)
            return self.getCurrTaskPrompts()
             # return self.runIteration(prompt)
        if creation_type == "Select":
            self.slct_task = self.curr_task
            return self.runIteration(prompt)
        elif creation_type == "RemoveParent":
            if self.curr_task != self.slct_task and self.curr_task:
                info = TaskDescription(target=self.curr_task)
                cmd = parcmd.RemoveParentCommand(info)
                self.cmd_list.append(cmd)
            return self.runIteration(prompt)
        elif creation_type == "Parent":
            for t in self.selected_tasks:
                print("Make ", t.getName()," parent of ", self.curr_task.getName())
                info = TaskDescription( )
                info.target = self.curr_task
                info.parent = t 
                cmd = parcmd.ParentCommand(info)
                self.cmd_list.append(cmd)
                break
            return self.runIteration(prompt)
        elif creation_type == "Unlink":
            if self.curr_task:
                info = TaskDescription(target=self.curr_task)
                cmd = lnkcmd.UnLinkCommand(info)
                self.cmd_list.append(cmd)
            return self.runIteration(prompt)
        elif creation_type == "Link":
            for t in self.selected_tasks:
                self.makeLink(self.curr_task, t)
                break
            return self.runIteration(prompt)
        elif creation_type == "Delete":
        # TODO: после удаления возвращаться к тому же дереву
            task = self.curr_task
            info = TaskDescription(target=self.curr_task)
            cmd_delete = create.RemoveCommand(info)
            self.cmd_list.append(cmd_delete)
            self.runIteration(prompt)
            if task in self.tree_arr:
                self.tree_arr.remove(task)
            self.setNextTask("1")
            del task
            return self.getCurrTaskPrompts()
        elif creation_type == "New":
            parent = None
            if cr.checkTypeFromName(type, "Response"):
                print('Can\'t create new Response')
                return self.getCurrTaskPrompts()
        elif creation_type == "SubTask":
            parent = self.curr_task
        else:
            return self.getCurrTaskPrompts()
        
        return self.createOrAddTask(prompt,type, creation_tag, parent,[])
        
    def createOrAddTask(self, prompt, type, tag, parent, params = []):
        # print('Create task')
        # print('Params=',params)
        info = TaskDescription(prompt=prompt, prompt_tag=tag, 
                                                             helper=self.helper, requester=self.requester, manager=self, 
                                                             parent=parent, params=params)
        # if params is not None:
            # info.params = params
        curr_cmd = cr.createTaskByType(type, info)

        if not curr_cmd:
            return self.getCurrTaskPrompts()
        self.cmd_list.append(curr_cmd)
        return self.runIteration(prompt)

    
    def makeLink(self, task_in : BaseTask, task_out :BaseTask):
        if task_in != None and task_out != None:
            if task_out.getType() == 'Collect' and task_in.getType() == 'Collect':
                print('Relink from', task_out.getName(),':')
                trgs = task_out.getAffectingOnTask()
                for trg in trgs:
                    print("   - [Make link] from ", trg.getName(), " to ", task_in.getName())
                    info = TaskDescription(target=task_in, parent=trg)
                    cmd = lnkcmd.LinkCommand(info)
                    self.cmd_list.append(cmd)
            else:
                print("[Make link] from ", task_out.getName(), " to ", task_in.getName())
                info = TaskDescription(target=task_in, parent=task_out)
                cmd = lnkcmd.LinkCommand(info)
                self.cmd_list.append(cmd)
        self.runIteration()



    def getTaskByName(self, name : str) -> BaseTask:
        for task in self.task_list:
            if task.getName() == name:
                return task
        return None
    
    def updateSetOption(self, task_name, param_name, key, value):
        print("Update set options")
        task = self.getTaskByName(task_name)
        if task.getType() == "SetOptions":
            task.updateParamStruct(param_name, key, value)
            return value
        return None

    def getFromSetOptions(self, task :BaseTask):
        group = []
        lst = task.getParamList()
        if lst is not None:
            for param in lst:
                print("Param:",param)
                out = {"type":param["type"],"parameters":[]}
                if "type" in param:
                    if param["type"] == "model":
                        chat = SimpleChatGPT()
                        val = {"ui":"listbox","key":"model","value":chat.getModelList()}
                        
                    for k,p in param.items():
                        if k != "type" and k != "model":
                            val = {"ui":"textbox","type":param["type"],"key":k,"value":p}
                            if isinstance(p, bool):
                                val["ui"] = "checkbox"
                    out["parameters"].append(val)
                group.append(out)
        return group
        
 
    def getTaskList(self):
        # print('Get tasks list')
        out = []
        for task in self.task_list:
            out.append(task.getName())
        return out
    
    def getCurrTaskName(self):
        if self.curr_task:
            return self.curr_task.getName()
        return "None"
    
    def setCurrentTaskByName(self, name):
        task = self.getTaskByName(name)
        if task:
            print("Set current task=", task.getName())
            self.curr_task = task
        
        for i in range(0, len(self.task_list)):
            if self.task_list[i] == task:
                self.task_index = i
        return self.getCurrTaskPrompts() 
           # in_prompt, in_role, out_prompt = self.curr_task.getMsgInfo()
        # return self.drawGraph(), gr.Dropdown.update(choices= self.getTaskList()), in_prompt, in_role, out_prompt

    def setSelectedTaskByName(self, name):
        task = self.getTaskByName(name)
        if task:
            print("Set current task=", task.getName())
            self.slct_task = task
 
    def runIteration(self, prompt = ''):
        # print("Run iteration")

        if self.need_human_response:
            self.need_human_response = False
            return self.getCurrTaskPrompts()

        self.index += 1
        log = 'id[' + str(self.index) + '] '
        out = "Report:\n"
        if len(self.cmd_list) > 0:
            cmd = self.cmd_list.pop(0)
            log += 'Command executed: '
            log += str(cmd) + '\n'
            log += "Command to execute: " + str(len(self.cmd_list)) +"\n"
            task, action = cmd.execute()
            if action == 'create' and task != None:
                self.task_list.append(task)
                if task.isRootParent():
                    self.tree_arr.append(task)
                self.curr_task = task
            elif action == 'delete':
                self.task_list.remove(task)
                self.curr_task = self.task_list[0]
            # log += task.task_creation_result
            out += str(task) + '\n'
            out += "Task description:\n"
            # out += task.task_description
            return self.getCurrTaskPrompts()


        all_task_expanded = False 
        if len(self.task_list) > 0:
            all_task_expanded = True
        # for task in self.task_list:
        #     log += "["+ str(index) + "] "
        #     index += 1
        #     cmd = task.getCmd()
        #     if (cmd != None):
        #         log += "From task:" + str(task) + " "
        #         log += "add command:" + str(cmd)
        #         self.cmd_list.append(cmd)
        #         all_task_expanded = False
        all_task_completed = False
        if all_task_expanded:
            all_task_completed = True
            log += "All task expanded\n"
            print("Complete task list")
            for task in self.task_list:
                if not task.completeTask():
                    all_task_completed = False
                else:
                    print("task complete=",str(task))

        if self.curr_task:
            tokens, price = self.curr_task.getCountPrice()
            out += "Tokens=" + str(tokens) +"\n"
            out += "Price=" + str(price) + "\n"
            out += pprint.pformat(self.curr_task.msg_list)


        if all_task_completed:
            log += "All task complete\n"
        if len(self.task_list) == 0:
            if True:
                log += "No any task"
                return self.getCurrTaskPrompts()

        out += 'tasks: ' + str(len(self.task_list)) + '\n'
        out += 'cmds: ' + str(len(self.cmd_list)) + '\n'
        return self.getCurrTaskPrompts()
    
    def updateCurrent(self):
        self.curr_task.update()
        return self.runIteration("")
    
    def update(self):
        print(10*"----------")
        print("NEW UPDATE",10*">>>>>>>>>>>")
        print(10*"----------")
        for task in self.task_list:
            if task.parent == None:
                task.update()
        return self.runIteration("")
    
    def updateSteppedSelectedInternal(self, info : TaskDescription = None):
        # print(10*"----------")
        # print("STEP",8*">>",self.curr_task.getName(),"||||||")
        # print(10*"----------")
        if info:
            info.stepped = True
            self.curr_task.update(info)
        else:
            # idx = 0
            # while(idx < 1000):
            #     if self.curr_task.isRootParent():
            #         print('Parent of',self.curr_task.getName(),' is None')
            #         break
            #     if self.curr_task.parent.findNextFromQueue(True) is not None:
            #         par = self.curr_task.parent
            #         self.curr_task = par
            #     else:
            #         print('Can\'t step on',self.curr_task.parent.getName())
            #         break
            #     idx += 1
            # print('Use old prompt:', self.curr_task.getLastMsgContent())
            self.curr_task.update(TaskDescription( prompt=self.curr_task.getLastMsgContent(), prompt_tag=self.curr_task.getLastMsgRole(), stepped=True))

        res, w_param = self.curr_task.getParamStruct("watched")
        if res:
            saver = SaveData()
            names = self.curr_task.getBranchedName()
            trgs = []
            if "targets" in w_param:
                for trg in w_param["targets"]:
                    task = self.getTaskByName(trg)
                    trgs.append({"name" : task.getName(), "chat": task.getMsgs()})
            pack = saver.makePack(name=names, message=self.curr_task.findKeyParam( self.curr_task.getLastMsgContent()),chat= self.curr_task.getMsgs(), chat_raw=self.curr_task.msg_list, targets=trgs)
            saver.save(pack)



        next = self.curr_task.getNextFromQueue()
        if next not in self.curr_task.getTree():
            # print('Go to the next tree')
            self.return_points.append(self.curr_task)
        # print(len(self.return_points))
        if next and self.curr_task != next:
            # if next.parent == None:
                # next.resetTreeQueue()
            self.curr_task = next
        else:
            if len(self.return_points) > 0:
                self.curr_task = self.return_points.pop()
            elif self.curr_task.parent:
                # print("Done some")
                pass
            else:
                # print("On start")
                pass
        # print("Next task is", next.getName())
        return next
    
    def resetCurTaskQueue(self):
        self.curr_task.resetTreeQueue()
        return self.getCurrTaskPrompts()
    
    def fixTasks(self):
        for task in self.task_list:
            task.fixQueueByChildList()
        return self.getCurrTaskPrompts()
    
    def updateAndExecuteStep(self, msg):
        self.curr_task.resetTreeQueue()
        info = TaskDescription(prompt=msg,
                                prompt_tag=self.curr_task.getLastMsgRole(),
                                manual=True)
        self.updateSteppedSelectedInternal(info)
        return self.getCurrTaskPrompts()

    def executeStep(self):
        self.updateSteppedSelectedInternal()
        return self.getCurrTaskPrompts() 
    
    def executeSteppedBranch(self, msg):
        info = TaskDescription(prompt=msg,
                                prompt_tag=self.curr_task.getLastMsgRole(),
                                manual=True)
        self.updateSteppedTree(info)
        for task in self.task_list:
            res, val = task.getParamStruct('output')
            if res and val['output']:
                self.curr_task = task
                break
        return self.getCurrTaskPrompts() 

    def updateSteppedTrgBranch(self, info = None):
        info = TaskDescription(prompt=self.curr_task.getLastMsgContent(),
                                prompt_tag=self.curr_task.getLastMsgRole(),
                                manual=True)
        self.updateSteppedTree(info)

        # if self.curr_task.parent == None:
        #     self.updateSteppedTree(info)
        # else:
        #     branches = [ch.getName() for ch in self.curr_task.parent.getChilds() if ch != self.curr_task]
        #     print('Update branch until:', branches)
        #     index = 0
        #     while(index < 100):
        #         if index == 0 and info is not None:
        #             next = self.updateSteppedSelectedInternal(info)
        #         else:
        #             next = self.updateSteppedSelectedInternal()
        #         if next is None or next.getName() in branches or next.isRootParent():
        #             print("Done in",index,"iteration")
        #             break
        #         index +=1
        return self.getCurrTaskPrompts() 

    
    def updateSteppedTree(self, info = None):
        index = 0
        self.curr_task.resetTreeQueue()
        last = self.curr_task
        processed_chain = [last.getName()]
        while(index < 1000):
            if index == 0 and info is not None:
                next = self.updateSteppedSelectedInternal(info)
            else:
                next = self.updateSteppedSelectedInternal()
            if next is None:
                # print("Done in",index,"iteration")
                break
            else:
                if last == next:
                    # print("Get repeat in",index,"iteration")
                    break
                else:
                    # print('After',last.getName(),'will be', next.getName())
                    processed_chain.append(next.getName())
                    last = next
            index +=1
        print('Done: update tree step by step in', index)
        print('Tree execution:','->'.join(processed_chain))
        return self.getCurrTaskPrompts() 
    
    
    def getCurTaskLstMsg(self) -> str:
        return self.curr_task.getMsgs()[-1]['content']
    
    def getCurTaskLstMsgRaw(self) -> str:
        return self.curr_task.getLastMsgContentRaw()
    
    
    def copyToClickBoardLstMsg(self):
        msg = self.getCurTaskLstMsg()
        pyperclip.copy(msg)
        pyperclip.paste()

    
    def copyToClickBoardDial(self):
        msgs = self.curr_task.getMsgs()
        text = ""
        for msg in msgs:
            text += msg['role'] + '\n' + 10*'====' + '\n\n\n'
            text += msg['content'] + '\n'
        pyperclip.copy(text)
        pyperclip.paste()

    def copyToClickBoardTokens(self):
        tokens, price = self.curr_task.getCountPrice()
        text  = 'Tokens: ' + str(tokens) + ' price: ' + str(price)
        pyperclip.copy(text)
        pyperclip.paste()

    def getCurrentExtTaskOptions(self):
        p = []
        names = finder.getExtTaskSpecialKeys()
        for name in names:
            res, val = self.curr_task.getParamStruct(name)
            # print(name,'=',val)
            if res and val[name]:
                p.append(name)
        return gr.CheckboxGroup(choices=names,value = p, interactive=True)
    
    def setCurrentExtTaskOptions(self, names : list):
        full_names = finder.getExtTaskSpecialKeys()
        for name in full_names:
            if name not in names:
                self.curr_task.updateParam2({'type': name, name : False})
            else:
                self.curr_task.updateParam2({'type': name, name : True})

        self.curr_task.saveAllParams()
        return self.getCurrentExtTaskOptions()
    
    def resetAllExtTaskOptions(self):
        full_names = finder.getExtTaskSpecialKeys()
        full_names.remove('input')
        for task in self.task_list:
            for name in full_names:
                task.updateParam2({'type': name, name : False})
            task.saveAllParams()
        return self.getCurrentExtTaskOptions()

    
    def getCurrTaskPrompts(self, set_prompt = ""):
        msgs = self.curr_task.getMsgs()
        out_prompt = ""
        out_prompt2 = ""
        if msgs:
            out_prompt = msgs[-1]["content"]
            if len(msgs) > 1:
                out_prompt2 = msgs[-2]["content"]
        saver = SaveData()
        chck = gr.CheckboxGroup.update(choices=saver.getMessages())
        in_prompt, in_role, out_prompt22 = self.curr_task.getMsgInfo()
        self.curr_task.printQueueInit()
        #quick fix
        r_msgs = []
        first = ""
        sec = ""
        for msg in msgs:
            if msg['role'] == 'assistant':
                sec = msg['content']
                r_msgs.append([first, sec])
                first = ""
                sec = ""
            else:
                if first != "":
                    r_msgs.append([first, sec])
                    first = msg['content']
                    r_msgs.append([first, sec])
                    first = ""
                    sec = ""
                else:
                    first = msg['content']
        if first != "":
            r_msgs.append([first, sec])

            # r_msgs.append((msg['role'], msg['content']))
            # r_msgs.append([ msg['content'],msg['role']])
            # if msg['role'] == 'assistant':
            #     r_msgs.append(( 'From ' + msg['role'] +':\n\n' + msg['content'] + '\n',msg['role']))
            # else:
            #     r_msgs.append(( 'From ' + msg['role'] +':\n\n' + msg['content'] + '\n',None))
        
        # print(r_msgs)
        value = finder.getBranchCodeTag(self.curr_task.getName())
        # TODO: вывадить код ветки
        # print('BranchCode=', self.curr_task.findKeyParam(value))

        graph = self.drawGraph()

        return (
            r_msgs, 
            in_prompt ,
            graph, 
            out_prompt, 
            in_role, 
            chck, 
            self.curr_task.getName(), 
            self.curr_task.getAllParams(), 
            set_prompt, 
            gr.Dropdown.update(choices= self.getTaskList()),
            gr.Dropdown.update(choices=self.getByTaskNameParamListInternal(self.curr_task), 
                               interactive=True), 
            gr.Dropdown.update(choices=[t.getName() for t in self.curr_task.getAllParents()], 
                               value=self.curr_task.getName(), 
                               interactive=True), 
            gr.Radio(value="SubTask"), 
            r_msgs,
            self.getCurrentExtTaskOptions(),
            # TODO: Рисовать весь граф, но в упрощенном виде
            graph,
            self.getTreeNamesForRadio(),
            self.getCurrentTreeNameForTxt()
            )
    
    def getByTaskNameParamListInternal(self, task : BaseTask):
        out = []
        for p in task.params:
            if 'type' in p:
                if p['type'] == 'child' and 'name' in p:
                    out.append(p['type'] + '(' + p['name'] + ')')
                else:
                    out.append(p['type'])
        return out
    
    def getByTaskNameParamList(self, task_name):
        task = self.getTaskByName(task_name)
        return gr.Dropdown.update(choices=self.getByTaskNameParamListInternal(task), interactive=True)
    
    def getFinderKeyString(self,task_name, fk_type, param_name, key_name):
        value = finder.getKey(task_name, fk_type, param_name, key_name, self)
        pyperclip.copy(value)
        pyperclip.paste()

    def getPathToFolder(self):
        app = Tk()
        app.withdraw() 
        app.attributes('-topmost', True)
        filename = askdirectory() 
        pyperclip.copy(filename)
        pyperclip.paste()
        return filename
    
    def getPathToFile(self):
        app = Tk()
        app.withdraw() 
        app.attributes('-topmost', True)
        filename = askopenfilename() 
        pyperclip.copy(filename)
        pyperclip.paste()
        return filename
  
    def getShortName(self, n_type : str, n_name : str) -> str:
        tasks_dict  = cr.getTasksDict()
        for t in tasks_dict:
            if t['type']== n_type:
                return n_name.replace(n_type, t['short'])
        return n_name
   
    def getTaskKeys(self, param_name):
        return self.getNamedTaskKeys(self.curr_task, param_name)

    def getByTaskNameTasksKeys(self, task_name, param_name):
        task = self.getTaskByName(task_name)
        return self.getNamedTaskKeys(task, param_name)

    def getNamedTaskKeys(self, task : BaseTask, param_name : str):
        res, data = task.getParamStruct(param_name)
        a = []
        if res:
            task_man = TaskManager()
            a = task_man.getListBasedOptionsDict(data)
        print('Get named task keys', a)
        return gr.Dropdown(choices=a, interactive=True)
    
    def getTaskKeyValue(self, param_name, param_key):
        print('Get task key value:',param_name,'|', param_key)
        if param_key == 'path_to_read':
            app = Tk()
            app.withdraw() # we don't want a full GUI, so keep the root window from appearing
            app.attributes('-topmost', True)
            filename = askopenfilename() # show an "Open" dialog box and return the path to the selected file
            return (gr.Dropdown(choices=[filename], value=filename, interactive=True, multiselect=False),
                    gr.Textbox(str(filename)))
        elif param_name == 'script' and param_key == 'path_to_trgs':
            app = Tk()
            app.withdraw()  
            app.attributes('-topmost', True)
            filename_src = list(askopenfilenames() )
            res, data = self.curr_task.getParamStruct(param_name)
            # data['targets_type'] = 'args'
            filename = []
            print('Get filenames for args:', filename)
            for val in filename_src:
                filename.append( data['path_to_python'] + ' ' + val)
            return (gr.Dropdown(choices=filename, value=filename,multiselect=True, interactive=True),
                    gr.Textbox(str(filename)))

        elif param_key == 'path_to_write':
            app = Tk()
            app.withdraw() # we don't want a full GUI, so keep the root window from appearing
            app.attributes('-topmost', True)
            filename = askdirectory() # show an "Open" dialog box and return the path to the selected file
            return gr.Dropdown(choices=[filename], value=os.path.join(filename,'insert_name'), interactive=True), gr.Textbox(value=filename, interactive=True)
        elif param_key == 'model':
            res, data = self.curr_task.getParamStruct(param_name)
            if res:
                cur_val = data[param_key]
                path_to_config = os.path.join('config','models.json')
                values = []
                with open(path_to_config, 'r') as config:
                    models = json.load(config)
                    for _, vals in models.items():
                        values.extend([opt['name'] for opt in vals['prices']])
                return (gr.Dropdown(choices=values, value=cur_val, interactive=True, multiselect=False),
                         gr.Textbox(value=''))
           
        task_man = TaskManager()
        res, data = self.curr_task.getParamStruct(param_name)
        if res and param_key in data:
            cur_val = data[param_key]
            values = task_man.getOptionsBasedOptionsDict(param_name, param_key)
            print('Update with',cur_val,'from', values)
            if cur_val in values:
                return (gr.Dropdown(choices=values, value=cur_val, interactive=True, multiselect=False),
                         gr.Textbox(value=''))
        cur_val = 'None'
        return (gr.Dropdown(choices=[cur_val], value=cur_val, interactive=True, multiselect=False), 
                gr.Textbox(value=''))
    
    def setTaskKeyValue(self, param_name, key, slt_value, mnl_value):
        if mnl_value == "":
            info = TaskDescription(target=self.curr_task, params={'name':param_name,'key':key,'select':slt_value})
        else:
            info = TaskDescription(target=self.curr_task, params={'name':param_name,'key':key,'select':mnl_value})
        cmd = edit.EditParamCommand(info)
        self.cmd_list.append(cmd)
        return self.runIteration('')

    def getAppendableParam(self):
        task_man = TaskManager()
        return task_man.getParamOptBasedOptionsDict()

    def appendNewParamToTask(self, param_name):
        print('Append new param to task')
        task_man = TaskManager()
        param = task_man.getParamBasedOptionsDict(param_name)
        if param is not None:
            info = TaskDescription(target=self.curr_task, params=param)
            cmd = edit.AppendParamCommand(info)
            self.cmd_list.append(cmd)
        return self.runIteration('')

    def updateSteppedSelected(self):
        res, val = self.curr_task.getParamStruct('input')
        if res and val['input']:
            info = TaskDescription(prompt=self.curr_task.getLastMsgContent(),
                                prompt_tag=self.curr_task.getLastMsgRole(),
                                manual=True)
            self.updateSteppedSelectedInternal(info)
        else:
            self.updateSteppedSelectedInternal()
        return self.getCurrTaskPrompts()

    def processCommand(self, json_msg,  tasks_json):
        send_task_list_json = {}
        cmd = json_msg['options']
        if 'cur_task' in cmd:
            self.setCurrentTaskByName(cmd['cur_task'])

        if 'slt_task' in cmd:
            self.setSelectedTaskByName(cmd['slt_task'])
        self.makeTaskAction(cmd['prompt'], cmd['type'], cmd['action'], cmd['role'])

        tasks_json_new = self.getTaskJsonStr()

        task_list_old = tasks_json['tasks']
        # print("old=", len(task_list_old))
        task_list_new = tasks_json_new['tasks']
        # print("new=", len(task_list_new))
        send_task_list = []
        for one_task in task_list_new:
            # print("new=",one_task['name'])
            if one_task not in task_list_old:
                # print("New task:", one_task['name'],"\n", one_task['chat'][-1])
                send_task_list.append(one_task)
                # for sec_task in task_list_old:
                #     if sec_task['name'] == one_task['name']:
                #         print("Edited")

        delete_task_list = []
        for one_task in task_list_old:
            # print("old=",one_task['name'])
            found = False
            for sec_task in task_list_new:
                if sec_task['name'] == one_task['name']:
                    found = True
            if not found:
                delete_task_list.append(one_task['name'])    


        send_task_list_json = {'tasks': send_task_list}
        send_task_list_json['id'] = 'updt'
        send_task_list_json['to_delete'] = delete_task_list
        print("Send task=", send_task_list_json)
        return send_task_list_json
    def syncCommand(self, send_task_list):
        send_task_list_json = {'tasks': send_task_list['tasks']}
        send_task_list_json['id'] = 'init'
        return send_task_list_json
 
   
    def beforeRemove(self, remove_folder = False, remove_task = True):
        print('Clean files by manager')
        print('Tasks:', [t.getName() for t in self.task_list])
        if remove_task:
            for task in self.task_list:
                task.beforeRemove()
                self.task_list.remove(task)
                del task
        if remove_folder:
            # os.path.split(self.getPath())
            # Path.rmdir(self.getPath())
            shutil.rmtree(self.getPath())

    def createExtProject(self, filename, prompt, parent) -> bool:
        # TODO: Возможно, что следует просто отправлять сюда имя программы, которое потом будет использовать loadExtProject. Таким образом имя папок будет уникальным
        res, ext_pr_name = self.loadexttask(filename, self)
        if res:
            cur = self.curr_task
            self.createOrAddTask(prompt, 'ExtProject','user',parent,[{'type':'external','project':ext_pr_name,'filename':filename}])
            if cur != self.curr_task and cur is not None:
                print('Successfully add external task')
                print('List of tasks:',[n.getName() for n in self.task_list])
                return True
        return False

    def copyChildChainTask(self, change_prompt = False, edited_prompt = '',
                           trg_type_t = '', src_type_t = '', 
                           forced_parent = False
                           ):
        print('Copy child chain tasks')
        tasks_chains = self.curr_task.getChildChainList()

        return self.copyTasksChain(tasks_chains, change_prompt, edited_prompt, trg_type_t, src_type_t, forced_parent)
    
    def copyTasksChain(self, tasks_chains, change_prompt = False, 
                       edited_prompt = '',trg_type_t = '', src_type_t = '', 
                       forced_parent = False):
        print('Task chains:')
        i = 0
        for branch in tasks_chains:
            print(i,[task.getName() for task in branch['branch']], branch['done'], branch['idx'],  branch['parent'].getName() if branch['parent'] else "None", branch['i_par'])
            i+= 1
        parent = None

        link_array = []
        start = None

        for i in range(len(tasks_chains)):
            branch = tasks_chains[i]
            for j in range(len(branch['branch'])):
                task = branch['branch'][j]
                prompt=task.getLastMsgContent() 
                prompt_tag=task.getLastMsgRole()
                trg_type = task.getType()
                if j == 0:
                    if i != 0:
                        parent = tasks_chains[branch['i_par']]['created'][-1]
                    branch['created'] = []
                    if i == 0:
                        # Если есть промпт для замены вставляем его
                        if forced_parent:
                            parent = self.curr_task.parent
                        if change_prompt:
                            prompt = edited_prompt
                        # if len(trg_type) > 0:
                            # trg_type = trg_type
                else:
                    parent = self.curr_task
                print('branch',i,'task',j,'par',parent.getName() if parent else "No parent")
                # Меняем тип задачи
                if trg_type == src_type_t:
                    trg_type = trg_type_t
                if trg_type == 'ExtProject':
                    res, param = task.getParamStruct('external')
                    if res:
                        prompt = param['prompt']
                        filename = param['filename']
                        if not self.createExtProject(filename, prompt, parent):
                            print('Can not create')
                            return self.getCurrTaskPrompts()
                    else:
                        print('No options')
                        return self.getCurrTaskPrompts()
                else:
                    self.createOrAddTask(prompt, trg_type, prompt_tag, parent, [])

                if i == 0 and j == 0:
                    start = self.curr_task
                if len(task.getHoldGarlands()) or len(task.getGarlandPart()):
                    link_array.append({'task':self.curr_task,
                                   'holders': task.getHoldGarlands(), 
                                   'garlandparts': task.getGarlandPart()})

                        
                branch['created'].append(self.curr_task)
        return link_array, start

    def copyTaskByInfoInternal(self):
        if self.tc_stop:
            return False
        i, j = self.tc_ij_list[self.tc_ij_list_idx]
        change_prompt = self.tc_change_prompt
        edited_prompt = self.tc_edited_prompt

        tasks_chains = self.tc_tasks_chains
        branch = tasks_chains[i]
        task = branch['branch'][j]
        # TODO: Заменить на особую функцию, которая используется только в случае копирования, чтобы переопределить ее для ExtProject. Для этой задачи при копировании важнее не входные переменные, а результирующее сообщение
        prompt=task.getLastMsgContent() 
        prompt_tag=task.getLastMsgRole()
        trg_type = task.getType()
        if j == 0:
            if branch['i_par'] is not None:
                parent = tasks_chains[branch['i_par']]['created'][-1]
            else:
                parent = branch['parent']
                if change_prompt:
                    prompt = edited_prompt
            branch['created'] = []
            branch['convert'] = []
        else:
            parent = self.curr_task
        print('branch',i,'task',j,'par',parent.getName() if parent else "No parent")
        # Меняем тип задачи
        for switch in self.tc_switch_type:
            if trg_type == switch['src']:
                trg_type = switch['trg']
        if trg_type == 'ExtProject':
            res, param = task.getParamStruct('external')
            if res:
                prompt = param['prompt']
                filename = param['filename']
                if not self.createExtProject(filename, prompt, parent):
                    print('Can not create')
                    # return self.getCurrTaskPrompts()
                    return False
            else:
                print('No options')
                # return self.getCurrTaskPrompts()
                return False
        else:
            self.createOrAddTask(prompt, trg_type, prompt_tag, parent, [])


        # for link in branch['links']:
            # if link['out'] == task:
                # link['res'] == self.curr_task 
        branch['created'].append(self.curr_task)
        branch['convert'].append({'from': task, 'to': self.curr_task})

        self.tc_ij_list_idx +=1
        if self.tc_ij_list_idx < len(self.tc_ij_list):
            return True
        else:
            self.tc_stop = True
            return False


# TODO: при копировании учитывать только ветви с Response, чтобы не плодить ненужные копии
    def getTasksChainsFromCurrTask(self, param):
        tasks_chains = self.curr_task.getTasksFullLinks(param)
        if 'chckresp' not in param:
            return  tasks_chains
        elif 'chckresp' in param and not param['chckresp']:
            return  tasks_chains
        buds = self.getSceletonBranchBuds(self.curr_task)

        # учитываем линковку задач
        tree = self.curr_task.getTree()
        trees = [tree.copy()]
        idx = 0
        while(idx < 1000):
            linked_tasks = []
            for task in tree:
                linked_tasks.extend( task.getHoldGarlands())
            tree = []
            if len(linked_tasks) == 0:
                break
            for task in linked_tasks:
                tree.extend( task.getTree())
                trees.append(task.getTree())
            idx +=1

        accepted = []
        for bud in buds:
            partasks = bud.getAllParents()
            right = False
            for task in partasks:
                if task.getType() == 'Response':
                    right = True
                    break
            if right:
                accepted.extend(partasks)
        print('Accepted:',[t.getName() for t in accepted])
        res_tasks_chains = []
        i = 0
        for branch in tasks_chains:
            print(i,
                  [task.getName() for task in branch['branch']], 
                  branch['done'], branch['idx'],  
                  branch['parent'].getName() if branch['parent'] else "None", 
                  branch['i_par'])


            remove = False
            for task in branch['branch']:
                if task not in accepted:
                    remove = True
            if not remove:
                print('Accept branch')
                res_tasks_chains.append(branch)
            else:
                print('Deny branch')
            i += 1
        return res_tasks_chains


    def copyTasksByInfo(self, tasks_chains, change_prompt = False, edited_prompt = '', switch = []):
        print('Copy tasks by info')
        self.copyTasksByInfoStart(tasks_chains, change_prompt, edited_prompt, switch)
        self.copyTasksByInfoExe()
        return self.copyTasksByInfoStop()

    def copyTasksByInfoStart(self, tasks_chains, change_prompt = False, edited_prompt = '',switch = []):
        # TODO: замораживать текущую задачу, чтобы оставить возможность дополнительного редактирования
        i = 0
        links_chain = []
        insert_tasks = []
        for branch in tasks_chains:
            print(i,
                  [task.getName() for task in branch['branch']], 
                  branch['done'], branch['idx'],  
                  branch['parent'].getName() if branch['parent'] else "None", 
                  branch['i_par'])

            for link in branch['links']:
                found = False
                for sv in links_chain:
                    if (sv['dir'] == 'in' or sv['dir'] == 'out') and (
                        sv['in'] == link['in'] 
                        and sv['out'] == link['out']):
                        found = True
                if 'insert' in link:
                    insert_tasks.append(link)
                if not found:
                    links_chain.append(link)
            i+= 1

        self.tc_tasks_chains = tasks_chains
        self.tc_links_chain = links_chain
        self.tc_insert_tasks = insert_tasks
        self.tc_ij_list = []
        self.tc_ij_list_idx = 0
        self.tc_change_prompt = change_prompt
        self.tc_edited_prompt = edited_prompt
        
        self.tc_switch_type = switch

        self.tc_start = True
        self.tc_stop = False

        for i in range(len(tasks_chains)):
            for j in range(len(tasks_chains[i]['branch'])):
                self.tc_ij_list.append([i,j])
                
    def copyTasksByInfoExe(self):
        while self.copyTaskByInfoInternal():
            pass

    def copyTasksByInfoStep(self):
        if self.tc_start:
            if self.tc_stop:
                self.copyTasksByInfoStop()
            else:
                self.copyTaskByInfoInternal()

    def copyTasksByInfoStop(self):
        for branch in self.tc_tasks_chains:
            print('branch convert results:')
            print([[t['from'].getName(),t['to'].getName()] for t in branch['convert']])
        print('Links list:')
        print([[link['out'].getName(),link['in'].getName()] for link in self.tc_links_chain])

        #TODO: протестировать вставку 
        for link in self.tc_links_chain:
            outtask = self.getCopyedTask(self.tc_tasks_chains, link['out'])
            if 'insert' in link and 'prompt' in link:
                self.curr_task = link['in']
                self.makeTaskActionPro(prompt=link['prompt'],type=link['type'], creation_type='Insert', creation_tag=link['tag'])
                intask = self.slct_task
            else:
                intask = self.getCopyedTask(self.tc_tasks_chains,link['in'])
            
            self.makeLink( intask, outtask )

        self.tc_start = False
        self.tc_stop = False
        return self.tc_tasks_chains

    def getCopyedTask(self, tasks_chans, task):
        for branch in tasks_chans:
            for info in branch['convert']:
                if info['from'] == task:
                    return info['to']
        return task


    # копирует цепочку задач с использованием правил
    # change_prompt = False, -- изменяет текстовое содержание родительской задачи цепи
    # edited_prompt = '', -- текст, на который производится изменение
    # trg_type = '', -- тип, на который меняется
    # apply_link = False,  -- копировать также свзяи
    # remove_old_link = False, -- удалять связи со старых задач
    # copy -- копировать связи
    # subtask -- создать ветвление от родительской задачи
    def copyChildChains(self, change_prompt = False, edited_prompt = '',
                        trg_type = '', src_type = '', 
                        apply_link = False, remove_old_link = False, 
                        copy = False, subtask = False):
        print(10*"----------")
        print('Copy child chains')
        print(10*"----------")
        link_array, start_node = self.copyChildChainTask(
                                                        change_prompt=change_prompt, 
                                                        edited_prompt= edited_prompt, 
                                                        trg_type_t= trg_type, 
                                                        src_type_t=src_type, 
                                                        forced_parent=subtask
                                                        )
        print(link_array)
        idx = 0
        while(idx < 1000):
            link_array_new = []
            for link in link_array:
                task = link['task']
                holders = link['holders']
                garlandparts = link['garlandparts']
                print(task.getName())
                print('holders', [t.getName() for t in holders])
                print('garlandparts', [t.getName() for t in garlandparts])
                if apply_link:                
                    for holder in holders:
                        if remove_old_link:
                            self.curr_task = holder
                            self.makeTaskActionBase("","","Unlink","")
                            holder.removeLinkToTask()
                            # self.manager.makeLink( task, holder)
                        if copy:
                            print('================================================Copy')
                            self.curr_task = holder
                            new_la, new_sn = self.copyChildChainTask(change_prompt=False, edited_prompt=task.getLastMsgContent(), forced_parent=True)
                            # print(holder)
                            # print(new_sn)
                            for l in new_la:
                                if new_sn == l['task']:
                                    new_la.remove(l)
                            link_array_new.extend( new_la )
                            # print(link_array_new)
                            self.makeLink( new_sn, task )

                    for part in garlandparts:
                        self.makeLink( task, part )
                        
            if len(link_array_new) == 0:
                break
            link_array = link_array_new
            idx += 1

        return self.getCurrTaskPrompts()
 

    def saveInfo(self):

        path_to_projectfile = os.path.join(self.getPath(),'project.json')
        if not self.info: 
            loaded = False
            # print('Try to load', path_to_projectfile)
            if os.path.exists(path_to_projectfile):
                try:
                    with open(path_to_projectfile,'r') as f:
                        self.info = json.load(f)
                        loaded = True
                except:
                    pass
            if not loaded:
                self.info = {'actions':[]}

        writer.writeJsonToFile(path_to_projectfile, self.info, 'w',1)

    def addActions(self, action = '', prompt = '', tag = '', act_type = '', param = {}):
        if self.info is None:
            self.saveInfo()
        id = len(self.info['actions'])
        action = {'id': id,'action':action,'prompt':prompt,'tag':tag,'type':act_type, 'param': param }

        action['current'] = self.curr_task.getName() if self.curr_task else None
        action['slct'] = self.slct_task.getName() if self.slct_task else None
        action['selected'] = [t.getName() for t in self.selected_tasks]


        self.info['actions'].append(action)
        self.saveInfo()

    def remLastActions(self):
        if len(self.info['actions']) > 0:
            cmd = self.info['actions'].pop()
            print('Remove last cmd:', cmd)
            self.saveInfo()

    def initInfo(self, method, task : BaseTask = None, path = 'saved', act_list = [], repeat = 3, limits = 1000):
        # print('Manager init info')
        self.loadexttask = method
        # TODO: А зачем мне вообще все задачи, а не только родительская?
        # self.task_list =  task.getAllParents() if task is not None else []
        self.curr_task = task
        task_name = task.getName() if task is not None else 'Base'
        self.setName(task_name)
        if task is not None:
            self.setPath(os.path.join(path,'tmp', self.getName()))
        else:
            self.setPath(path)
        self.saveInfo()
        if 'task' not in self.info:
            self.info['task'] = task_name
        if 'script' not in self.info:
            self.info['script'] = {'managers':[]}
        if 'repeat' not in self.info:
            self.info['repeat'] = repeat
        if task is not None and len(act_list) > 0:
            self.info['actions'] = act_list
            self.info['limits'] = limits
        self.info['done'] = False
        self.info['idx'] = 0
        # Начальные данные для вызова скриптов, если их нет
        if 'state' not in self.info:
            self.info['ext_states'] = ['init_created']
        if 'type' not in self.info:
            self.info['type'] = 'simple'

        self.saveInfo()
        # print(self.info)


