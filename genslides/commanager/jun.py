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

import py7zr

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

        self.browser = WebBrowser()

        self.need_human_response = False


        task_manager = TaskManager()

        links = task_manager.getLinks()
        # parent_task_list = task_manager.getParentTaskPrompts()
        # print("parent tasks=", parent_task_list)
        # for task in parent_task_list:
        #     print(10*"==","=>type=", task['type'])
        #     self.makeTaskAction(task['content'], task['type'], "New")
        self.createTask()

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

            # task.completeTask()

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
        parent_prompt_list = task_manager.getTaskPrompts(parent_path)

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
        





    #        if not os.path.exists("saved"):
    #               os.makedirs("saved")
    #        self.path_searches = "saved/searches.json"
    #        self.path_links = "saved/links.json"
    #        self.path_pagecontent = "saved/page_content.json"
    #        path = self.path_searches
    #        if not os.path.exists(path):
    #               with open(path, 'w') as f:
    #                      print('Create file: ', path)
    #        path = self.path_links
    #        if not os.path.exists(path):
    #               with open(path, 'w') as f:
    #                      print('Create file: ', path)
    #        path = self.path_pagecontent
    #        if not os.path.exists(path):
    #               with open(path, 'w') as f:
    #                      print('Create file: ', path)
    # def saveRespJson(self,path, request, response):
    #        resp_json_out = {}
    #        resp_json_out['request'] = request
    #        resp_json_out['responses'] = response
    #        with open(path, 'w') as f:
    #               json.dump(resp_json_out,f,indent=1)
    # def getResponse(self, path, request):
    #        if os.stat(path).st_size != 0:
    #               try:
    #                      with open(path, 'r') as f:
    #                             rq = json.load(f)
    #                      if 'request' in rq and rq['request'] == request:
    #                             return rq['responses']
    #               except json.JSONDecodeError:
    #                      pass
    #        return []
    def setNextTask(self, input):
        saver = SaveData()
        chck = gr.CheckboxGroup.update(choices=saver.getMessages())

        try:
            inc = int(input)
        except ValueError:
            print("Value error")
        #Try float.
            # ret = float(s)
            return "","", self.drawGraph(), "", "", chck
        print("Increment=",inc)
        self.task_index += inc

        if len(self.task_list) <= self.task_index:
            self.task_index = 0
        elif self.task_index < 0:
            self.task_index = len(self.task_list) - 1


        self.curr_task = self.task_list[self.task_index]

        # return self.drawGraph(), pprint.pformat((self.curr_task.msg_list))
        tokens, price = self.curr_task.getCountPrice()
        output = "Tokens=" + str(tokens) +"\n"
        output += "Price=" + str(price) + "\n"
        output += pprint.pformat(self.curr_task.msg_list)
        in_prompt, in_role, out_prompt = self.curr_task.getMsgInfo()
        return out_prompt, output ,self.drawGraph(), in_prompt, in_role, chck

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

    def drawGraph(self):
        if len(self.task_list) > 0:
            f = graphviz.Digraph(comment='The Test Table')

            # if self.curr_task:
            #         f.node ("Current",self.curr_task.getInfo(), style="filled", color="skyblue", shape = "rectangle", pos = "0,0")
            
            for task in self.task_list:
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
            
            for task in self.task_list:
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
  
    def makeTaskAction(self, prompt, type, creation_type, creation_tag):
        # print(10*"==")
        # print("Create new task")
        # print("type=",type)
        # print("prompt=", prompt)
        # print("creation type=", creation_type)
        out = ""
        log = "Nothing"
        img_path = "output/img.png"
        print(10*"====")
        print("Make action ", creation_type)
        print(10*"====")

        if type is None or creation_type is None:
            return out, log, img_path
        if creation_type == "Edit":
            
            info = TaskDescription(prompt=prompt,prompt_tag=creation_tag, manual=True)
            self.curr_task.update(info)
            in_prompt, in_role, out_prompt = self.curr_task.getMsgInfo()
            return out_prompt, log, self.drawGraph() , in_prompt, in_role, []
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
                input_params["prompt"] = {"message": prompt, "options":["good","bad"]}

            info = TaskDescription(prompt=self.curr_task.prompt,prompt_tag=self.curr_task.prompt_tag, params=[input_params])
            self.curr_task.update(info)
            return out, log, self.drawGraph() , "","",[]
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
                info = TaskDescription(prompt=self.curr_task.getRichPrompt(),prompt_tag=self.curr_task.getTagPrompt(), parent=self.slct_task)
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
            # if type.startswith("Response"):
                return out, log, img_path
        elif creation_type == "SubTask":
            parent = self.curr_task
        else:
            return out, log, img_path
        
        curr_cmd = cr.createTaskByType(type, TaskDescription(prompt=prompt, helper=self.helper, requester=self.requester, parent=parent,prompt_tag=creation_tag))

        # print("Current cmd=", curr_cmd)

        if not curr_cmd:
            return out, log, img_path
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

        in_prompt, in_role, out_prompt = self.curr_task.getMsgInfo()
        return self.drawGraph(), gr.Dropdown.update(choices= self.getTaskList()), in_prompt, in_role, out_prompt

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
            return out_prompt, "" ,self.drawGraph(), in_prompt, in_role, chck
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
                self.curr_task = task
            log += task.task_creation_result
            out += str(task) + '\n'
            out += "Task description:\n"
            out += task.task_description
            img_path = self.drawGraph()
            in_prompt, in_role, out_prompt = self.curr_task.getMsgInfo()
            return out_prompt, log ,self.drawGraph(), in_prompt, in_role, chck
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
            in_prompt, in_role, out_prompt = self.curr_task.getMsgInfo()
            return out_prompt, log ,self.drawGraph(), in_prompt, in_role, chck
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
        return out_prompt, log ,self.drawGraph(), in_prompt, in_role, chck
        #  return out, log, img_path, self.curr_task.msg_list[-1]["content"], self.curr_task.msg_list[-1]["role"]
    
    def update(self):
        print(10*"----------")
        print("NEW UPDATE",10*">>>>>>>>>>>")
        print(10*"----------")
        for task in self.task_list:
            if task.parent == None:
                task.update()
        return self.runIteration("")
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
 


