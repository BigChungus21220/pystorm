from abc import ABC, abstractmethod
from typing import Self

type Molang = str

type MolangValue = Molang | int | float | bool
type JSONValue = str | int | float | bool | list[JSONValue] | tuple[JSONValue, ...]
type MolangNumber = Molang | int | float
type MolangInt = Molang | int
type MolangVector3 = tuple[MolangNumber, MolangNumber, MolangNumber]
type MolangVector2 = tuple[MolangNumber, MolangNumber]

class JSONContributions:
    def __init__(self, root: str | None = None) -> None:
        self.root = root
        self.contributions: dict[str, JSONValue] = {}
    
    def contribute(self, path: str, value: JSONValue):
        if self.root != None:
            self.contributions[self.root + "." + path] = value
        else:
            self.contributions[path] = value
    
    def contribute_or_default(self, path: str, value: JSONValue, defaultValue: JSONValue):
        if value != defaultValue:        
            if self.root != None:
                self.contributions[self.root + "." + path] = value
            else:
                self.contributions[path] = value
    
    def merge(self, other: Self):
        self.contributions.update(other.contributions)

class JSONContributor(ABC):
    @abstractmethod
    def contributeJson(self) -> JSONContributions:
        pass
    