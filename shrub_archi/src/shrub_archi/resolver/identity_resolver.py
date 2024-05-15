import concurrent.futures
import itertools
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple, Optional

from shrub_archi.model.model import Identity, Views
from shrub_archi.repository.repository import Repository, RepositoryFilter


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

    def __hash__(self):
        return hash((self.identity1.unique_id, self.identity2.unique_id))


@dataclass
class ResolverResult:
    score: int
    rule: str
    # can be True, False or None
    manual_verification: bool = None
    MAX_EQUAL_SCORE: int = 100

    def has_max_score(self):
        return self.score >= self.MAX_EQUAL_SCORE


class IdentityResolver(ABC):
    def __init__(self, parent: "IdentityResolver" = None):
        self.resolver_chain: List[IdentityResolver] = [self]
        if parent:
            self.resolver_chain.append(*parent.resolver_chain)

    def resolve(self, identity1: Identity, identity2: Identity) -> ResolverResult:
        result = None
        for cmp in self.resolver_chain:
            result = cmp.do_resolve(identity1, identity2)
            if result:
                break

        return result

    @abstractmethod
    def do_resolve(self, identity1: Identity, identity2: Identity) -> ResolverResult:
        ...


class RepositoryResolver:
    def classification_resolve(self, ids1: List[ResolvedIdentity], ids2: List[ResolvedIdentity],
                               comparator: IdentityResolver):
        result = []
        for id1, id2 in [(id1, id2) for id1, id2 in itertools.product(ids1, ids2)]:
            compare_result = comparator.resolve(id1, id2)
            if compare_result:
                resolved_id = ResolvedIdentity(identity1=id1, identity2=id2, resolver_result=compare_result)
                result.append(resolved_id)
        return result

    def resolve(self, repo1: Repository, repo2: Repository, repo2_filter: RepositoryFilter = None,
                comparator: IdentityResolver = None):
        result = []

        def to_map(repository: Repository, repo_filter: RepositoryFilter = None):
            # build map from repository items based on filter and identities
            map_ids1 = {}
            for k, g in itertools.groupby(repository.filter(repo_filter),
                    lambda id: id.classification):
                if k not in map_ids1:
                    map_ids1[k] = list(g)
                else:
                    map_ids1[k] += list(g)
            return map_ids1

        map1 = to_map(repo1)
        map2 = to_map(repo2, repo2_filter)
        with concurrent.futures.ThreadPoolExecutor() as exec:
            futures = []
            for group1 in map1:
                if group1 in map2:
                    futures.append(exec.submit(self.classification_resolve, map1[group1], map2[group1], comparator))
            for future in concurrent.futures.as_completed(futures):
                result += future.result()
        return result


def resolutions_is_resolved(resolutions: List[ResolvedIdentity], id2: str) -> Tuple[bool, Optional[bool]]:
    found, result = resolutions_get_resolved_identity(resolutions, id2)
    if result:
        return True, result.resolver_result.manual_verification
    return found, result


def resolutions_get_resolved_identity(resolutions: List[ResolvedIdentity], id2: str) -> Tuple[bool, Optional[ResolvedIdentity]]:
    result = False, None
    if resolutions:
        for res_id in [res_id for res_id in resolutions if res_id.identity2.unique_id == id2]:
            result = True, res_id
            break
    return result