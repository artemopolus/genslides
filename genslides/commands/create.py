from genslides.commands.simple import SimpleCommand


class CreateCommand(SimpleCommand):
   def __init__(self, description ) -> None:
      super().__init__(description)
      self.task = None
   def execute(self):
      # print("execute: Create " + str(self.input.method))
      self.task = self.input.method( self.input )
      return self.task, 'create'
   
   def unexecute(self):
      return self.task, 'delete'

class RemoveCommand(SimpleCommand):
   def __init__(self, input) -> None:
      super().__init__(input)

   def execute(self) -> None:
      task = self.input.target
      self.task = task
      self.parent = task.parent
      self.childs = task.getChilds()
      self.holders = task.getHoldGarlands()
      task.beforeRemove()
      
      return task, 'delete'
  
   
   def unexecute(self) -> None:
      task = self.task
      task.setParent(self.parent)
      for holder in self.holders:
         task.createLinkToTask(holder)

      for child in self.childs:
         child.setParent(task)

      task.afterRestoration()

      return task, 'create'
            
