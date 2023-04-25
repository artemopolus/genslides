from genslides.task.presentation import PresentationTask
from genslides.task.presentation import SlideTask
from genslides.task.information import InformationTask

from genslides.utils.reqhelper import RequestHelper
from genslides.utils.testrequest import TestRequester
from genslides.utils.request import Requester
from genslides.utils.searcher import WebSearcher
from genslides.utils.searcher import GoogleApiSearcher

import gradio as gr
class Manager:
       def __init__(self, helper : RequestHelper, requester : Requester, searcher : WebSearcher) -> None:
              self.task_list = []
              self.task_index = 0
              self.curr_task = None
              self.cmd_list = []
              self.cmd_index = 0
              self.helper = helper
              self.requester = requester
              self.searcher = searcher
              self.index = 0
       def add_new_task( self, prompt):
              self.index += 1
              if self.curr_task != None:
                     output = 'List of command:\n'
                     index = 1
                     cmd = self.curr_task.getCmd()
                     if cmd is None:
                            self.curr_task = None
                     else:
                            self.cmd_list.append(cmd)
                     for cmd in self.cmd_list:
                            output += str(index) + '. ' + str(cmd.method)
                            index += 1
                     return output, 'id[' + str(self.index) + '] Create command'
              elif len(self.cmd_list) == 0:
                     start_task = InformationTask( None, self.helper, self.requester, prompt)
                     request = start_task.init + start_task.prompt + start_task.endi
                     responses = self.requester.getResponse(request)
                     # here search
                     log = 'id[' + str(self.index) + '] Evaluation of prompt\n'
                     links = []
                     for resp in responses:
                            search_list = self.searcher.getSearchs(resp.info)
                            for sr in search_list:
                                   links.append(sr)
                                   log += sr + '\n'
                     #evaluate search results => links
                     self.curr_task = start_task
                     return start_task.init + start_task.prompt + start_task.endi, log
              elif self.task_index < len(self.task_list):
                     self.task_index += 1
                     self.curr_task = self.task_list[self.task_index]
                     log = 'id[' + str(self.index) + '] Next task\n'
                     return str(task), log
              elif self.task_index  + 1 > len(self.task_list):
                     index = 0
                     self.task_index = 0
                     for cmd in self.cmd_list:
                            task = cmd.execute()
                            if(task != None):
                                   self.task_list.append(task)
                                   index += 1
                     log = 'id[' + str(self.index) + '] Created task: ' + str(index) + '\n'

                           
              out = 'tasks: ' + str(len(self.task_list)) + '\n' 
              out += 'task index: ' + str(len(self.task_index)) + '\n' 
              out = 'cmds: ' + str(len(self.cmd_list)) + '\n' 
              out += 'cmd index: ' + str(len(self.cmd_index)) + '\n' 
              out += 'current task: ' + str(self.curr_task)
              return  out, 'id[' + str(self.index) + '] Unknown action'

def gr_body(request) -> None:
       manager = Manager(RequestHelper(),TestRequester(), GoogleApiSearcher())
       with gr.Blocks() as demo:
              input = gr.Textbox(label="Input", lines=1, value=request)
              add_new_btn = gr.Button(value= "I don't care, Let's do this")

              output = gr.Textbox(label="Output Box")
              # init = gr.Textbox(label="Init", lines=4)
              prompt = gr.Textbox(label="Prompt", lines=4)
              # endi = gr.Textbox(label="Endi", lines=4)
              question = gr.Textbox(label="Question", lines=4)
              search = gr.Textbox(label="Search", lines=4)
              userinput = gr.Textbox(label="User Input", lines=4)

              add_new_btn.click(fn=manager.add_new_task, inputs=[input], outputs=[ prompt, output], api_name='add_new_task')
       demo.launch()



def main() -> None:
       prompt = "Bissness presentation for investors. My idea is automation of presentation. You just type your idea then software propose your steps to create presentation and try to automatize it."

       if 1:
              print("Start gradio application")
              gr_body(prompt)
              return

       print("Start console application")

       helper = RequestHelper()
       requester = TestRequester()
       print(helper.getPrompt('Table', 'blahblabhlah.'))
       task_list = []
       cmd_list = []
       # task_list.append(SlideTask(None))
       start_task = PresentationTask( None, helper, requester, prompt)
       task_list.append(start_task)

       print(task_list)

       for task in task_list:
              cmd = task.getCmd()
              if(cmd != None):
                     cmd_list.append(cmd)

       for cmd in cmd_list:
              task = cmd.execute()
              if(task != None):
                     task_list.append(task)

       print("Task list: " + str(len(task_list)))
       for task in task_list:
              print(task)
       print("Cmd list:" + str(len(cmd_list)))
    

if __name__ == "__main__":
      main()
      
