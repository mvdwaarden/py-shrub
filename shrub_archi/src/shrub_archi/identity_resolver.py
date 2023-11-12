import itertools
import json
import os
from abc import ABC, abstractmethod
from difflib import SequenceMatcher
from enum import Enum
from typing import Dict
from typing import Optional, List, Tuple

from dataclasses import dataclass

import shrub_util.core.logging as logging
from shrub_archi.identity import Identity
from shrub_archi.repository import Repository


class ResolvedIdentityAction(Enum):
    REPLACE_TARGET_ID = 1
    REPLACE_TARGET_NAME = 2
    REPLACE_TARGET_DESCRIPTION = 4

    def part_of(self, stacked_action: int):
        return stacked_action & self.value > 0


@dataclass
class ResolvedIdentity:
    identity1: "Identity"
    identity2: "Identity"
    compare_result: "CompareResult"


@dataclass
class CompareResult:
    score: int
    rule: str
    # can be True, False or None
    resolved_result: bool = False
    MAX_EQUAL_SCORE: int = 100

    def has_max_score(self):
        return self.score >= self.MAX_EQUAL_SCORE


class CompareResolutionStore:
    def __init__(self, location: str):
        self.location = location
        self._resolutions: Dict[str, Tuple[str, bool]] = None

    @property
    def resolutions(self):
        return self._resolutions

    @resolutions.setter
    def resolutions(self, resolved_identities: List[ResolvedIdentity]):
        self._resolutions = {}
        for res_id in resolved_identities:
            self._resolutions[res_id.identity1.unique_id] = (
                res_id.identity2.unique_id, res_id.compare_result.resolved_result)

    def _get_resolution_file(self, name) -> str:
        return os.path.join(self.location,
                            f"{name if name else 'resolved_identities'}.json")

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
                    self._resolutions = json.load(ifp)
            except Exception as ex:
                logging.get_logger().error(
                    f"problem reading resolution file {self._get_resolution_file(name)}",
                    ex=ex)
                self.resolutions = {}
        return self.resolutions

    def write(self, name: str):
        try:
            with open(self._get_resolution_file(name), "w") as ofp:
                json.dump(self.resolutions, ofp)
        except Exception as ex:
            logging.get_logger().error(
                f"problem writing resolution file {self._get_resolution_file}", ex=ex)

    def resolution(self, id1, id2):
        if self.resolutions and id1 in self.resolutions and id == self.resolutions[id1][
            0]:
            return self.resolutions[id1][1]
        else:
            return None

    def is_resolved(self, id2):
        if self.resolutions:
            result = None
            for verified in [value[1] for value in self.resolutions.values() if
                             value[0] == id2]:
                result = verified
                break
        else:
            result = None
        return result

    def apply_to(self, resolved_ids: List[ResolvedIdentity]):
        for id1, (id2, verified_check_result) in self.resolutions.items():
            res_id = next(res_id for res_id in resolved_ids if
                          res_id.identity1.unique_id == id1 and res_id.identity2.unique_id == id2)
            if res_id:
                res_id.compare_result.resolved_result = verified_check_result
                res_id.compare_result.rule = CompareResolutionStoreComparator.RULE


class Comparator(ABC):
    def __init__(self, parent: "Comparator" = None):
        self.compare_chain: List[Comparator] = [self]
        if parent:
            self.compare_chain.append(*parent.compare_chain)

    def compare(self, identity1: Identity,
                identity2: Identity) -> CompareResult:
        result = None
        for cmp in self.compare_chain:
            result = cmp.do_compare(identity1, identity2)
            if result:
                break

        return result

    @abstractmethod
    def do_compare(self, identity1: Identity,
                   identity2: Identity) -> CompareResult:
        pass


class CompareResolutionStoreComparator(Comparator):
    RULE = "ID_RESOLUTION_FILE"

    def __init__(self, resolution_store: CompareResolutionStore):
        super().__init__()
        self.resolution_store = resolution_store

    def do_compare(self, identity1: Identity,
                   identity2: Identity) -> CompareResult:
        result: Optional[CompareResult] = None
        if self.resolution_store:
            resolved = self.resolution_store.resolution(
                identity1.unique_id, identity2.unique_id)
            if resolved is not None:
                result = CompareResult(
                    score=CompareResult.MAX_EQUAL_SCORE,
                    rule=self.RULE,
                    resolved_result=True)
        return result


class NaiveIdentityComparator(Comparator):
    def __init__(self, cutoff_score: int = 80, parent: Comparator = None):
        super().__init__(parent)
        self.cutoff_score = cutoff_score

    def do_compare(self, identity1: Identity, identity2: Identity) -> Optional[
        CompareResult]:
        result = None
        if identity1.unique_id == identity2.unique_id:
            result = CompareResult(
                score=CompareResult.MAX_EQUAL_SCORE, rule="ID_EXACT_RULE",
                resolved_result=True)
        elif identity1.classification == identity2.classification:
            if identity1.name == identity2.name:
                result = CompareResult(
                    score=CompareResult.MAX_EQUAL_SCORE + 10,
                    rule="NAME_EXACT_RULE")
            else:
                name_score = int(SequenceMatcher(a=identity1.name,
                                                 b=identity2.name).ratio() * CompareResult.MAX_EQUAL_SCORE)
                description_score = 0
                if identity1.description and identity2.description and len(
                        identity1.description) > 10 and len(identity2.description) > 10:
                    description_score = int(SequenceMatcher(a=identity1.description,
                                                            b=identity2.description).ratio() * CompareResult.MAX_EQUAL_SCORE)
                if name_score > 0 and name_score > description_score:
                    result = CompareResult(score=name_score,
                                           rule="NAME_CLASS_RULE")
                elif description_score > 0:
                    result = CompareResult(score=description_score,
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
        for id1, id2 in [(id1, id2) for id1, id2 in
                         itertools.product(ids1.identities, ids2.identities)]:
            compare_result = comparator.compare(id1, id2)
            if compare_result:
                resolved_id = ResolvedIdentity(identity1=id1, identity2=id2,
                                               compare_result=compare_result)
                if cache:
                    self.cache_resolved_ids.append(resolved_id)
                yield resolved_id
