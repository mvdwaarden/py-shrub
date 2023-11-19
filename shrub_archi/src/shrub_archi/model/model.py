from typing import Optional, Dict, Tuple, List

from dataclasses import dataclass


@dataclass
class Identity:
    unique_id: str
    name: str
    classification: str = None
    description: Optional[str] = None
    source: Optional[str] = None

    def __hash__(self):
        return super().__hash__()


@dataclass
class View(Identity):
    unique_id: str
    name: str
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


Relations = Dict[str, Relation]
RelationsLookup = Dict[Tuple[str, str], Relation]
Identities = Dict[str, Identity]
Views = Dict[str, View]
