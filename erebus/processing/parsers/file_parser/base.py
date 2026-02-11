from abc import ABC, abstractmethod

class BaseFileParser(ABC):

    technique: str = None
    extensions: tuple[str, ...] = ()

    @abstractmethod
    def can_parse(self, url: str) -> bool:
        pass

    @abstractmethod
    def extract_text(self, content: bytes) -> str:
        pass

    def parse(self, url: str, content: bytes) -> str:
        return self.extract_text(content)