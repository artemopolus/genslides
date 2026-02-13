from genslides.commands.simple import SimpleCommand


class LinkCommand(SimpleCommand):
    def __init__(self, input) -> None:
        super().__init__(input)
        self.name = "link"

    def execute(self) -> None:
        task_in = self.input.target
        trg = self.input.parent
        task_in.createLinkToTask(trg)
        return super().execute()
    
    def unexecute(self) -> None:
        task = self.input.target
        task.removeLinkToTask()
        return super().unexecute()
    
class UnLinkCommand(SimpleCommand):
    def __init__(self, input) -> None:
        super().__init__(input)
        self.name = "unlink"

    def execute(self) -> None:
        task = self.input.target
        self.holders = task.getHoldGarlands()
        self.parts = task.getGarlandPart()
        task.removeLinkToTask()
        return super().execute()
    
    def unexecute(self) -> None:
        task = self.input.target
        for holder in self.holders:
            holder.createLinkToTask(task)
            # task.createLinkToTask(holder)
        for part in self.parts:
            # part.createLinkToTask(task)
            task.createLinkToTask(part)

        return super().unexecute()
