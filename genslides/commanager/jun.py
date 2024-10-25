from genslides.task.base import TaskDescription
from genslides.task.base import TaskManager
from genslides.task.base import BaseTask

from genslides.utils.reqhelper import RequestHelper
from genslides.utils.request import Requester
from genslides.utils.searcher import WebSearcher
from genslides.utils.largetext import Summator

from genslides.utils.savedata import SaveData, getTimeForSaving

import genslides.task.creator as cr
import genslides.commands.edit as edit
import genslides.commands.create as create
import genslides.commands.parent as parcmd
import genslides.commands.link as lnkcmd

from genslides.utils.largetext import SimpleChatGPT
import genslides.utils.writer as writer
import genslides.utils.loader as Loader
import genslides.utils.searcher as Sr
import genslides.utils.readfileman as Reader
import genslides.utils.filemanager as FileMan

import os

import json

import graphviz

import pprint

import pyperclip
import shutil

import re

from tkinter import Tk     # from tkinter import Tk for Python 3.x
from tkinter.filedialog import askopenfilename, askdirectory, askopenfilenames

import datetime

import pathlib

import genslides.task_tools.actions as Act
import genslides.commanager.man as Man

class Manager(Man.Jun):
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

        self.no_output = False

    def enableOutput2(self):
        self.no_output = False

    def disableOutput2(self):
        self.no_output = True

   
    def getColor(self) -> str:
        if self.info and 'color' in self.info:
            return self.info['color']
        return '#7ed38c'

