from genslides.commands.simple import SimpleCommand

class ParentCommand(SimpleCommand):
    def __init__(self, input) -> None:
        super().__init__(input)

    def execute(self) -> None:
        input = self.input.copy()
        trg = input.target
        input.target = None
        trg.update(input)
        return super().execute()
    
    def unexecute(self) -> None:
        return super().unexecute()
    
class RemoveParentCommand(SimpleCommand):
    def __init__(self, input) -> None:
        super().__init__(input)

    def execute(self) -> None:
        task = input.target
        task.removeParent()
        task.update()

        return super().execute()
    
    def unexecute(self) -> None:
        return super().unexecute()