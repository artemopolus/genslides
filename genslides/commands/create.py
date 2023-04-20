from genslides.commands.simple import SimpleCommand
import genslides.utils.reqhelper as ReqHelper

class CreateCommand(SimpleCommand):
   def __init__(self, parent, reqhelper : ReqHelper, description, method) -> None:
      super().__init__()
      self.parent = parent
      self.reqhelper = reqhelper
      self.description = description
      self.method = method
   def execute(self):
      print("execute: Create " + str(self.method))
      return self.method( self.parent, self.reqhelper, self.description)
      # self.list.append(slide)
   def unexecute(self):
      pass
            
