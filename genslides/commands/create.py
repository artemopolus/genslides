from genslides.commands.simple import SimpleCommand

class CreateCommand(SimpleCommand):
   def __init__(self, tasklist, parent, method) -> None:
      super().__init__()
      self.list = tasklist
      self.parent = parent
      self.method = method
   def execute(self):
      print("execute: Create " + str(self.method))
      return self.method(self.parent)
      # self.list.append(slide)
   def unexecute(self):
      pass
            