# TODO: сменить место хранения параметров менеджера
    def setParam(self, param_name, param_value):
        if param_name in self.params:
            # print("Set ",param_name," to ",param_value)
            self.params[param_name] = param_value
            with open(self.path_to_file, 'w') as f:
                json.dump(self.params,f,indent=1)
        else:
            print("Can\'t set param")

    def getParam(self, param_name):
        if param_name in self.params:
            return self.params[param_name]
        return None
    
    # def getParamGradioInput(self, param_name):
    #     out = self.getParam(param_name + " lst")
    #     if not out:
    #         out = []
    #     return gr.Dropdown( choices= out, interactive=True)

    
    def getParamsLst(self):
        out = []
        for param in self.params:
            if not param.endswith(" lst"):
                out.append(param)
        return out

   
    def createCollectTreeOnSelectedTasks(self, action_type):
        return self.createTreeOnSelectedTasks(action_type,"Collect")

    def createTreeOnSelectedTasks(self, action_type : str, task_type : str):
        print(action_type,' on ', task_type, 'cur task', self.curr_task.getName(),'with selected', self.getSelectedTask().getName())
        first = True
        trg = self.curr_task
        task_list = self.selected_tasks.copy()
        for task in task_list:
            self.curr_task = trg
            role = task.getLastMsgRole()
            self.makeTaskAction("",task_type, action_type, role,[])
            # if first:
            #     parent = None
            #     if action_type == 'SubTask':
            #         parent = self.curr_task
            #     self.createOrAddTask("",task_type,"user",parent,[])
            #     first = False
            # else:
            #     parent = self.curr_task
            #     self.createOrAddTask("",task_type,"user",parent,[])
            if action_type == 'Insert':
                self.makeLink(self.curr_task.parent, task)
            else:
                self.makeLink(self.curr_task, task)
        self.clearSelectList()
    
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

    def loadTasksList(self, safe = False, trg_files = []):
        if self.is_loaded:
            return
        # print(10*"=======")
        print('Fast load of tasks' if safe else 'Load task from files')
        print('Manager path=', self.getPath())
        task_manager = TaskManager()
        links = task_manager.getLinks(Loader.Loader.getUniPath(self.getPath()), trg_files=trg_files)
        self.createTask(prnt_task=None, safe=safe, trg_tasks=trg_files)
            

        # print('Links', links)

        for link in links:
            trgs = link['linked']
            affect_task = self.getTaskByName(link['name'])
            for trg in trgs:
                influense_task = self.getTaskByName(trg)
                self.makeLink(affect_task, influense_task)

        for task in self.task_list:
                task.completeTask()

        self.is_loaded = True

        # for task in self.task_list:
        #     print("Task name=", task.getName(), " affected")
        #     for info in task.by_ext_affected_list:
        #         print("by ",info.parent.getName())
        #     print("influence")
        #     for info in task.affect_to_ext_list:
        #         print("to ",info.parent.getName())

   
   
    def setBranchEndName(self, summary):
        leave = self.endes[self.endes_idx]
        param = {'type':'bud','text': summary,'branch':leave.getBranchCodeTag()}
        leave.setParamStruct(param)
 

    
   
    def getCopyTasks(self, start_task : BaseTask) ->list[BaseTask]:
        fork, fork_root = self.getBranchUpFork(start_task)
        select_branches = [start_task]
        if fork != None:
            print('Fork is',fork.getName())
            for child in fork.getChilds():
                if child != fork_root:
                    child_branch = child.getAllChildChains()
                    branch_found = False
                    task_found = None
                    for idx, task in enumerate(child_branch):
                        # print('Check in', task.getName())
                        pres, pparam = task.getParamStruct('copied', True)
                        if pres:
                            names = pparam['cp_path']
                            if start_task.getName() in names:
                                    task_found = task
                                    branch_found = True
                                    break
                    if branch_found:
                        select_branches.extend([task_found])
        return select_branches


    def getCopyBranch(self, start_task: BaseTask) ->list[BaseTask]:
        fork, fork_root = self.getBranchUpFork(start_task)
        src_branch = fork_root.getAllChildChains()
        select_branches = src_branch.copy()
        if fork != None:
            print('Fork is',fork.getName())
            for child in fork.getChilds():
                if child != fork_root:
                    child_branch = child.getAllChildChains()
                    branch_found = False
                    for idx, task in enumerate(child_branch):
                        # print('Check in', task.getName())
                        pres, pparam = task.getParamStruct('copied', True)
                        task_found = False
                        if pres:
                            names = pparam['cp_path']
                            for s_task in src_branch:
                                if s_task.getName() in names:
                                    task_found = True
                                    break
                        if task_found:
                            branch_found = True
                    if branch_found:
                        select_branches.extend(child_branch)
        return select_branches



    def updateEditToCopyBranch(self, start_task : BaseTask):
        fork, fork_root = self.getBranchUpFork(start_task)
        src_tasks = start_task.getAllChildChains()

        if fork != None:
            print('Fork for branches is',fork.getName())
            for child in fork.getChilds():
                if child != fork_root:
                    trg_tasks = child.getAllChildChains()
                    for task in trg_tasks:
                        # print('Check in', task.getName())
                        pres, pparam = task.getParamStruct('copied', True)
                        if pres:
                            names = pparam['cp_path']
                            found = False
                            for name in names:
                                for s_task in src_tasks:
                                    if name in s_task.getName():
                                        print('Find in',names,'target',s_task.getName())
                                        task.update(TaskDescription( prompt=s_task.getLastMsgContent(), 
                                                  prompt_tag=s_task.getLastMsgRole()
                                                  ))
                                        found = True
                                if found:
                                    break


    def getTextFromFile(self, text, filenames):
        if filenames is None:
            return text
        print("files=",filenames.name)
        with open(filenames.name) as f:
            text += f.read()
        return text
    
    def addRenamedPair(self, stdtaskname : str, chgtaskname : str):
        self.renamed_parent.append(
            {
                'std': stdtaskname,
                'chg': chgtaskname
            }
        )

    def clearRaenamedList(self):
        self.renamed_parent.clear()
    
    def checkParentName(self, task_info, parent :BaseTask) -> bool:
        # if len(self.renamed_parent) and 'parent' in task_info:
            # print(f"""Check {parent.getName()} with {task_info['parent']} using {self.renamed_parent}""")
        for pair in self.renamed_parent:
            if pair['chg'] == parent.getName():
                return 'parent' in task_info and task_info['parent'] == pair['std']
        return 'parent' in task_info and task_info['parent'] == parent.getName()
    
    def getParentSavingName(self, task : BaseTask):
        for pair in self.renamed_parent:
            if pair['chg'] == task.getName():
                return pair['std'].replace(self.getProjPrefix(), "")
        return task.getName().replace(self.getProjPrefix(), "")

    def createTaskByFile(self, parent :BaseTask = None, files = []):
        if len(files) == 0:
            path = Loader.Loader.getUniPath(self.getPath())
            files = FileMan.getFilesPathInFolder(path)
        # if parent != None:
        #     print('Create task by parent',parent.getName())
        starttasklist = self.task_list.copy()
        linklist = []
        for file in files:
            task_info = Reader.ReadFileMan.readJson(Loader.Loader.getUniPath(file))
            prompt = ''
            role = 'user'
            self.curr_task = parent
            if parent == None and 'parent' in task_info and task_info['parent'] == '':
                if 'chat' in task_info and len(task_info['chat']) > 0:
                    prompt = task_info['chat'][-1]['content']
                    role = task_info['chat'][-1]['role']
                for link in task_info['linked']:
                    linklist.append({'in':FileMan.getFileName(file),'out':link})
                # self.makeTaskAction(prompt, task_info['type'], "New", role)
                self.createOrAddTask(prompt=prompt, type=FileMan.getFileName(file), tag=role,parent=None)
            elif parent and self.checkParentName(task_info, parent):
                # print('Create using path=', file)
                if 'chat' in task_info and len(task_info['chat']) > 0:
                    prompt = task_info['chat'][-1]['content']
                    role = task_info['chat'][-1]['role']
                for link in task_info['linked']:
                    linklist.append({'in':FileMan.getFileName(file),'out':link})
                self.createOrAddTask(prompt=prompt, type=FileMan.getFileName(file), tag=role,parent=parent)
        addtasklist = []
        for task in self.task_list:
            if task not in starttasklist:
                addtasklist.append(task)
        # print('Add task list',[t.getName() for t in addtasklist])
        return addtasklist, linklist
    
    def applyLinks(self,linklist):
        for link in linklist:
            self.makeLink(self.getTaskByName(link['in']),self.getTaskByName(link['out']))

    def loadTasksListFileBased(self, files = []):
        if self.is_loaded:
            return
        print('Loading of tasks list based on file: manager', self.getName(),'with path',self.getPath())
        idx = 0
        start_tasks = self.task_list.copy()
        task_links = []
        print(f"Start task list:{[t.getName() for t in start_tasks]}")
        while idx < 1000:
            n_start_tasks = []
            # print('[',idx,']Start tasks list',[t.getName() for t in start_tasks])
            if idx == 0:
                for task in start_tasks: #Если некоторые задачи уже загружены
                    # print('Create task for', task.getName())
                    n_start_tasks2, n_task_list2 = self.createTaskByFile(task, files)
                    n_start_tasks.extend(n_start_tasks2)
                    task_links.extend(n_task_list2)
                n_start_tasks2, n_task_list2 = self.createTaskByFile(files = files)
                n_start_tasks.extend(n_start_tasks2)
                task_links.extend(n_task_list2)
                task_links.extend(n_task_list2)
            else:
                for task in start_tasks:
                    # print('Create task for', task.getName())
                    n_start_tasks2, n_task_list2 = self.createTaskByFile(task, files)
                    n_start_tasks.extend(n_start_tasks2)
                    task_links.extend(n_task_list2)
            if len(n_start_tasks) == 0:
                break
            start_tasks = n_start_tasks
            idx +=1
        # print('Loadinf done in',idx,'steps')
        self.applyLinks(task_links)
        self.is_loaded = True
        print(f'Loading is done:{len(self.task_list)} task(s)')



    def createTask(self, prnt_task = None, safe = False, trg_tasks = []):
        # print(10*"=======")
        # dt1 = datetime.datetime.now()        
        if prnt_task == None:
            parent_path = ""
        else:
            parent_path = prnt_task.path
            self.curr_task = prnt_task
            # print("task=", self.curr_task.path)
            # print("Parent task path=", parent_path)
        init_task_list = self.task_list.copy()
        task_manager = TaskManager()
        # parent_prompt_list = task_manager.getTaskPrompts(self.getPath(), trg_path= parent_path, ignore_safe=safe, trg_tasks=trg_tasks)
        parent_prompt_list = task_manager.getTaskPromptsFromCache(self.getPath(), trg_path= parent_path, ignore_safe=safe, trg_tasks=trg_tasks)

        # print("prompt count=",len(parent_prompt_list))
        # dt2 = datetime.datetime.now()    

        for prompt in parent_prompt_list:
            self.curr_task = prnt_task
            # print("content=",prompt['content'])
            if parent_path == "":
                self.makeTaskAction(prompt['content'], prompt['type'], "New", prompt['role'], trgtaskname=prompt['trgtaskname'])
            else:
                self.makeTaskAction(prompt['content'], prompt['type'], "SubTask",prompt['role'], trgtaskname=prompt['trgtaskname'])

        trg_task_list = self.task_list.copy()
        
        # dt3 = datetime.datetime.now()    

        # print(self.curr_task.getName(),'was created by:\t',(dt2-dt1).microseconds/1000,'ms |',(dt3-dt2).microseconds/1000,'ms')    

        # print("task count=",len(self.task_list),",exclude=",len(init_task_list))
        if len(parent_prompt_list):
            for task in trg_task_list:
                if task not in init_task_list:
                    # print("+++",parent_path)
                    self.createTask(task, safe=safe, trg_tasks=trg_tasks)
        

    def setNextTask(self, input):
        saver = SaveData()

        try:
            inc = int(input)
        except ValueError:
            print("Value error")
        #Try float.
            # ret = float(s)
            return 
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


    def drawGraph(self, only_current= True, max_index = -1, path = "output/img", hide_tasks = True, add_multiselect = False, max_childs = 3, add_linked=False, all_tree_task = False):
        # print('Draw graph')
        if only_current:
            if self.curr_task == None:
                if len(self.task_list) > 0:
                    self.curr_task = self.task_list[0] 
            if self.curr_task.isRootParent() or all_tree_task:
                trg_list = self.curr_task.getTree(max_childs=10)
            else:
                trg_list = self.curr_task.getAllParents(max_index = max_index)
                for task in self.curr_task.getAllChildChains(max_index=max_index, max_childs=max_childs):
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
                    for t in self.multiselect_tasks:
                        if t not in trg_list:
                            trg_list.append(t)
        else:
            trg_list = self.task_list
        # print('Target tasks:',[t.getName() for t in trg_list])
        if len(trg_list) > 0:
            f = graphviz.Digraph(comment='The Test Table',
                                  graph_attr={'size':"7.75,10.25",'ratio':'fill'})
            
            # Скрываем задачи не этого менеджера
            if hide_tasks:
                # print('Hide tasks')
                rm_tasks = []
                for task in trg_list:
                    if task not in self.task_list:
                        rm_tasks.append(task)
                # print('Task to hide:',[t.getName() for t in rm_tasks])
                for task in rm_tasks:
                    trg_list.remove(task)

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
                elif task.readyToGenerate():
                    color = 'darkmagenta'
                    shape = "ellipse" #rectangle,hexagon
                    f.node( task.getIdStr(), task.getName(),style="filled", color = color, shape = shape)
                elif task in self.multiselect_tasks:
                    color = "lightsalmon3"
                    shape = "ellipse" #rectangle,hexagon
                    if task == self.curr_task:
                        color = "gold"
                    if len(task.getHoldGarlands()) > 0:
                        color = 'crimson'
                    if task.checkType('Response'):
                        shape = 'hexagon'
                    f.node( task.getIdStr(), task.getName(),style="filled", color = color, shape = shape)
                elif task == self.curr_task:
                    color = "skyblue"
                    shape = "ellipse" #rectangle,hexagon
                    if len(task.getHoldGarlands()) > 0:
                        color = 'skyblue4'
                    f.node( task.getIdStr(), task.getName(),style="filled", shape = shape, color = color)
                else:
                    color = 'ghostwhite'
                    shape = "ellipse" #rectangle,hexagon
                    if self.getTaskParamRes(task, "block"):
                        color="gold2"
                    elif self.getTaskParamRes(task, "input"):
                        color="aquamarine"
                    elif self.getTaskParamRes(task, "output"):
                        color="darkgoldenrod1"
                    elif self.getTaskParamRes(task, "check"):
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
                    if task.checkType('Response'):
                        shape = 'hexagon'
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
        return ["MoveUp","RemoveBranch", "RemoveTree","RemoveTaskList","Insert","Remove","ReqResp","Divide"]
    
    def makeRequestAction(self, prompt, selected_action, selected_tag):
        print('Make',selected_action,'Request')
        if selected_action == "New" or selected_action == "SubTask":
            return self.makeTaskAction(prompt, "Request", selected_action, "user")
        if selected_action == "Edit":
            return self.makeTaskAction(prompt, "Request", selected_action, selected_tag)
        
       
        
    def makeResponseAction(self, selected_action):
        return self.makeTaskAction("", "Response",selected_action, "assistant")
        
 
    def makeTaskAction(self, prompt, type, creation_type, creation_tag, params = [], trgtaskname = ''):
        if creation_type in self.getMainCommandList() or creation_type in self.vars_param:
            return self.makeTaskActionBase(prompt, type, creation_type, creation_tag, params, trgtaskname=trgtaskname)
        elif creation_type in self.getSecdCommandList():
            return self.makeTaskActionPro(prompt, type, creation_type, creation_tag, params)
        saver = SaveData()
    
 
    def makeTaskActionPro(self, prompt, type, creation_type, creation_tag, params = []):
        if creation_type == "RemoveBranch":
            tasks = self.curr_task.getChainBeforeBranching()
            trg = None
            if len(tasks) > 0:
                trg = tasks[0].getParent()
            for task in tasks:
                self.curr_task = task
                self.makeTaskActionBase(prompt, type, "Delete", creation_tag, params)
            if trg is not None:
                self.curr_task = trg
        elif creation_type == "RemoveTaskList":
            self.removeTaskList(self.multiselect_tasks)
            if self.curr_task == None:
                self.curr_task = self.task_list[0]
        elif creation_type == "RemoveTree":
            tasks = self.curr_task.getTree()
            for task in tasks:
                self.curr_task = task
                self.makeTaskActionBase(prompt, type, "Delete", creation_tag, params)
        elif creation_type == "Insert":
            task1 = self.curr_task.parent
            task2 = self.curr_task
            if task1:
                # self.makeTaskActionBase(prompt, type, "RemoveParent", creation_tag)
                self.curr_task = task1
                self.makeTaskActionBase(prompt, type, "SubTask", creation_tag, params)
            else:
                self.makeTaskActionBase(prompt, type, "New", creation_tag, params)
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
            else:
                task_12.addChild(task2)
                task2.saveAllParams()
                task_12.saveAllParams()
            # self.makeTaskActionBase(prompt, type, "Parent", creation_tag)
            try:
            # if task1 is not None:
                print('Parents\nFirst', task1.parent.getName() if task1.parent is not None else 'None','=',task1.getName())
                # print('Childs')
                # for ch in task1.getChilds():
                #     print(ch.getName())
            
                # print(task1.queue)
            # if self.slct_task is not None:
                print('Middle', self.slct_task.parent.getName() if self.slct_task.parent is not None else 'None','=',self.slct_task.getName())
                # print('Childs')
                # for ch in self.slct_task.getChilds():
                #     print(ch.getName())
                # print(self.slct_task.queue)
                print('Last', self.curr_task.parent.getName() if self.curr_task.parent is not None else 'None','=', self.curr_task.getName())
                # print('Childs')
                # for ch in self.curr_task.getChilds():
                #     print(ch.getName())
            except Exception as e:
                print('Error', creation_type,':', e)
            # print(self.curr_task.queue)
            # if task1 is not None:
            #     task1.update()
            # else:
            #     self.slct_task.update()
            # self.curr_task = self.slct_task
            self.curr_task = task2
            print('Selected',self.slct_task.getName())
            print('Current', self.curr_task.getName())

        elif creation_type == "Remove":
            task2 = self.curr_task
            self.curr_task.extractTask()
            self.curr_task = task2
            self.makeTaskActionBase(prompt, type, "Delete", creation_tag, params)
           
        elif creation_type == "ReqResp":
            if self.curr_task is not None:
                self.makeTaskActionBase(prompt,"Request","SubTask","user", params)
            else:
                self.makeTaskActionBase(prompt,"Request","New","user", params)
            self.makeTaskActionBase(prompt,"Response","SubTask","assistant", params)
        elif creation_type == "MoveUp":
            return self.moveCurrentTaskUP()
        elif creation_type == "Divide":
            text = self.curr_task.getLastMsgContent()
            tag = self.curr_task.getLastMsgRole()
            prs = text.split('[[---]]')
            if len(prs) < 2:
                return 
            else:
                last = prs.pop()
                for text in prs:
                    self.makeTaskActionBase(text, "Request", "Insert", tag, params)
                return self.makeTaskActionBase(last, "Request", "Edit", tag, params)

    def updateTaskParam(self, param):
        self.curr_task.setParam(param)
    
    def makeTaskActionBase(self, prompt, type, creation_type, creation_tag, params = [], trgtaskname = ''):
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
            return 
        if creation_type == "Edit":
            info = TaskDescription(prompt=prompt,prompt_tag=creation_tag)
            info.target = self.curr_task
            cmd = edit.EditCommand(info)
            self.cmd_list.append(cmd)
            return self.runIteration()
        elif creation_type == "EditAndStep":
            info = TaskDescription(prompt=prompt,prompt_tag=creation_tag, manual=True, stepped=True)
            self.updateSteppedSelectedInternal(info)
            return 
        elif creation_type == "EditAndStepTree":
            info = TaskDescription(prompt=prompt,prompt_tag=creation_tag, manual=True, stepped=True)
            self.updateSteppedTree(info)
            return 
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
            return 
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
            task = self.curr_task
            next_task_after = task.getParent()
            if next_task_after is None:
                for ch in task.getChilds():
                    next_task_after = ch
                    break
            info = TaskDescription(target=self.curr_task)
            cmd_delete = create.RemoveCommand(info)
            self.cmd_list.append(cmd_delete)
            self.runIteration(prompt)
            if task in self.tree_arr:
                self.tree_arr.remove(task)
            if next_task_after is None:
                self.setNextTask("1")
            else:
                self.curr_task = next_task_after
            del task
            return 
        elif creation_type == "New":
            parent = None
            if cr.checkTypeFromName(type, "Response"):
                print('Can\'t create new Response')
                return 
        elif creation_type == "SubTask":
            if cr.checkTypeFromName(type, "ExternalInput"):
                parent = None
            else:
                parent = self.curr_task
        else:
            return 
        
        return self.createOrAddTask(prompt,type, creation_tag, parent, params, trgtaskname)
        
    def createOrAddTask(self, prompt, type, tag, parent, params = [], trgtaskname = ''):
        # print('Create task')
        # print('Params=',params)
        res, task_params = self.helper.getParams(type)
        if res:
            task_params = self.updateTaskParams(params, task_params)
        else:
            task_params = params
        info = TaskDescription(prompt=prompt, prompt_tag=tag, 
                                                             helper=self.helper, requester=self.requester, manager=self, 
                                                             parent=parent, params=task_params, trgtaskname=trgtaskname)
        # if params is not None:
            # info.params = params
        curr_cmd = cr.createTaskByType(type, info)

        # if not curr_cmd:
            # return self.getCurrTaskPrompts()
        self.cmd_list.append(curr_cmd)
        return self.runIteration(prompt)

    
    def makeLink(self, task_in : BaseTask, task_out :BaseTask):
        if task_in != None and task_out != None:
            if (
                task_out.isReceiver() and task_in.isReceiver()
                ):
                print('Relink from', task_out.getName(),':')
                trgs = task_out.getAffectingOnTask()
                for trg in trgs:
                    print("   - [Make link] from ", trg.getName(), " to ", task_in.getName())
                    info = TaskDescription(target=task_in, parent=trg)
                    cmd = lnkcmd.LinkCommand(info)
                    self.cmd_list.append(cmd)
            else:
                # print("[Make link] from ", task_out.getName(), " to ", task_in.getName())
                info = TaskDescription(target=task_in, parent=task_out)
                cmd = lnkcmd.LinkCommand(info)
                self.cmd_list.append(cmd)
        else:
            print('Can\'t make link')
        self.runIteration()



    def getTaskByName(self, name : str) -> BaseTask:
        for task in self.task_list:
            if task.getName() == name:
                return task
        # print('Can\'t get task by name', name)
        return None
    
    def updateSetOption(self, task_name, param_name, key, value):
        print("Update set options")
        task = self.getTaskByName(task_name)
        if task.checkType("SetOptions"):
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
        
 
    def updateTaskParams(self, initparams : list, addparams : list):
        resparams = []
        for add in addparams:
            for init in initparams:
                if 'type' in init and 'type' in add and init['type'] == add['type']:
                    add.update(init)
                    break
            resparams.append(add)

        for init in initparams:
            found = False
            for add in resparams:
                if 'type' in init and 'type' in add and init['type'] == add['type']:
                    found = True
                    break
            if not found:
                resparams.append(init)
        return resparams
    # Возвращает список созданных задач. Например,
    # если задача содержит список, то создать дочерние задачи по списку
    # Это может быть востребовано для перебора файлов в папке
    # Перебор результатов поиска в Гугл или Яндексе
    # Список действий, перечисленных ГПТ

    def createOrAddTaskByInfo(self,task_type, info : TaskDescription):
        info.helper = self.helper
        info.requester=self.requester
        info.manager = self
        res, task_params = self.helper.getParams(task_type)
        if res:
            task_params.update(info.params)
            info.params = self.updateTaskParams(info.params, task_params)

        curr_cmd = cr.createTaskByType(task_type, info)
        self.cmd_list.append(curr_cmd)
        return self.runCmdList()

    def runCmdList(self) ->BaseTask:
        if len(self.cmd_list) > 0:
            cmd = self.cmd_list.pop(0)
            task, action = cmd.execute()
            if action == 'create' and task != None:
                self.addTask(task)
                self.curr_task = task
                return task
            elif action == 'delete':
                if task in self.task_list:
                    self.task_list.remove(task)
                if self.curr_task == None:
                    self.curr_task = self.task_list[0]
        return None

    def runIteration(self, prompt = ''):
        # print("Run iteration")

        if self.need_human_response:
            self.need_human_response = False
            # return self.getCurrTaskPrompts()

        self.index += 1
        log = 'id[' + str(self.index) + '] '
        out = "Report:\n"
        if len(self.cmd_list) > 0:
            cmd = self.cmd_list.pop(0)
            log += 'Command executed: '
            log += str(cmd) + '\n'
            log += "Command to execute: " + str(len(self.cmd_list)) +"\n"
            task, action = cmd.execute()
            # print('[=]',action)
            if action == 'create' and task != None:
                self.addTask(task)
                self.curr_task = task
            elif action == 'delete':
                if task in self.task_list:
                    self.task_list.remove(task)
                if self.curr_task == None:
                    self.curr_task = self.task_list[0]
            # log += task.task_creation_result
            out += str(task) + '\n'
            out += "Task description:\n"
            # out += task.task_description
            # return self.getCurrTaskPrompts()


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
            # print("Complete task list")
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
                # return self.getCurrTaskPrompts()

        out += 'tasks: ' + str(len(self.task_list)) + '\n'
        out += 'cmds: ' + str(len(self.cmd_list)) + '\n'
        # return self.getCurrTaskPrompts()
    
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
    
    def updateSteppedSelectedInternal(self, info : TaskDescription = None, update_task = True):
        # print(10*"----------")
        dt1 = datetime.datetime.now()        
        init_log = "STEP" + 4*">>" + self.curr_task.getName() + "||" + getTimeForSaving() + "||"
        # print(10*"----------")
        if update_task:
            if info:
                info.stepped = True
                self.curr_task.update(info)
            else:
                self.curr_task.update(TaskDescription( prompt=self.curr_task.getLastMsgContent(), 
                                                    prompt_tag=self.curr_task.getLastMsgRole(), 
                                                    stepped=True))

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


        # acceptedchilds = [t.getName() for t in self.curr_task.getChilds() if t in self.task_list]
        acceptedchilds = [t.getName() for t in self.task_list]
        next = self.curr_task.getNextFromQueue(trgtaskNames=acceptedchilds)

        dt2 = datetime.datetime.now()  
        delta = dt2 - dt1
        init_log += str(delta.microseconds /1000) + 'ms'      
        # if next:
        #     print(init_log,'===>', next.getName(),'in tasks list:',next in self.task_list)
        # else:
        #     print(init_log, 'Next task is None')

        if next not in self.curr_task.getTree():
            # print('Go to the next tree')
            self.return_points.append(self.curr_task)
        # print(len(self.return_points))
        if next and self.curr_task != next and next in self.task_list:
            # print('Next task is in task list')
            # if next.parent == None:
                # next.resetTreeQueue()
            # bres, bparam = next.is_blocking().getParamStruct('block')
            # if next.getParent() != None and next.getParent().isFrozen():
            #     pass
            if next.is_blocking():
                pass
            else:
                # print('Set new current task', next.getName())
                self.curr_task = next
        elif next and self.curr_task != next and next not in self.task_list:
            self.curr_task = self.curr_task.getParent()
            return self.curr_task.getParent()
        else:
            if len(self.return_points) > 0:
                # print('Go to return points from', [t.getName() for t in self.return_points])
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
        return 
    
    def fixTasks(self):
        for task in self.task_list:
            task.fixQueueByChildList()
    
    def updateAndExecuteStep(self, msg):
        self.curr_task.resetTreeQueue()
        info = TaskDescription(prompt=msg,
                                prompt_tag=self.curr_task.getLastMsgRole(),
                                manual=True)
        self.updateSteppedSelectedInternal(info)
        return 

    def executeStep(self):
        self.updateSteppedSelectedInternal()
        return  
    
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
        return  

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
        return  

    
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
        return  
    
    
    def getCurTaskLstMsg(self) -> str:
        return self.curr_task.getMsgs()[-1]['content']
    
    def getCurTaskLstMsgRaw(self) -> str:
        return self.curr_task.getLastMsgContentRaw()
    
    def getCurTaskRole(self) -> str:
        _,role,_ = self.curr_task.getMsgInfo()
        return role
        
    
    


    def convertMsgsToChat(self, msgs):
        r_msgs = []
        # first = ""
        # sec = ""
        # for msg in msgs:
        #     if msg['role'] == 'assistant':
        #         sec = msg['content']
        #         r_msgs.append([first, sec])
        #         first = ""
        #         sec = ""
        #     else:
        #         if first != "":
        #             r_msgs.append([first, sec])
        #             first = msg['content']
        #             r_msgs.append([first, sec])
        #             first = ""
        #             sec = ""
        #         else:
        #             first = msg['content']
        # if first != "":
        #     r_msgs.append([first, sec])
        for msg in msgs:
            if msg['role'] not in ['user','assistant','system']:
                msg['role'] = 'user'
        return msgs


    
    def getByTaskNameParamListInternal(self, task : BaseTask):
        out = []
        for p in task.getAllParams():
            if 'type' in p:
                if p['type'] == 'child' and 'name' in p:
                    out.append(p['type'] + ':' + p['name'])
                else:
                    out.append(p['type'])
        return out
    
    
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
    
    def getAndCheckLongName(self, short_name : str) -> list[bool,str]:
        tasks_dict  = cr.getTasksDict()
        for t in tasks_dict:
            if t['short']== short_name:
                return True, t['type']
        return False, ''
  
    
   
    def setTaskKeyValue(self, param_name, key, mnl_value):
        info = TaskDescription(target=self.curr_task, params={'name':param_name,'key':key,'select':mnl_value})
        cmd = edit.EditParamCommand(info)
        self.cmd_list.append(cmd)
        return self.runIteration('')

    def getAppendableParam(self):
        task_man = TaskManager()
        return task_man.getParamOptBasedOptionsDict()

    def appendNewParamToTask(self, param_name):
        # print('Append new param',param_name,'to task', self.curr_task.getName())
        task_man = TaskManager()
        param = task_man.getParamBasedOptionsDict(param_name)
        if param is not None:
            info = TaskDescription(target=self.curr_task, params=param)
            cmd = edit.AppendParamCommand(info)
            self.cmd_list.append(cmd)
        return self.runIteration('')
    
    def removeParamFromTask(self, param_name):
        info = TaskDescription(target=self.curr_task, params={'name':param_name})
        cmd = edit.RemoveParamCommand(info)
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
        return 

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
                param_task = task.copyAllParams(True)
                print('Copy',task.getName())
                print('Param:', param_task)
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
                            return 
                    else:
                        print('No options')
                        return 
                else:
                    self.createOrAddTask(prompt, trg_type, prompt_tag, parent, param_task)
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
        # Заменить на особую функцию, которая используется только в случае копирования, 
        # чтобы переопределить ее для ExtProject. Для этой задачи при копировании важнее не входные переменные, 
        # а результирующее сообщение
        if 'reqSraw' in self.tasksbranchcopy_param and self.tasksbranchcopy_param['reqSraw']:
            prompt=task.getPromptContentForCopyConverted() 
        else:
            prompt=task.getPromptContentForCopy() 
        prompt_tag=task.getLastMsgRole()
        trg_type = task.getType()
        param_task = task.copyAllParams(True)
        prio = task.getPrio()
        if j == 0:
            if branch['i_par'] is not None:
                parent = tasks_chains[branch['i_par']]['created'][-1]
            else:
                # Самый первый элемент дерева, устнаавливаем родительский элемент
                # устанавливаем произвольного родителя если указано
                if self.tc_new_parent == None:
                    parent = branch['parent']
                else:
                    if i == 0:
                        parent = self.tc_new_parent
                    else:
                        parent = branch['parent']
                # если нужно меняем промпт
                if change_prompt:
                    prompt = edited_prompt
            branch['created'] = []
            branch['convert'] = []
        else:
            parent = self.curr_task
        # print('branch',i,'task',j,'par',parent.getName() if parent else "No parent")
        # Меняем тип задачи
        for switch in self.tc_switch_type:
            if trg_type == switch['src'] and task not in self.tc_ignore_conv:
                trg_type = switch['trg']
            # TODO: При изменении типа задач. Если param_task содержит Collect и в нем input равен array, то создать цепочку задач на базе параметров, но только последовательно 
        if task.checkType('ExtProject'):
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
        elif task.checkType('InExtTree'):
            # res, param = task.getParamStruct('external')
            try:
                found = False
                for i,param in enumerate(param_task):
                    if param['type'] == 'external':
                        found = True
                        param_task[i]['retarget']['chg'] = parent.getName()
                        param_task[i]['project_path'] = param_task[i]['exttreetask_path']
                        param_task[i]['copy'] = 'Copy'
                        del param_task[i]['exttreetask_path']

                        # param_task[i]['retarget']['chg'] = parent.getName()
                        break
                if found:
                    self.createOrAddTask(prompt, trg_type, prompt_tag, parent, param_task)
                else:
                    print('No options for InExtTree')
            except Exception as e:
                print('InExtTree task create error:', e)
                return False
        else:
            self.createOrAddTask(prompt, trg_type, prompt_tag, parent, param_task)
        if j != 0:
            self.curr_task.setPrio(prio)

        if j == 0:
            self.curr_task.freezeTask()
        
        if 'forcecopyresp' in self.tasksbranchcopy_param and self.tasksbranchcopy_param['forcecopyresp']:
            if self.curr_task.checkType('Response'):
                self.curr_task.forceSetPrompt(prompt)

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
                if task.checkType('Response'):
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


    def copyTasksByInfo(self, tasks_chains, change_prompt = False, edited_prompt = '', switch = [], new_parent = None, ignore_conv = [], param = {}):
        # print('Copy tasks by info')
        self.copyTasksByInfoStart(tasks_chains, change_prompt, edited_prompt, switch, new_parent, ignore_conv, param)
        self.copyTasksByInfoExe()
        return self.copyTasksByInfoStop()

    def copyTasksByInfoStart(self, tasks_chains, change_prompt = False, edited_prompt = '',switch = [], new_parent = None, ignore_conv = [], param = {}):
        i = 0
        links_chain = []
        insert_tasks = []
        for branch in tasks_chains:
            print(i,'|',
                  [task.getName() for task in branch['branch']], 
                  branch['done'],'idx=', branch['idx'],'par=' , 
                  branch['parent'].getName() if branch['parent'] else "None", 'idx_par=',
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

        self.tc_new_parent = new_parent
        self.tc_ignore_conv = ignore_conv
        self.tasksbranchcopy_param = param

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
        # for branch in self.tc_tasks_chains:
        #     print('branch convert results:[[from, to]]')
        #     print([[t['from'].getName(),t['to'].getName()] for t in branch['convert']])
        # print('Links list:')
        # print([[link['out'].getName(),link['in'].getName()] for link in self.tc_links_chain])
        # print('Inserting order:', [[i,link['in'].getName()] for i,link in enumerate(self.tc_links_chain)])

        for link in self.tc_links_chain:
            outtask = self.getCopyedTask(self.tc_tasks_chains, link['out'])
            if 'insert' in link and 'prompt' in link:
                param_task = link['in'].copyAllParams(True)
                self.curr_task = link['in']
                if link['insert']:
                    if 'option' in link:
                        if link['option'] == 'std':
                            self.makeTaskAction(prompt=link['prompt'],type=link['type'], creation_type='Insert', creation_tag=link['tag'], params=param_task)
                            intask = self.slct_task
                            self.makeLink( intask, outtask )
                        elif link['option'] == 'sub':
                            self.makeTaskAction(prompt=link['prompt'],type=link['type'], creation_type='SubTask', creation_tag=link['tag'], params=param_task)
                            intask = self.curr_task
                            self.makeLink( intask, outtask )
                        elif link['option'] == 'move':
                            self.makeTaskAction("","","Unlink","")
                            intask = self.curr_task
                            self.makeLink( intask, outtask )
                        else:
                            pass
                    else:
                        self.makeTaskAction(prompt=link['prompt'],type=link['type'], creation_type='Insert', creation_tag=link['tag'], params=param_task)
                        intask = self.slct_task
                        self.makeLink( intask, outtask )
                else:
                    self.makeTaskAction(prompt=link['prompt'],type=link['type'], creation_type='SubTask', creation_tag=link['tag'], params=param_task)
                    intask = self.curr_task
                    self.makeLink( intask, outtask )
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

        return 
 

    def saveInfo(self, check = False):
        tree_info = []
        self.updateTreeArr(check_list=check)
        for task in self.tree_arr:
            task_buds = self.getSceletonBranchBuds(task)
            tree_info.append(Sr.ProjectSearcher.getInfoForSearch(task_buds))

        # print('Save info', self.getName(), '[',len(self.tree_arr),']\n', tree_info)
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
        if len(self.tree_arr) > 0:
            Sr.ProjectSearcher.saveSearchInfo(tree_info, self.info)
        writer.writeJsonToFile(path_to_projectfile, self.info, 'w', 1)



    def addActions(self, action = '', prompt = '', tag = '', act_type = '', param = {}):
        if 'dont' in param:
            del param['dont']
        if self.info is None:
            self.saveInfo()
        id = len(self.info['actions'])
        curr = ""
        sel = ""
        multi = [t.getName() for t in self.getMultiSelectedTasks()]
        if self.getCurrentTask():
            curr = self.getCurrentTask().getName()
        if self.getSelectedTask():
            sel = self.getSelectedTask().getName()
        self.info['actions'].append(Act.createActionPack(id, action, prompt, tag, act_type, param, curr, sel, multi))
        self.saveInfo()

    def remLastActions(self):
        if len(self.info['actions']) > 0:
            cmd = self.info['actions'].pop()
            print('Remove last cmd:', cmd)
            self.saveInfo()

    def initInfo(self, method, task : BaseTask = None, path = 'saved', act_list = [], repeat = 3, limits = 1000, params = {}):
        self.loadexttask = method
        if 'path' in params:
            self.setPath(Loader.Loader.getUniPath(params['path']))
            del params['path']
        else:
            if task is not None:
                tmp_manname = task.getName()
                tmp_manpath = os.path.join(path,'tmp', tmp_manname)
                idx = 0
                while os.path.exists(tmp_manpath):
                    idx += 1
                    tmp_manname = task.getName() + '_' + str(idx)
                    tmp_manpath = os.path.join(path,'tmp', tmp_manname)
                    
                params['name'] = tmp_manname
                self.setPath(tmp_manpath)
            else:
                self.setPath(path)
        self.saveInfo()
        self.curr_task = task
        if task is not None:
            self.task_list = [task]
            if 'name' in params:
                self.setName(params['name'])
            else:
                task_name = task.getName() if task is not None else 'Base'
                self.setName(task_name)
                if 'task' not in self.info:
                    self.info['task'] = task_name
        
        self.info.update(params)

        if 'name' in self.info:
            self.setName(self.info['name'])
        else:
            if 'task' in self.info:
                self.setName(self.info['task'])
            else:
                self.setName('Base')
            

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
    def sortKey(self, task):
        res, pparam = task.getParamStruct('tree_step')
        if res:
            idx = pparam['idx']
        else:
            idx = 0
        return idx
    

    def addTask(self, task :BaseTask):
        if task ==None:
            return
        # print('Add task', task.getName())
        if self.curr_task == None:
            self.curr_task = task
        if task not in self.task_list:
            self.task_list.append(task)
    
    def rmvTask(self, task: BaseTask):
        if task in self.task_list:
            self.task_list.remove(task)
 

    def addTasks(self, tasks: list):
        for task in tasks:
            self.addTask(task)
        return
    
   
    def removeTaskList(self, del_tasks):
        self.curr_task.extractTaskList(del_tasks)
        for task in del_tasks:
            self.curr_task = task
            self.makeTaskActionBase('', '', "Delete", '')


   
    def copyTasksIntoManager(self, tasks : list[BaseTask]):
        next_man = self
        for task in tasks:
            if task not in next_man.task_list:
                cur_man = task.getManager()
                next_man.addTask(task)
                task.setManager(next_man)
                cur_man.rmvTask(task)

    def allowUpdateInternalArrayParam(self):
        cnt = self.getFrozenTasksCount()
        if cnt == 0:
            return True
        return False
    
   
    def copyTree(self, branch_infos):
        parent_task = None
        for info in branch_infos:
            if info['parent_branch'] != None:
                last_branch = branch_infos[info['parent_branch']]['created']
                parent_task = self.getTaskByName(last_branch[-1])
                self.copyBranchPartByInfo(info, parent_task)
            else:
                if len(info['branch']):
                    trgtaskname = info['branch'][-1]['parent']
                    if trgtaskname != "":
                        print(f"Try to find task with {trgtaskname}")
                        parent_task = self.getTaskByName(trgtaskname)
                self.copyBranchPartByInfo(info, parent_task)
        return info


    def copyBranchPartByInfo(self, branch, start_parent: BaseTask):
        parent = start_parent
        branch['created'] = []
        branch['convert'] = []
        for j, task_info in enumerate(branch['branch']):
            # task_info = branch['branch'][j]
            param_task = task_info['params']
            if j != 0:
                parent = self.getCurrentTask()
            trg_type = task_info["trg_type"]
            prompt = task_info["prompt"]
            role = task_info["role"]
            prio = task_info["prio"]
            trgtaskname = task_info["trgtaskname"]
            if trg_type.endswith('InExtTree'):
                # res, param = task.getParamStruct('external')
                try:
                    found = False
                    for i,param in enumerate(param_task):
                        if param['type'] == 'external':
                            found = True
                            param_task[i]['retarget']['chg'] = parent.getName()
                            param_task[i]['project_path'] = param_task[i]['exttreetask_path']
                            param_task[i]['copy'] = 'Copy'
                            del param_task[i]['exttreetask_path']

                            # param_task[i]['retarget']['chg'] = parent.getName()
                            break
                    if found:
                        self.createOrAddTask(prompt, trg_type, role, parent, param_task, trgtaskname)
                    else:
                        print('No options for InExtTree')
                except Exception as e:
                    print('InExtTree task create error:', e)
                    return False
            else:
                self.createOrAddTask(prompt, trg_type, role, parent, param_task, trgtaskname)
            if j != 0:
                self.curr_task.setPrio(prio)

            if j == 0:
                self.curr_task.freezeTask()
            
            if trg_type.endswith('Response') and prompt != "":
                self.curr_task.forceSetPrompt(prompt)

            branch['created'].append(self.getCurrentTask().getName())
            branch['convert'].append({'from': task_info["trgtaskname"], 'to': self.getCurrentTask().getName()})

    def syncManager( self, manager : Man.Jun):
        manager.task_list = self.task_list
        manager.setCurrentTask(self.getCurrentTask())
        manager.setSelectedTaskByName(self.getSelectedTask().getName())
        for task in self.getMultiSelectedTasks():
            manager.addTaskToMultiSelected(task)

    def forceUnFreezeTask( self, task : BaseTask ):
        task.unfreezeTask()
    
