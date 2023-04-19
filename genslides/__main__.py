from genslides.task.presentation import PresentationTask
from genslides.task.presentation import SlideTask 
from genslides.commands.simple import SimpleCommand


def main() -> None:
       print("Start console")
       task_list = []
       cmd_list = []
       task_list.append(SlideTask(None))
       task_list.append(PresentationTask("Name", "Some"))

       for task in task_list:
              print("Ping")
              cmd = task.createSubTask()
              if(cmd != None):
                     cmd_list.append(SimpleCommand(cmd))

       for cmd in cmd_list:
              cmd.execute()

       print("Done")
    

if __name__ == "__main__":
      main()
      
