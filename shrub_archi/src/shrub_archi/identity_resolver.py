from dataclasses import dataclass
from typing import Dict
from difflib import SequenceMatcher
import itertools
from abc import ABC, abstractmethod
from enum import Enum
import os
from typing import Optional, List
import json
import shrub_util.core.logging as logging
from shrub_archi.identity import Identity

from shrub_archi.repository import Repository


class ResolvedIdentityAction(Enum):
    REPLACE_TARGET_ID = 1
    REPLACE_TARGET_NAME = 2
    REPLACE_TARGET_DESCRIPTION = 4
    def part_of(self,stacked_action: int):
        return stacked_action & self.value > 0




@dataclass
class ResolvedIdentity:
    identity1: "Identity"
    identity2: "Identity"
    compare_result: "IdentityCompareResult"


@dataclass
class IdentityCompareResult:
    score: int
    rule: str
    verified: bool = False
    MAX_RESOLVED_SCORE: int = 100

    def has_max_score(self):
        return self.score == self.MAX_RESOLVED_SCORE

class ResolutionStore:
    def __init__(self, location: str):
        self.resolution_store_location = location
        self._resolutions : Dict[str, str] = None

    @property
    def resolutions(self):
        return self._resolutions
    @resolutions.setter
    def resolutions(self, resolved_identities: List[ResolvedIdentity]):
        self._resolutions = {}
        for res_id in resolved_identities:
            if res_id.compare_result.has_max_score() or res_id.compare_result.verified or res_id.compare_result.score == IdentityCompareResult.MAX_RESOLVED_SCORE:
                self._resolutions[res_id.identity1.unique_id] = res_id.identity2.unique_id

    def _get_resolution_file(self, name) -> str:
        return os.path.join(self.resolution_store_location, f"{name if name else 'resolved_identities'}.json")

    def read_from_string(self, resolutions: str):
        if not self.resolutions:
            try:
                self._resolutions = json.loads(resolutions)
            except Exception as ex:
                logging.get_logger().error(
                    f"problem reading resolutions",
                    ex=ex)
                self.resolutions = {}
        return self.resolutions

    def read(self, name: str):
        if not self.resolutions:
            try:
                with open(self._get_resolution_file(name), "r") as ifp:
                    self.resolutions  = json.load(ifp)
            except Exception as ex:
                logging.get_logger().error(f"problem reading resolution file {self._get_resolution_file(name)}", ex=ex)
                self.resolutions = {}
        return self.resolutions

    def write(self, name: str):
        try:
            with open(self._get_resolution_file(name), "w") as ofp:
                json.dump(self.resolutions, ofp)
        except Exception as ex:
            logging.get_logger().error(
                f"problem writing resolution file {self._get_resolution_file}", ex=ex)


    def is_resolved(self, id1, id2):
        return self.resolutions and id1 in self.resolutions and self.resolutions[id1] == id2


class Comparator(ABC):
    @abstractmethod
    def compare(self, identity: Identity, identity2: Identity) -> IdentityCompareResult:
        return IdentityCompareResult(0, "")


class NaiveIdentityComparator(Comparator):
    def __init__(self, cutoff_score: int = 80, resolution_store: ResolutionStore = None):
        self.cutoff_score = cutoff_score
        self.resolution_store = resolution_store

    def compare(self, identity1: Identity, identity2: Identity) -> Optional[
        IdentityCompareResult]:
        result: Optional[IdentityCompareResult] = None
        if self.resolution_store and self.resolution_store.is_resolved(identity1.unique_id, identity2.unique_id):
            result = IdentityCompareResult(
                score=IdentityCompareResult.MAX_RESOLVED_SCORE, rule="ID_RESOLUTION",
                verified=True)
        elif identity1.unique_id == identity2.unique_id:
            result = IdentityCompareResult(
                score=IdentityCompareResult.MAX_RESOLVED_SCORE, rule="ID_EXACT_RULE",
                verified=True)
        elif identity1.classification == identity2.classification:
            if identity1.name == identity2.name:
                result = IdentityCompareResult(
                    score=IdentityCompareResult.MAX_RESOLVED_SCORE + 10,
                    rule="NAME_EXACT_RULE")
            else:
                name_score = int(SequenceMatcher(a=identity1.name,
                                                 b=identity2.name).ratio() * IdentityCompareResult.MAX_RESOLVED_SCORE)
                description_score = 0
                if identity1.description and identity2.description and len(
                        identity1.description) > 10 and len(identity2.description) > 10:
                    description_score = int(SequenceMatcher(a=identity1.description,
                                                            b=identity2.description).ratio() * IdentityCompareResult.MAX_RESOLVED_SCORE)
                if name_score > 0 and name_score > description_score:
                    result = IdentityCompareResult(score=name_score,
                                                   rule="NAME_CLASS_RULE")
                elif description_score > 0:
                    result = IdentityCompareResult(score=description_score,
                                                   rule="DESCRIPTION_CLASS_RULE")

        return result if result and result.score >= self.cutoff_score else None


class IdentityResolver:
    def __init__(self):
        self.cache_resolved_ids: List[ResolvedIdentity] = []

    @property
    def resolved_ids(self) -> List[ResolvedIdentity]:
        return self.cache_resolved_ids
    def resolve(self, ids1: Repository, ids2: Repository, cache=True,
                comparator: Comparator = None):
        comparator = comparator if comparator else NaiveIdentityComparator()
        for id1, id2 in [(id1, id2) for id1, id2 in
                         itertools.product(ids1.identities, ids2.identities)]:
            compare_result = comparator.compare(id1, id2)
            if compare_result:
                resolved_id = ResolvedIdentity(identity1=id1, identity2=id2,
                                               compare_result=compare_result)
                if cache:
                    self.cache_resolved_ids.append(resolved_id)
                yield resolved_id


