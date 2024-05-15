from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Tuple, List, Any


class ElementType(Enum):
    BUSINESS_ACTOR = "BusinessActor"
    CONSTRAINT = "Constraint"
    APPLICATION = "Application"


@dataclass
class Identity:
    unique_id: str
    name: str
    classification: str = None
    description: Optional[str] = None
    location: Optional[str] = None
    #data from the source that is used to create the Identity (can be XML element)
    data: Optional[Any] = None

    def __hash__(self):
        return super().__hash__()


@dataclass
class PropertyDefinition(Identity):
    ...


@dataclass
class View(Identity):
    classification: str = None
    description: Optional[str] = None
    source: Optional[str] = None
    referenced_elements: List[str] = None
    referenced_relations: List[str] = None

    def __hash__(self):
        return super().__hash__()


@dataclass
class Relation(Identity):
    source_id: Optional[str] = None
    target_id: Optional[str] = None
    source: Optional[Identity] = None
    target: Optional[Identity] = None

    def __hash__(self):
        return super().__hash__()

    def connects(self, id1: str, id2: str) -> bool:
        return (self.source_id == id1 and self.target_id == id2 or
                self.source_id == id2 and self.target_id == id1)


Relations = Dict[str, Relation]
RelationsLookup = Dict[Tuple[str, str], Relation]
Identities = Dict[str, Identity]
Views = Dict[str, View]
PropertyDefinitions = Dict[str, PropertyDefinition]
