from genslides.commands.simple import SimpleCommand


class CreateCommand(SimpleCommand):
   def __init__(self, description ) -> None:
      super().__init__(description)
   def execute(self):
      print("execute: Create " + str(self.input.method))
      return self.input.method( self.input )
   def unexecute(self):
      pass

class RemoveCommand(SimpleCommand):
   def __init__(self, input) -> None:
      super().__init__(input)

   def execute(self) -> None:
      task = self.input.target
      task.beforeRemove()
      return None
  
   
   def unexecute(self) -> None:
      return super().unexecute()
            
