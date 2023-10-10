from genslides.task.presentation import PresentationTask
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

from genslides.utils.largetext import SimpleChatGPT

import os
from os import listdir
from os.path import isfile, join

import json

import gradio as gr
import graphviz

import pprint

import pyperclip


import datetime

class Manager:
    def __init__(self, helper: RequestHelper, requester: Requester, searcher: WebSearcher) -> None:
        self.helper = helper
        self.requester = requester
        self.searcher = searcher
        self.vars_param = ["stopped", "input", "output", "watched"]
        self.path_to_file = "config/base.json"
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
        self.tree_arr = []
        self.tree_idx = 0

        self.browser = WebBrowser()

        self.need_human_response = False
        self.path = 'saved/'
        self.proj_pref = ''

    def getPath(self) -> str:
        return self.path
    
    def setPath(self, path : str):
        self.path = path

    def getTaskExtention(self) -> str:
        return '.json'

    def getProjPrefix(self) -> str:
        return self.proj_pref
  

    def appendExtendProjectTasks(self, path_to_project, name):
        task_manager = TaskManager()
        task_manager.setPath(path_to_project)
        task_manager.setProjPrefix(name)
        self.loadTasksList()




    def loadTasksList(self):
        print(10*"=======")
        print('Load tasks from files')
        task_manager = TaskManager()
        self.createTask()

        links = task_manager.getLinks()

        for link in links:
            trgs = link['linked']
            affect_task = self.getTaskByName(link['name'])
            for trg in trgs:
                influense_task = self.getTaskByName(trg)
                self.makeLink(affect_task, influense_task)

        for task in self.task_list:
                task.completeTask()

        for task in self.task_list:
            print("Task name=", task.getName(), " affected")
            for info in task.by_ext_affected_list:
                print("by ",info.parent.getName())
            print("influence")
            for info in task.affect_to_ext_list:
                print("to ",info.parent.getName())


    def goToNextTree(self):
        print('Current tree was',self.tree_idx,'out of',len(self.tree_arr))
        if len(self.tree_arr) > 0:
            if self.tree_idx + 1 < len(self.tree_arr):
                self.tree_idx += 1
            else:
                self.tree_idx = 0
            self.curr_task = self.tree_arr[self.tree_idx]
        else:
            for task in self.task_list:
                if task.parent is None:
                    self.tree_arr.append(task)
            if len(self.tree_arr) > 0:
                self.curr_task = self.tree_arr[0]
                self.tree_idx = 1
        print('Current task is', self.curr_task.getName())
        return self.getCurrTaskPrompts()
            

    def goToNextChild(self):
        chs = self.curr_task.getChilds()
        if len(chs) > 0:
            if len(chs) > 1:
                self.branch_lastpar = self.curr_task
                self.branch_idx = 0
            self.curr_task = chs[0]
        return self.getCurrTaskPrompts()
    
    def goToParent(self):
        if self.curr_task.parent is not None:
            self.curr_task = self.curr_task.parent
        return self.getCurrTaskPrompts()

    def goToNextBranch(self):
        trg = self.curr_task
        idx = 0
        while(idx < 1000):
            if trg.parent is None:
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
        print(10*"=======")
        if prnt_task == None:
            parent_path = ""
        else:
            parent_path = prnt_task.path
            self.curr_task = prnt_task
            # print("task=", self.curr_task.path)
            print("Parent task path=", parent_path)
        init_task_list = self.task_list.copy()
        task_manager = TaskManager()
        parent_prompt_list = task_manager.getTaskPrompts(self.getPath(), parent_path)

        print("prompt count=",len(parent_prompt_list))

        for prompt in parent_prompt_list:
            self.curr_task = prnt_task
            # print("content=",prompt['content'])
            if parent_path == "":
                self.makeTaskAction(prompt['content'], prompt['type'], "New", prompt['role'])
            else:
                self.makeTaskAction(prompt['content'], prompt['type'], "SubTask",prompt['role'])

        trg_task_list = self.task_list.copy()

        print("task count=",len(self.task_list),",exclude=",len(init_task_list))
        if len(parent_prompt_list):
            for task in trg_task_list:
                if task not in init_task_list:
                    print("+++",parent_path)
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

    def drawGraph(self, only_current= True):
        if only_current:
            trg_list = self.curr_task.getTree()
        else:
            trg_list = self.task_list
        if len(trg_list) > 0:
            f = graphviz.Digraph(comment='The Test Table')

            # if self.curr_task:
            #         f.node ("Current",self.curr_task.getInfo(), style="filled", color="skyblue", shape = "rectangle", pos = "0,0")
            
            for task in trg_list:
                if task == self.curr_task:
                    f.node( task.getIdStr(), task.getName(),style="filled",color="skyblue")
                    # f.node ("Current",task.getInfo(), style="filled", color="skyblue", shape = "rectangle", pos = "0,0")
                    # f.edge (task.getIdStr(), "Current", color = "skyblue", arrowhead = "dot")
                elif task ==self.slct_task:
                    f.node( task.getIdStr(), task.getName(),style="filled",color="darksalmon")
                else:
                    if self.getTaskParamRes(task, "stopped"):
                    # if task.getParam("stopped") == [True, True]:
                        f.node( task.getIdStr(), task.getName(),style="filled",color="crimson")
                    elif self.getTaskParamRes(task, "input"):
                    # elif task.getParam("input") == [True, True]:
                        f.node( task.getIdStr(), task.getName(),style="filled",color="aquamarine")
                    elif self.getTaskParamRes(task, "output"):
                    # elif task.getParam("output") == [True, True]:
                        f.node( task.getIdStr(), task.getName(),style="filled",color="darkgoldenrod1")
                    elif task.is_freeze:
                        f.node( task.getIdStr(), task.getName(),style="filled",color="cornflowerblue")
                    else:
                        info = task.getInfo()
                        if task.prompt_tag == "assistant":
                            f.node( task.getIdStr(), task.getName(),style="filled",color="azure2")
                        else:
                            f.node( task.getIdStr(), info)


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
        return ["New", "SubTask","Edit","Delete", "Select", "Link", "Unlink", "Parent", "RemoveParent","EditAndStep"]
    def getSecdCommandList(self):
        return ["RemoveBranch", "RemoveTree", "Insert","Remove","ReqResp"]

  
    def makeTaskAction(self, prompt, type, creation_type, creation_tag):
        if creation_type in self.getMainCommandList() or creation_type in self.vars_param:
            return self.makeTaskActionBase(prompt, type, creation_type, creation_tag)
        elif creation_type in self.getSecdCommandList():
            return self.makeTaskActionPro(prompt, type, creation_type, creation_tag)
        saver = SaveData()
        chck = gr.CheckboxGroup.update(choices=saver.getMessages())
        return "", "" ,self.drawGraph(),"" , "user", chck
 
    def makeTaskActionPro(self, prompt, type, creation_type, creation_tag):
        out_prompt = ""
        in_prompt = ""
        in_role = "user"
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
                self.makeTaskActionBase(prompt, type, "RemoveParent", creation_tag)
                self.curr_task = task1
                self.makeTaskActionBase(prompt, type, "SubTask", creation_tag)
            else:
                self.makeTaskActionBase(prompt, type, "New", creation_tag)
            self.slct_task = self.curr_task
            self.curr_task = task2
            self.makeTaskActionBase(prompt, type, "Parent", creation_tag)
            print('Parents:\nFirst', task1.parent.getName(),'=',task1.getName())
            print('Childs')
            for ch in task1.getChilds():
                print(ch.getName())
            print(task1.queue)
            print('Middle', self.slct_task.parent.getName(),'=',self.slct_task.getName())
            print('Childs')
            for ch in self.slct_task.getChilds():
                print(ch.getName())
            print(self.slct_task.queue)
            print('Last', self.curr_task.parent.getName(),'=', self.curr_task.getName())
            print('Childs')
            for ch in self.curr_task.getChilds():
                print(ch.getName())
            print(self.curr_task.queue)
            task1.update()

        elif creation_type == "Remove":
            task1 = self.curr_task.parent
            task2 = self.curr_task
            if task1 is None:
                self.makeTaskActionBase(prompt, type, "Delete", creation_tag)
            else:
                task3_list = task2.getChilds()
                self.makeTaskActionBase(prompt, type, "Delete", creation_tag)
                self.slct_task = task1
                for task in task3_list:
                    self.curr_task = task
                    self.makeTaskActionBase(prompt, type, "Parent", creation_tag)

        elif creation_type == "ReqResp":
            if self.curr_task is not None:
                self.makeTaskActionBase(prompt,"Request","SubTask","user")
            else:
                self.makeTaskActionBase(prompt,"Request","New","user")
            self.makeTaskActionBase(prompt,"Response","SubTask","assistant")
            
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
        print(10*"====")
        print("Make action", creation_type)
        print(10*"====")

        if type is None or creation_type is None:
            print('Abort maske action')
            return self.getCurrTaskPrompts()
        if creation_type == "Edit":
            info = TaskDescription(prompt=prompt,prompt_tag=creation_tag, manual=True)
            self.curr_task.update(info)
            return self.getCurrTaskPrompts()
        elif creation_type == "EditAndStep":
            info = TaskDescription(prompt=prompt,prompt_tag=creation_tag, manual=True, stepped=True)
            self.updateSteppedSelectedInternal(info)
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
                self.curr_task.removeParent()
                self.curr_task.update()
            return self.runIteration(prompt)
        elif creation_type == "Parent":
            if self.curr_task != self.slct_task and self.curr_task and self.slct_task:
                print("Make ", self.slct_task.getName()," parent of ", self.curr_task.getName())
                info = TaskDescription( prompt=self.curr_task.getLastMsgContent(), prompt_tag=self.curr_task.getLastMsgRole(), parent=self.slct_task)
                # info = TaskDescription(prompt=self.curr_task.getRichPrompt(),prompt_tag=self.curr_task.getTagPrompt(), parent=self.slct_task)
                self.curr_task.update(info)
            return self.runIteration(prompt)
        elif creation_type == "Unlink":
            if self.curr_task:
                self.curr_task.removeLinkToTask()
            return self.runIteration(prompt)
        elif creation_type == "Link":
            if self.curr_task != self.slct_task:
                self.makeLink(self.curr_task, self.slct_task)
            return self.runIteration(prompt)
        elif creation_type == "Delete":
            task = self.curr_task
            task.beforeRemove()
            self.task_list.remove(task)
            self.setNextTask("1")
            del task
            return self.runIteration(prompt)
        elif creation_type == "New":
            parent = None
            if cr.checkTypeFromName(type, "Response"):
                print('Can\'t create new Response')
            # if type.startswith("Response"):
                return out, log, img_path
        elif creation_type == "SubTask":
            parent = self.curr_task
        else:
            return out, log, img_path
        
        return self.createOrAddTask(prompt,type, creation_tag, parent)
        
    def createOrAddTask(self, prompt, type, tag, parent, params = None):
        print('Create task')
        info = TaskDescription(prompt=prompt, prompt_tag=tag, 
                                                             helper=self.helper, requester=self.requester, manager=self, 
                                                             parent=parent)
        if params is not None:
            info.params = params
        curr_cmd = cr.createTaskByType(type, info)

        if not curr_cmd:
            return self.getCurrTaskPrompts()
        self.cmd_list.append(curr_cmd)
        return self.runIteration(prompt)

    
    def makeLink(self, task_in : BaseTask, task_out :BaseTask):
        if task_in != None and task_out != None:
            print("Make link from ", task_out.getName(), " to ", task_in.getName())
            task_in.createLinkToTask(task_out)

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
        out = []
        for task in self.task_list:
            out.append(task.getName())
        return out
    
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
 
    def runIteration(self, prompt):
        print("Run iteration")
        img_path = "output/img.png"

        if not os.path.exists(img_path):
            img_path = "examples/test.png"

        saver = SaveData()
        chck = gr.CheckboxGroup.update(choices=saver.getMessages())


        if self.need_human_response:
            self.need_human_response = False
            # return "", "", img_path, self.curr_task.msg_list[-1]["content"], self.curr_task.msg_list[-1]["role"]
            in_prompt, in_role, out_prompt = self.curr_task.getMsgInfo()
            return self.getCurrTaskPrompts()
        # if len(self.task_list) > 0:
        #     f = graphviz.Digraph(comment='The Test Table')
            
        #     for task in self.task_list:
        #         if task == self.curr_task:
        #             f.node( task.getIdStr(), task.getName(),style="filled",color="skyblue")
        #         else:
        #             f.node( task.getIdStr(), task.getName())
            
        #     for task in self.task_list:
        #         for child in task.childs:
        #             f.edge(task.getIdStr(), child.getIdStr())
        #     img_path = "output/img"
        #     f.render(filename=img_path,view=False,format='png')
        #     img_path += ".png"
        #     del f

        self.index += 1
        log = 'id[' + str(self.index) + '] '
        out = "Report:\n"
        if len(self.cmd_list) > 0:
            cmd = self.cmd_list.pop(0)
            log += 'Command executed: '
            log += str(cmd) + '\n'
            log += "Command to execute: " + str(len(self.cmd_list)) +"\n"
            task = cmd.execute()
            if (task != None):
                self.task_list.append(task)
                if task.parent is None:
                    self.tree_arr.append(task)
                self.curr_task = task
            log += task.task_creation_result
            out += str(task) + '\n'
            out += "Task description:\n"
            out += task.task_description
            img_path = self.drawGraph()
            in_prompt, in_role, out_prompt = self.curr_task.getMsgInfo()
            return self.getCurrTaskPrompts()
            #  return out, log, img_path, self.curr_task.msg_list[-1]["content"], self.curr_task.msg_list[-1]["role"]

        img_path = self.drawGraph()
        index = 0

        all_task_expanded = False 
        if len(self.task_list) > 0:
            all_task_expanded = True
        for task in self.task_list:
            log += "["+ str(index) + "] "
            index += 1
            cmd = task.getCmd()
            if (cmd != None):
                log += "From task:" + str(task) + " "
                log += "add command:" + str(cmd)
                self.cmd_list.append(cmd)
            # else:
                # task.completeTask()
                all_task_expanded = False
        all_task_completed = False
        if all_task_expanded:
            all_task_completed = True
            log += "All task expanded\n"
            print("Complete task list")
            for task in self.task_list:
                # print("complete tasl=", task.getName())
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
            return self.getCurrTaskPrompts()
            #  return out, log, img_path, self.curr_task.msg_list[-1]["content"], self.curr_task.msg_list[-1]["role"]
            # if self.curr_task:
            #     self.curr_task.completeTask()

        # for task in self.task_list[:]:
        #     if task.isSolved():
        #         self.task_list.remove(task)

        if len(self.task_list) == 0:
            if True:
                log += "No any task"
                return out, log, img_path, "", ""
            log += "Start command\n"
            curr_task = PresentationTask(TaskDescription(prompt=prompt, helper=self.helper, requester=self.requester))
            self.task_list.append(curr_task)
            out += "Task description:\n"
            log += curr_task.task_creation_result
            out += curr_task.task_description
            self.curr_task = curr_task
            return out, log, img_path

           # curr_task = InformationTask( None, self.helper, self.requester, prompt)
            # responses = []
            # responses = chatgpttask.completeTask()
            # log += "Search list:\n"
            # for resp in responses:
            #        log += resp + '\n'
            # log += "Getted links:\n"
            # links = []
            # googletask = GoogleTask(searcher=self.searcher, reqhelper=self.helper, requester=self.requester, prompt=responses)
            # links = googletask.completeTask()
            # for link in links:
            #        log += link + '\n'

            # browsertask = BrowserTask(browser=self.browser, reqhelper=self.helper, requester=self.requester, prompt=links)
            # text = browsertask.completeTask()
            # print('text len=',len(text))
            # summtask = SummaryTask(summator=self.summator,reqhelper=self.helper,requester=self.requester,prompt=text)
            # summtask.completeTask()
        out += 'tasks: ' + str(len(self.task_list)) + '\n'
        out += 'cmds: ' + str(len(self.cmd_list)) + '\n'
        in_prompt, in_role, out_prompt = self.curr_task.getMsgInfo()
        return self.getCurrTaskPrompts()
        #  return out, log, img_path, self.curr_task.msg_list[-1]["content"], self.curr_task.msg_list[-1]["role"]
    
    def update(self):
        print(10*"----------")
        print("NEW UPDATE",10*">>>>>>>>>>>")
        print(10*"----------")
        for task in self.task_list:
            if task.parent == None:
                task.update()
        return self.runIteration("")
    
    def updateSteppedSelectedInternal(self, info : TaskDescription = None):
        print(10*"----------")
        print("STEP",8*">>>>>>>>>>>","||||||")
        print(10*"----------")
        if info:
            info.stepped = True
            self.curr_task.update(info)
        else:
            # idx = 0
            # while(idx < 1000):
            #     if self.curr_task.parent is None:
            #         print('Parent of',self.curr_task.getName(),' is None')
            #         break
            #     if self.curr_task.parent.findNextFromQueue(True) is not None:
            #         par = self.curr_task.parent
            #         self.curr_task = par
            #     else:
            #         print('Can\'t step on',self.curr_task.parent.getName())
            #         break
            #     idx += 1
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
        if next:
            print("Next task is", next.getName())
            # if next.parent == None:
                # next.resetTreeQueue()
            self.curr_task = next
        else:
            if self.curr_task.parent:
                print("Done some")
            else:
                print("On start")
        return next
    
    def resetCurTaskQueue(self):
        self.curr_task.resetTreeQueue()
        return self.getCurrTaskPrompts()
    
    def fixTasks(self):
        for task in self.task_list:
            task.fixQueueByChildList()
        return self.getCurrTaskPrompts()

    
    def updateSteppedTree(self, info = None):
        index = 0
        self.curr_task.resetTreeQueue()
        while(index < 3):
            if index == 0 and info is not None:
                next = self.updateSteppedSelectedInternal(info)
            else:
                next = self.updateSteppedSelectedInternal()
            if next is None:
                print("Done in",index,"iteration")
                break
            index +=1
        return self.getCurrTaskPrompts() 
    
    def getCurrTaskPrompts(self):
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
        return r_msgs, in_prompt ,self.drawGraph(), out_prompt, in_role, chck, self.curr_task.getName(), self.curr_task.getAllParams(), "", gr.Dropdown.update(choices= self.getTaskList()),gr.Dropdown.update(choices=[p['type'] for p in self.curr_task.params if 'type' in p], interactive=True), gr.Dropdown.update(choices=[t.getName() for t in self.curr_task.getAllParents()], value=self.curr_task.getName(), interactive=True)
    
    def getByTaskNameParamList(self, task_name):
        task = self.getTaskByName(task_name)
        return gr.Dropdown.update(choices=[p['type'] for p in task.params if 'type' in p], interactive=True)
    
    def getFinderKeyString(self,task_name, fk_type, param_name, key_name):
        if fk_type == 'msg':
            value = '{' + task_name + ':msg_content}'
        elif fk_type == 'json':
            value = '{' + task_name + ':msg_content:json:}'
        elif fk_type == 'tokens':
            value = '{' + task_name + ':tokens_cnt}'
        elif fk_type == 'param':
            value = '{' + task_name + ':' + param_name + ':' + key_name + '}'
        pyperclip.copy(value)
        pyperclip.paste()

    
    def getTaskKeys(self, param_name):
        return self.getNamedTaskKeys(self.curr_task, param_name)

    def getByTaskNameTasksKeys(self, task_name, param_name):
        print(task_name, param_name)
        task = self.getTaskByName(task_name)
        return self.getNamedTaskKeys(task, param_name)

    def getNamedTaskKeys(self, task : BaseTask, param_name : str):
        res, data = task.getParamStruct(param_name)
        print(res, data, task.getName(), task.params)
        a = []
        if res:
            task_man = TaskManager()
            a = task_man.getListBasedOptionsDict(data)
        print('Get named task keys', a)
        return gr.Dropdown(choices=a, interactive=True)
    
    def getTaskKeyValue(self, param_name, param_key):
        task_man = TaskManager()
        res, data = self.curr_task.getParamStruct(param_name)
        if res and param_key in data:
            cur_val = data[param_key]
            values = task_man.getOptionsBasedOptionsDict(param_name, param_key)
            if cur_val in values:
                return gr.Dropdown.update(choices=values, value=cur_val, interactive=True)
        return gr.Dropdown.update(choices=[cur_val], value=cur_val, interactive=True)
    
    def setTaskKeyValue(self, param_name, key, slt_value, mnl_value):
        if mnl_value == "":
            self.curr_task.updateParamStruct(param_name, key, slt_value)
        else:
            self.curr_task.updateParamStruct(param_name, key, mnl_value)
        return  self.getCurrTaskPrompts()

    def getAppendableParam(self):
        task_man = TaskManager()
        return task_man.getParamOptBasedOptionsDict()

    def appendNewParamToTask(self, param_name):
        task_man = TaskManager()
        param = task_man.getParamBasedOptionsDict(param_name)
        if param is not None:
            self.curr_task.setParamStruct(param)
        return self.getCurrTaskPrompts()

    def updateSteppedSelected(self):
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
 


