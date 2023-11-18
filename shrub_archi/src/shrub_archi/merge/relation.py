from typing import Dict, Tuple, Optional

from dataclasses import dataclass

from .identity import Identity


@dataclass
class Relation(Identity):
    source_id: Optional[str] = None
    target_id: Optional[str] = None
    source: Optional[Identity] = None
    target: Optional[Identity] = None


Relations = Dict[str, Relation]
RelationsLookup = Dict[Tuple[str, str], Relation]
