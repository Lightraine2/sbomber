from abc import ABC, abstractmethod

class BaseParser(ABC):
    @abstractmethod
    def get_dependency_file_name(self):
        pass

    @abstractmethod
    def parse_dependencies(self, file_content):
        pass