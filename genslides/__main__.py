from genslides.task.presentation import PresentationTask
from genslides.task.presentation import SlideTask 
from genslides.commands.simple import SimpleCommand


def main() -> None:
       print("Start console")
       task_list = []
       cmd_list = []
       # task_list.append(SlideTask(None))
       task_list.append(PresentationTask("Name", "Some"))

       print(task_list)

       for task in task_list:
              print("Ping")
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
      
