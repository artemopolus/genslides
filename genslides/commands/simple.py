from abc import ABCMeta, abstractmethod


class SimpleCommand(metaclass=ABCMeta):
    def __init__(self, method) -> None:
        self.method = method

    @abstractmethod
    def execute(self) -> None:
        pass

    @abstractmethod
    def unexecute(self) -> None:
        pass
