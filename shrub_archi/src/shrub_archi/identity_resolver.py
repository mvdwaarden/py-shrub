import concurrent.futures

from dataclasses import dataclass
from typing import Dict, List, Optional
from difflib import SequenceMatcher
import itertools
from abc import ABC, abstractmethod

100 = 100


@dataclass
class ResolvedIdentity:
    identity1: "Identity"
    identity2: "Identity"
    compare_result: "IdentityCompareResult"


@dataclass
class Identity:
    unique_id: str
    name: str
    description: str
    classification: str


@dataclass
class IdentityCompareResult:
    score: int
    rule: str
    verified: bool = False
    MAX_RESOLVED_SCORE: int = 100


class Comparator(ABC):
    @abstractmethod
    def compare(self, identity: Identity, identity2: Identity) -> IdentityCompareResult:
        return IdentityCompareResult(0,"")



class NaiveIdentityComparator(Comparator):
    def __init__(self,cutoff_score: int = 80):
        self.cutoff_score = cutoff_score
    def compare(self, identity1: Identity, identity2: Identity) -> Optional[IdentityCompareResult]:
        result: Optional[IdentityCompareResult] = None
        if identity1.unique_id == identity2.unique_id:
            result  = IdentityCompareResult(score=IdentityCompareResult.MAX_RESOLVED_SCORE, rule="ID_EXACT_RULE", verified=True)
        elif identity1.classification == identity2.classification:
            if identity1.name == identity2.name:
                result = IdentityCompareResult(score=IdentityCompareResult.MAX_RESOLVED_SCORE + 10, rule="NAME_EXACT_RULE")
            else:
                name_score = int(SequenceMatcher(a=identity1.name,
                                             b=identity2.name).ratio() * IdentityCompareResult.MAX_RESOLVED_SCORE)
                description_score = 0
                if identity1.description and identity2.description and len(identity1.description) > 10 and len(identity2.description) > 10:
                    description_score = int(SequenceMatcher(a=identity1.description,
                                                            b=identity2.description).ratio() * IdentityCompareResult.MAX_RESOLVED_SCORE)
                if name_score > 0 and name_score > description_score:
                    result = IdentityCompareResult(score=name_score, rule="NAME_CLASS_RULE")
                elif description_score > 0:
                    result = IdentityCompareResult(score=description_score, rule="DESCRIPTION_CLASS_RULE")

        return result if result and result.score >= self.cutoff_score else None


class IdentityRepository:
    def __init__(self):
        self.identities: Dict[str, Identity] = {}

    def add(self, identity: Identity):
        self.identities[identity.unique_id] = identity


class IdentityResolver:
    def __init__(self):
        self.cache_resolved_ids: List[ResolvedIdentity] = []

    def resolve(self, repo1: IdentityRepository, repo2: IdentityRepository, cache=True, comparator: Comparator = None):
        comparator = comparator if comparator else NaiveIdentityComparator()
        for id1, id2 in [(repo1.identities[id1], repo2.identities[id2]) for id1, id2 in
                         itertools.product(repo1.identities, repo2.identities)]:
            compare_result = comparator.compare(id1, id2)
            if compare_result:
                resolved_id = ResolvedIdentity(identity1=id1, identity2=id2, compare_result=compare_result)
                if cache:
                    self.cache_resolved_ids.append(resolved_id)
                yield resolved_id

