import concurrent.futures
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
from shrub_archi.merge.repository import CoArchiRepository


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
        self._resolutions: Dict[Tuple[str, str], bool] = None

    @property
    def resolutions(self):
        return self._resolutions

    @resolutions.setter
    def resolutions(self, resolved_identities: List[ResolvedIdentity]):
        self._resolutions = {}
        for res_id in resolved_identities:
            self._resolutions[res_id.identity1.unique_id, res_id.identity2.unique_id] = res_id.resolver_result.manual_verification

    def _get_resolution_file(self, name) -> str:
        return os.path.join(self.location,
                            f"{name if name else 'resolved_identities'}.json")

    def _read_from_string(self, resolutions: str):
        self._resolutions = {}
        for id1, id2, manually_verified in json.loads(resolutions):
            self._resolutions[(id1, id2)] = manually_verified

    def read_from_string(self, resolutions: str):
        if not self._resolutions:
            try:
                self._read_from_string(resolutions)
            except Exception as ex:
                logging.get_logger().error(
                    f"problem reading resolutions",
                    ex=ex)
        return self.resolutions

    def read(self, name: str):
        if not self._resolutions:
            try:
                with open(self._get_resolution_file(name), "r") as ifp:
                    self._read_from_string(ifp.read())
            except Exception as ex:
                logging.get_logger().error(
                    f"problem reading resolution file {self._get_resolution_file(name)}",
                    ex=ex)
                self._resolutions = {}
        return self.resolutions

    def write(self, name: str):
        try:
            tmp = []
            for (id1, id2), value in self.resolutions.items():
                tmp.append((id1, id2, value))
            with open(self._get_resolution_file(name), "w") as ofp:
                json.dump(tmp, ofp)
        except Exception as ex:
            logging.get_logger().error(
                f"problem writing resolution file {self._get_resolution_file}", ex=ex)

    def resolution(self, id1, id2):
        if self.resolutions and (id1,id2) in self.resolutions:
            return self.resolutions[id1,id2]
        else:
            return None

    def is_resolved(self, id2):
        result = False, None
        if self.resolutions:
            for verified in [value for (_, id2_check), value in self.resolutions.items() if
                             id2 == id2_check]:
                result = True, verified
                break
        return result

    def apply_to(self, resolved_ids: List[ResolvedIdentity]):
        for (id1, id2) ,manual_verification in self.resolutions.items():
            for res_id in [res_id for res_id in resolved_ids if
                           res_id.identity1.unique_id == id1 and res_id.identity2.unique_id == id2]:
                res_id.resolver_result.manual_verification = manual_verification
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
                score=ResolverResult.MAX_EQUAL_SCORE + 10, rule="ID_EXACT_RULE")
        elif identity1.classification == identity2.classification:
            if not identity1.name or not identity2.name:
                ...
            elif identity1.name == identity2.name:
                result = ResolverResult(
                    score=ResolverResult.MAX_EQUAL_SCORE + 10,
                    rule="NAME_EXACT_RULE")
            else:
                name_score = 0
                if len(identity1.name) > 10 and len(identity2.name) > 10:
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
    def classification_resolve(self, ids1: List[ResolvedIdentity],
                               ids2: List[ResolvedIdentity],
                               comparator: IdentityResolver):
        result = []
        for id1, id2 in [(id1, id2) for id1, id2 in
                         itertools.product(ids1, ids2)]:
            compare_result = comparator.resolve(id1, id2)
            if compare_result:
                resolved_id = ResolvedIdentity(identity1=id1,
                                               identity2=id2,
                                               resolver_result=compare_result)
                result.append(resolved_id)
        return result

    def resolve(self, repo1: CoArchiRepository, repo2: CoArchiRepository,
                comparator: IdentityResolver = None):
        naive = False
        result = []

        def to_map(repository: CoArchiRepository):
            map_ids1 = {}
            for k, g in itertools.groupby(repo1.identities,
                                          lambda id: id.classification):
                if k not in map_ids1:
                    map_ids1[k] = list(g)
                else:
                    map_ids1[k] += list(g)
            return map_ids1

        map1 = to_map(repo1)
        map2 = to_map(repo2)
        with concurrent.futures.ProcessPoolExecutor() as exec:
            futures = []
            for group1 in map1:
                if group1 in map2:
                    futures.append(
                        exec.submit(self.classification_resolve, map1[group1],
                                    map2[group1],
                                    comparator))
            for future in concurrent.futures.as_completed(futures):
                result += future.result()
        return result
