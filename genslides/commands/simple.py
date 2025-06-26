from abc import ABCMeta, abstractmethod

import genslides.task.base as base
import genslides.utils.savedata as Save

class SimpleCommand(metaclass=ABCMeta):
    def __init__(self, input : base.TaskDescription ) -> None:
        self.input = input
        self.name = "simple"
        self.time = Save.getTimeForSaving()
        self.task : base.BaseTask = None

    def getName(self):
        task_name = "None" if self.task == None else self.task.getName()
        return f"{self.name} ({self.time}): {task_name}"

    @abstractmethod
    def execute(self) -> None:
        return None, 'stay'

    @abstractmethod
    def unexecute(self) -> None:
        return None, 'stay'
