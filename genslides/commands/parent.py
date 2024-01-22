from genslides.commands.simple import SimpleCommand
from genslides.task.base import TaskDescription

class ParentCommand(SimpleCommand):
    def __init__(self, input) -> None:
        super().__init__(input)

    def execute(self) -> None:
        input = self.input
        trg = input.target
        info = TaskDescription( prompt=trg.getLastMsgContent(), prompt_tag=trg.getLastMsgRole())
        info.parent = input.parent
        oldpar = trg.parent
        trg.update(info)
        info.parent = oldpar
        self.info = info
        self.trg = trg
        return super().execute()
    
    def unexecute(self) -> None:
        self.trg.update(self.info)
        return super().unexecute()
    
class RemoveParentCommand(SimpleCommand):
    def __init__(self, input) -> None:
        super().__init__(input)

    def execute(self) -> None:
        trg = self.input.target
        oldpar = trg.parent
        info = TaskDescription( prompt=trg.getLastMsgContent(), prompt_tag=trg.getLastMsgRole())
        info.parent = oldpar
        trg.removeParent()
        trg.update()
        self.info = info
        self.trg = trg

        return super().execute()
    
    def unexecute(self) -> None:
        self.trg.update(self.info)
        return super().unexecute()