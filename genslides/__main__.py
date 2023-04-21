from genslides.task.presentation import PresentationTask
from genslides.task.presentation import SlideTask 
from genslides.commands.simple import SimpleCommand
from genslides.utils.reqhelper import RequestHelper
from genslides.utils.testrequest import TestRequester

def main() -> None:
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
      
