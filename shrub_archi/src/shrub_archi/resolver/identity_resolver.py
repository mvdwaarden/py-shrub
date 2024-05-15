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
    source: "Identity"
    target: "Identity"
    resolver_result: "ResolverResult"

    def __hash__(self):
        return hash((self.source.unique_id, self.target.unique_id))


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

    def resolve(self, source: Identity, target: Identity) -> ResolverResult:
        result = None
        for cmp in self.resolver_chain:
            result = cmp.do_resolve(source, target)
            if result:
                break

        return result

    @abstractmethod
    def do_resolve(self, source: Identity, target: Identity) -> ResolverResult:
        ...


class RepositoryResolver:
    def classification_resolve(
        self,
        source_identities: List[ResolvedIdentity],
        target_identities: List[ResolvedIdentity],
        comparator: IdentityResolver,
    ):
        result = []
        for source, target in [
            (source, target)
            for source, target in itertools.product(
                source_identities, target_identities
            )
        ]:
            compare_result = comparator.resolve(source, target)
            if compare_result:
                resolved_id = ResolvedIdentity(
                    source=source, target=target, resolver_result=compare_result
                )
                result.append(resolved_id)
        return result

    def resolve(
        self,
        target_repo: Repository,
        source_repo: Repository,
        source_filter: RepositoryFilter = None,
        comparator: IdentityResolver = None,
    ):
        result = []

        def to_segmented_map_by_classification(
            repository: Repository, repo_filter: RepositoryFilter = None
        ):
            # build map from repository items based on filter and identities
            # it segments all the identities in the repository on classification
            map_ids1 = {}
            for k, g in itertools.groupby(
                repository.filter(repo_filter), lambda id: id.classification
            ):
                if k not in map_ids1:
                    map_ids1[k] = list(g)
                else:
                    map_ids1[k] += list(g)
            return map_ids1

        target_map = to_segmented_map_by_classification(target_repo)
        source_map = to_segmented_map_by_classification(source_repo, source_filter)
        with concurrent.futures.ThreadPoolExecutor() as exec:
            futures = []
            for target_group in target_map:
                if target_group in source_map:
                    futures.append(
                        exec.submit(
                            self.classification_resolve,
                            source_map[target_group],
                            target_map[target_group],
                            comparator,
                        )
                    )
            for future in concurrent.futures.as_completed(futures):
                result += future.result()
        return result


def resolutions_get_resolved_identity(
    resolutions: List[ResolvedIdentity], unique_id: str, unique_id_should_match_source: bool = False
) -> Tuple[bool, Optional[List[ResolvedIdentity]]]:
    result = False
    res_ids = []
    if resolutions:
        for res_id in [
            res_id for res_id in resolutions if (unique_id_should_match_source and res_id.source.unique_id == unique_id)
                or res_id.target.unique_id == unique_id
        ]:
            result = True
            if not res_ids:
                res_ids = []
            res_ids.append(res_id)
    return result, res_ids
