from abc import ABC, abstractmethod

class Patterns(ABC):
    @classmethod
    @abstractmethod
    def get_patterns(cls):
        pass