class Projecter:
    def __init__(self, manager : Manager = None) -> None:
        mypath = "projects/"
        if not os.path.exists(mypath):
            os.makedirs(mypath)
        self.mypath = mypath
        self.savedpath = "saved/"
        self.manager = manager
        saver = SaveData()
        saver.removeFiles()
        self.current_project_name = self.manager.getParam("current_project_name")
        self.updateSessionName()

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

    def clear(self):
        self.clearFiles()
        self.manager.onStart() 

    def getEvaluetionResults(self, input):
        print("In:", input)
        saver = SaveData()
        saver.updateEstimation(input)


    def load(self, filename):
        if filename == "":
            return ""
        onlyfiles = [f for f in listdir(self.mypath) if isfile(join(self.mypath, f))]
        self.clearFiles()
        if filename + ".7z" not in onlyfiles:
            return ""
        with py7zr.SevenZipFile(self.mypath + filename + ".7z", 'r') as archive:
            archive.extractall(path=self.savedpath)

        self.manager.onStart() 
        self.current_project_name = filename
        self.manager.setParam("current_project_name",self.current_project_name)
        self.updateSessionName()

        return filename

    
    def save(self, name):
        self.current_project_name = name
        self.manager.setParam("current_project_name",self.current_project_name)

        mypath = self.savedpath
        onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
        first = True
        for file in onlyfiles:
            if first:
                with py7zr.SevenZipFile( self.mypath + name + ".7z", 'w') as archive:
                    archive.write(self.savedpath + file, arcname = file)
                first = False
            else:
                with py7zr.SevenZipFile( self.mypath + name + ".7z", 'a') as archive:
                    archive.write(self.savedpath + file, arcname = file)

        return gr.Dropdown.update( choices= self.loadList(), interactive=True)

