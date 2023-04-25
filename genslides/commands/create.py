from genslides.commands.simple import SimpleCommand
import genslides.utils.reqhelper as ReqHelper
import genslides.utils.request as Requester

class CreateCommand(SimpleCommand):
   def __init__(self, parent, reqhelper : ReqHelper, requester : Requester, description: str , method) -> None:
      super().__init__(method)
      self.parent = parent
      self.reqhelper = reqhelper
      self.requester = requester
      self.description = description
   def execute(self):
      print("execute: Create " + str(self.method))
      return self.method( self.parent, self.reqhelper, self.requester, self.description)
      # self.list.append(slide)
   def unexecute(self):
      pass
            
