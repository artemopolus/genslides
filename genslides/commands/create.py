from genslides.commands.simple import SimpleCommand

import genslides.utils.reqhelper as ReqHelper
import genslides.utils.request as Requester

class CreateCommand(SimpleCommand):
   def __init__(self, description ) -> None:
      super().__init__(description.method)
      self.description = description
   def execute(self):
      print("execute: Create " + str(self.method))
      return self.method( self.description )
   def unexecute(self):
      pass
            
