import genslides.commands.simple as SimpleCommand
from genslides.task.presentation import PresentationTask
from genslides.task.presentation import SlideTask

class createSlide(SimpleCommand):
   def __init__(self, list, parent : PresentationTask) -> None:
      super().__init__()
      self.list = list
      self.parent = parent
   def execute(self):
      slide = SlideTask(self.parent)
      list.append(slide)
      pass
   def unexecute(self):
      pass
            
