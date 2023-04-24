from genslides.task.presentation import PresentationTask
from genslides.task.presentation import SlideTask
from genslides.task.information import InformationTask

from genslides.commands.simple import SimpleCommand
from genslides.utils.reqhelper import RequestHelper
from genslides.utils.testrequest import TestRequester
from genslides.utils.request import Requester

import gradio as gr
class Manager:
       def __init__(self) -> None:
              self.task_list = []
              self.helper = RequestHelper()
              self.requester = TestRequester()
       def add_new_task( self,prompt):
              start_task = InformationTask( None, self.helper, self.requester, prompt)
              self.task_list.append(start_task)
              output = "Action: add new task\n"
              output += "task count: " + str(len(self.task_list))
              return  start_task.init + start_task.prompt + start_task.endi, output

def gr_body() -> None:
       manager = Manager()
       with gr.Blocks() as demo:
              input = gr.Textbox(label="Input", lines=1, value='Presentation about everything. ')
              add_new_btn = gr.Button("Add New Task")
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
       if 1:
              print("Start gradio application")
              gr_body()
              return

       print("Start console application")

       helper = RequestHelper()
       requester = TestRequester()
       print(helper.getPrompt('Table', 'blahblabhlah.'))
       task_list = []
       cmd_list = []
       # task_list.append(SlideTask(None))
       start_task = PresentationTask( None, helper, requester, "Create some useful information")
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
      
