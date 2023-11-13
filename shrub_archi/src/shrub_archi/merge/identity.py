from typing import Optional, Dict

from dataclasses import dataclass


@dataclass
class Identity:
    unique_id: str
    name: str
    classification: str = None
    description: Optional[str] = None
    source: Optional[str] = None


Identities = Dict[str, Identity]
