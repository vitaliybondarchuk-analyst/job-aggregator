from abc import ABC, abstractmethod
from models import Vacancy

class BaseCollector(ABC):
    source = ""

    @abstractmethod
    def collect(self, terms: list[str]) -> list[Vacancy]:
        raise NotImplementedError
