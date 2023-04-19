from abc import ABCMeta, abstractmethod

class SimpleCommand(metaclass=ABCMeta):
    @abstractmethod
    def execute(self)->None:
       pass
    @abstractmethod
    def unexecute(self)->None:
       pass
    