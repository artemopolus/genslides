from abc import ABCMeta, abstractmethod

class SimpleCommand(metaclass=ABCMeta):
    def __init__(self, input ) -> None:
        self.input = input

    @abstractmethod
    def execute(self) -> None:
        return None

    @abstractmethod
    def unexecute(self) -> None:
        pass
