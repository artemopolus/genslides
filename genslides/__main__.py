from genslides.task.presentation import PresentationTask
from genslides.task.base import TaskDescription

from genslides.utils.reqhelper import RequestHelper
from genslides.utils.testrequest import TestRequester
from genslides.utils.request import Requester
from genslides.utils.searcher import WebSearcher
from genslides.utils.searcher import GoogleApiSearcher
from genslides.utils.largetext import Summator
from genslides.utils.browser import WebBrowser

import os
import json

import gradio as gr
import graphviz


class Manager:
    def __init__(self, helper: RequestHelper, requester: Requester, searcher: WebSearcher) -> None:
        self.task_list = []
        self.task_index = 0
        self.start_task = None
        self.cmd_list = []
        self.cmd_index = 0
        self.helper = helper
        self.requester = requester
        self.searcher = searcher
        self.index = 0

        self.browser = WebBrowser()
        self.summator = Summator()

        self.need_human_response = False
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

    def add_new_task(self, prompt):
        img_path = "output/img.png"

        if not os.path.exists(img_path):
            img_path = "examples/test.png"


        if self.need_human_response:
            self.need_human_response = False
            return "", "", img_path
        if len(self.task_list) > 0:
            f = graphviz.Digraph(comment='The Test Table')
            
            for task in self.task_list:
                f.node( task.getName(), task.getLabel())
            
            for task in self.task_list:
                for child in task.childs:
                    f.edge(task.getName(), child.getName())
            img_path = "output/img"
            f.render(filename=img_path,view=False,format='png')
            img_path += ".png"
            del f

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
            log += task.task_creation_result
            out += str(task) + '\n'
            out += "Task description:\n"
            out += task.task_description
            return out, log, img_path
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
            for task in self.task_list:
                if not task.completeTask():
                    all_task_completed = False
                else:
                    print("task complete=",str(task))

        if all_task_completed:
            log += "All task complete\n"
            return out, log, img_path
            # if self.start_task:
            #     self.start_task.completeTask()

        # for task in self.task_list[:]:
        #     if task.isSolved():
        #         self.task_list.remove(task)

        if len(self.task_list) == 0:
            log += "Start command\n"
            # start_task = ChatGPTTask(reqhelper=self.helper, requester=self.requester, prompt=prompt)
            # start_task = PresentationTask(reqhelper=self.helper, requester=self.requester, prompt=prompt)
            start_task = PresentationTask(TaskDescription(prompt=prompt, helper=self.helper, requester=self.requester))
            self.task_list.append(start_task)
            out += "Task description:\n"
            log += start_task.task_creation_result
            out += start_task.task_description
            self.start_task = start_task
            return out, log, img_path

           # start_task = InformationTask( None, self.helper, self.requester, prompt)
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
        return out, log, img_path


def gr_body(request) -> None:
    manager = Manager(RequestHelper(), TestRequester(), GoogleApiSearcher())
    with gr.Blocks() as demo:
        input = gr.Textbox(label="Input", lines=4, value=request)
        add_new_btn = gr.Button(value="I don't care, Let's do this")

        # init = gr.Textbox(label="Init", lines=4)
        prompt = gr.Textbox(label="Prompt", lines=4)
        output = gr.Textbox(label="Output Box")
        # endi = gr.Textbox(label="Endi", lines=4)
        # question = gr.Textbox(label="Question", lines=4)
        # search = gr.Textbox(label="Search", lines=4)
        # userinput = gr.Textbox(label="User Input", lines=4)
        graph_img = gr.Image()

        add_new_btn.click(fn=manager.add_new_task, inputs=[input], outputs=[
                          prompt, output, graph_img], api_name='add_new_task')
    demo.launch()


def main() -> None:
    prompt = "Bissness presentation for investors. My idea is automation of presentation. You just type your idea then software propose your steps to create presentation and try to automatize it."

    if 1:
        print("Start gradio application")
        gr_body(prompt)
        return

    print("Start console application")


if __name__ == "__main__":
    main()
