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
from shrub_archi.merge.identity import Identity
from shrub_archi.merge.repository import Repository


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
    resolver_result: "ResolverResult"


@dataclass
class ResolverResult:
    score: int
    rule: str
    # can be True, False or None
    manual_verification: bool = None
    MAX_EQUAL_SCORE: int = 100

    def has_max_score(self):
        return self.score >= self.MAX_EQUAL_SCORE


class ResolutionStore:
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
                res_id.identity2.unique_id, res_id.resolver_result.manual_verification)

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
                self._resolutions = {}
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
                self._resolutions = {}
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
            for res_id in [res_id for res_id in resolved_ids if
                           res_id.identity1.unique_id == id1 and res_id.identity2.unique_id == id2]:
                res_id.resolver_result.manual_verification = verified_check_result
                res_id.resolver_result.rule = "ID_RESOLUTION_FILE"
                break


class IdentityResolver(ABC):
    def __init__(self, parent: "IdentityResolver" = None):
        self.resolver_chain: List[IdentityResolver] = [self]
        if parent:
            self.resolver_chain.append(*parent.resolver_chain)

    def resolve(self, identity1: Identity,
                identity2: Identity) -> ResolverResult:
        result = None
        for cmp in self.resolver_chain:
            result = cmp.do_resolve(identity1, identity2)
            if result:
                break

        return result

    @abstractmethod
    def do_resolve(self, identity1: Identity,
                   identity2: Identity) -> ResolverResult:
        pass


class NaiveIdentityResolver(IdentityResolver):
    def __init__(self, cutoff_score: int = 80, parent: IdentityResolver = None):
        super().__init__(parent)
        self.cutoff_score = cutoff_score

    def do_resolve(self, identity1: Identity, identity2: Identity) -> Optional[
        ResolverResult]:
        result = None
        if identity1.unique_id == identity2.unique_id:
            result = ResolverResult(
                score=ResolverResult.MAX_EQUAL_SCORE, rule="ID_EXACT_RULE",
                manual_verification=True)
        elif identity1.classification == identity2.classification:
            if identity1.name == identity2.name:
                result = ResolverResult(
                    score=ResolverResult.MAX_EQUAL_SCORE + 10,
                    rule="NAME_EXACT_RULE")
            else:
                name_score = int(SequenceMatcher(a=identity1.name,
                                                 b=identity2.name).ratio() * ResolverResult.MAX_EQUAL_SCORE)
                description_score = 0
                if identity1.description and identity2.description and len(
                        identity1.description) > 10 and len(identity2.description) > 10:
                    description_score = int(SequenceMatcher(a=identity1.description,
                                                            b=identity2.description).ratio() * ResolverResult.MAX_EQUAL_SCORE)
                if name_score > 0 and name_score > description_score:
                    result = ResolverResult(score=name_score,
                                            rule="NAME_CLASS_RULE")
                elif description_score > 0:
                    result = ResolverResult(score=description_score,
                                            rule="DESCRIPTION_CLASS_RULE")

        return result if result and result.score >= self.cutoff_score else None


class RepositoryResolver:
    def resolve(self, ids1: Repository, ids2: Repository,
                comparator: IdentityResolver = None):
        for id1, id2 in [(id1, id2) for id1, id2 in
                         itertools.product(ids1.identities, ids2.identities)]:
            compare_result = comparator.resolve(id1, id2)
            if compare_result:
                resolved_id = ResolvedIdentity(identity1=id1, identity2=id2,
                                               resolver_result=compare_result)
                yield resolved_id