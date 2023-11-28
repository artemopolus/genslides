from abc import ABCMeta, abstractmethod

import genslides.task.base as base

class SimpleCommand(metaclass=ABCMeta):
    def __init__(self, input : base.TaskDescription ) -> None:
        self.input = input

    @abstractmethod
    def execute(self) -> None:
        return None, 'stay'

    @abstractmethod
    def unexecute(self) -> None:
        return None, 'stay'
