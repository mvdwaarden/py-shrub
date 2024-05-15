import concurrent.futures
import math
import os
import time
from abc import abstractmethod
from concurrent.futures import ThreadPoolExecutor
from difflib import SequenceMatcher
from enum import Enum
from typing import Optional, List

import shrub_util.core.logging as logging
from shrub_archi.model.model import Identity, Relation
from shrub_archi.repository.repository import (
    CoArchiRepository,
    Repository,
    RepositoryFilter,
    ViewRepositoryFilter,
)
from shrub_archi.resolver.identity_resolver import (
    ResolvedIdentity,
    RepositoryResolver,
    IdentityResolver,
    ResolverResult,
    resolutions_get_resolved_identity,
)
from shrub_archi.resolver.resolution_store import ResolutionStore
import itertools


class NaiveRelationResolver(IdentityResolver):
    def __init__(
        self,
        resolutions: List[ResolvedIdentity],
        cutoff_score: int = 80,
        parent: IdentityResolver = None,
    ):
        super().__init__(parent)
        self.resolutions = resolutions
        self.cutoff_score = cutoff_score

    def do_resolve(
        self, source: Identity, target: Identity
    ) -> Optional[ResolverResult]:
        rel_result = source_result = target_result = None

        if (
            isinstance(source, Relation)
            and isinstance(target, Relation)
            and source.classification == target.classification
        ):
            if source.unique_id == target.unique_id:
                rel_result = ResolverResult(
                    score=ResolverResult.MAX_EQUAL_SCORE + 10, rule="REL_ID_EXACT_RULE"
                )
            else:
                source_rel: Relation = source
                target_rel: Relation = target
                # check if the source of the target relation is resolved
                found, source_results = resolutions_get_resolved_identity(
                    self.resolutions, target_rel.source_id
                )
                target_results = []
                # check if the source of the source relation exists in the resolved source_ids
                for res_id in source_results:
                    if res_id.source.unique_id == source_rel.source_id:
                        # check if the target of the target relation is resolved
                        found, target_results = resolutions_get_resolved_identity(
                            self.resolutions, target_rel.target_id
                        )
                        source_result = res_id
                        break
                # check if the target of the source relation exists in the resolved target ids
                for res_id in target_results:
                     if res_id.source.unique_id == source_rel.target_id:
                        # check if the target of the target relation is resolved
                        target_result = res_id
                        break
                if target_result:
                    if (
                        not source_rel.name
                        or not target_rel.name
                        or source_rel.name.lower() == target_rel.name.lower()
                    ):
                        rel_result = ResolverResult(
                            score=source_result.resolver_result.score
                            * target_result.resolver_result.score
                            / ResolverResult.MAX_EQUAL_SCORE,
                            rule="REL_SOURCE_TARGET_NAME_NAME_EXACT_RULE",
                        )
                    elif math.fabs(len(source.name) - len(target.name)) < 10:
                        name_score = int(
                            SequenceMatcher(
                                a=source.name.lower(), b=target.name.lower()
                            ).ratio()
                            * ResolverResult.MAX_EQUAL_SCORE
                        )
                        if name_score > 0 and name_score >= self.cutoff_score:
                            rel_result = ResolverResult(
                                score=name_score,
                                rule="REL_SOURCE_TARGET_NAME_CLASS_RULE",
                            )

        return rel_result if rel_result else None


class NaiveIdentityResolver(IdentityResolver):
    def __init__(self, cutoff_score: int = 80, parent: IdentityResolver = None):
        super().__init__(parent)
        self.cutoff_score = cutoff_score

    def do_resolve(
        self, identity1: Identity, identity2: Identity
    ) -> Optional[ResolverResult]:
        result = None

        if isinstance(identity1, Relation) and isinstance(identity2, Relation):
            ...
        elif identity1.unique_id == identity2.unique_id:
            result = ResolverResult(
                score=ResolverResult.MAX_EQUAL_SCORE + 10, rule="ID_EXACT_RULE"
            )
        elif identity1.classification == identity2.classification:
            if not identity1.name or not identity2.name:
                ...
            elif identity1.name.lower() == identity2.name.lower():
                result = ResolverResult(
                    score=ResolverResult.MAX_EQUAL_SCORE + 10, rule="NAME_EXACT_RULE"
                )
            else:
                name_score = 0
                if math.fabs(len(identity1.name) - len(identity2.name)) < 10:
                    name_score = int(
                        SequenceMatcher(
                            a=identity1.name.lower(), b=identity2.name.lower()
                        ).ratio()
                        * ResolverResult.MAX_EQUAL_SCORE
                    )
                description_score = 0
                if (
                    identity1.description
                    and identity2.description
                    and len(identity1.description) > 10
                    and len(identity2.description) > 10
                ):
                    description_score = int(
                        SequenceMatcher(
                            a=identity1.description, b=identity2.description
                        ).ratio()
                        * ResolverResult.MAX_EQUAL_SCORE
                    )
                if name_score > 0 and name_score > description_score:
                    result = ResolverResult(score=name_score, rule="NAME_CLASS_RULE")
                elif description_score > 0:
                    result = ResolverResult(
                        score=description_score, rule="DESCRIPTION_CLASS_RULE"
                    )

        return result if result and result.score >= self.cutoff_score else None


class RepositoryImporter:
    """Merges repository 2 to repository 1, considers
    - if identities in repo1 already exists, the copied identity is ignored
    - if an artefact is copied, all resolved id's that exist in repo 1 are replaced
    """

    def __init__(
        self,
        target_repo: Repository,
        source_repo: Repository,
        source_filter: RepositoryFilter,
        resolution_store: ResolutionStore = None,
        compare_cutoff_score=None,
    ):
        self.target_repo: Repository = target_repo
        self.source_repo: Repository = source_repo
        self.source_filter: RepositoryFilter = source_filter
        self.resolutions: List[ResolvedIdentity] = []
        self._identity_resolver: Optional[RepositoryResolver] = None
        self._identity_comparator: Optional[IdentityResolver] = None
        self._relation_comparator: Optional[IdentityResolver] = None
        self.compare_cutoff_score = compare_cutoff_score if compare_cutoff_score else 85

    def do_import(self):
        # make sure to read source repository
        self.read_repositories([self.source_repo])
        self.import_()

    def do_resolve(self):
        self.read_repositories([self.target_repo, self.source_repo])
        self.resolutions: List[ResolvedIdentity] = []
        self.resolve_elements(source_filter=self.source_filter)
        self.resolve_relations(source_filter=self.source_filter)

    def read_repositories(self, repos: List[Repository]):
        with ThreadPoolExecutor() as exec:
            futures = {exec.submit(repo.read): repo for repo in repos}
            for future in concurrent.futures.as_completed(futures):
                repo = future.result()
                print(f"finished {futures[future]} identities {len(repo.identities)}")

    def resolve_elements(self, source_filter: RepositoryFilter = None):
        st = time.time()
        source_filter_clone = source_filter.clone()
        source_filter_clone.include_elements = True
        source_filter_clone.include_relations = False
        self.resolutions += list(
            self.resolver.resolve(
                target_repo=self.target_repo,
                source_repo=self.source_repo,
                source_filter=source_filter_clone,
                comparator=self.identity_comparator,
            )
        )
        print(
            f"took {time.time() - st} seconds to determine {len(self.resolutions)} element resolutions"
        )

    def resolve_relations(self, source_filter: RepositoryFilter = None):
        source_filter_clone = source_filter.clone()
        source_filter_clone.include_elements = False
        source_filter_clone.include_relations = True
        st = time.time()
        self.resolutions += list(
            self.resolver.resolve(
                target_repo=self.target_repo,
                source_repo=self.source_repo,
                source_filter=source_filter_clone,
                comparator=self.relation_comparator,
            )
        )
        print(
            f"took {time.time() - st} seconds to determine {len(self.resolutions)} relation resolutions"
        )

    def get_target_ids_for_source_id(self, unique_id) -> list[str]:
        result = []
        for resolution in [
            resolution
            for resolution in self.resolutions
            if resolution.source.unique_id == unique_id
            and resolution.resolver_result.manual_verification is True
        ]:
            result.append(resolution.target.unique_id)
        return sorted(result)

    def update_uuids_in_str(self, content: str) -> str:
        for resolution in [
            resolution
            for resolution in self.resolutions
            if resolution.resolver_result.manual_verification is True
        ]:
            target_ids = self.get_target_ids_for_source_id(resolution.source.unique_id)
            content = content.replace(
                resolution.source.unique_id, resolution.target.unique_id
            )
            print(
                f"replaced {resolution.source.unique_id} -> {resolution.target.unique_id}"
            )
            if len(target_ids) > 1:
                # note first one is kept!
                for target_id in target_ids[1:]:
                    content = content.replace(target_id, target_ids[0])
                    print(f"merged {target_id} -> {target_ids[0]}")

        return content

    @property
    def resolver(self) -> RepositoryResolver:
        if not self._identity_resolver:
            self._identity_resolver = RepositoryResolver()

        return self._identity_resolver

    @property
    def identity_comparator(self) -> IdentityResolver:
        if not self._identity_comparator:
            self._identity_comparator = NaiveIdentityResolver(
                cutoff_score=self.compare_cutoff_score
            )
        return self._identity_comparator

    @property
    def relation_comparator(self) -> IdentityResolver:
        if not self._relation_comparator:
            self._relation_comparator = NaiveRelationResolver(
                resolutions=self.resolutions, cutoff_score=self.compare_cutoff_score
            )
        return self._relation_comparator

    @abstractmethod
    def import_(self):
        ...

    @abstractmethod
    def import_sweep_update_uuids(self):
        ...


class XmiArchiRepositoryImporter(RepositoryImporter):
    """Merges repository 2 to repository 1, considers
    - if identities in repo1 already exists, the copied identity is ignored
    - if an artefact is copied, all resolved id's that exist in repo 1 are replaced
    """

    def __init__(
        self,
        target_repo: Repository,
        source_repo: Repository,
        source_filter: ViewRepositoryFilter,
        resolution_store: ResolutionStore = None,
        compare_cutoff_score=None,
    ):
        super().__init__(
            target_repo=target_repo,
            source_repo=source_repo,
            source_filter=source_filter,
            compare_cutoff_score=compare_cutoff_score,
        )

    def import_(self):
        # use target items, and copy everything which is in target but has no equivalent in source
        # read ID from source, check if it is resolved
        # resolved: do not copy
        # not resolved : copy, make sure to replace all resolved ID's with repo 1 UUID
        to_import_identities = []
        for view in self.source_filter.views:
            to_import_identities += view.referenced_elements
            to_import_identities += view.referenced_relations
            to_import_identities += self.source_repo.get_implicit_relations_not_in_view(
                view
            )

        # import elements not in target repo, take resolution store info into account
        for unique_id in set(to_import_identities):
            # find resolutions for ID in target repo (multiple source identities can map to same target identity)
            found = False
            target_ids = self.get_target_ids_for_source_id(unique_id)
            # if NOT found -> ADD
            if len(target_ids) == 0:
                # find identity in source repo
                identity = self.source_repo.get_identity_by_id(unique_id)
                match identity:
                    case Relation():
                        self.target_repo.add_relation(identity)
                    case Identity():
                        self.target_repo.add_element(identity)
            # if source maps to multiple identities in target, remove all but one in the target!!
            if len(target_ids) > 1:
                for target_id in target_ids[1:]:
                    identity = self.target_repo.get_identity_by_id(target_id)
                    match identity:
                        case Relation():
                            self.target_repo.del_relation(identity)
                        case Identity():
                            self.target_repo.del_element(identity)

        for property_definition in self.source_repo.property_definitions:
            self.target_repo.add_property_definition(property_definition)

        for view in self.source_filter.views:
            self.target_repo.add_view(view)

    def import_sweep_update_uuids(self):
        content = None
        with open(self.target_repo.get_dry_run_location(), "r", encoding="utf8") as ifp:
            content = self.update_uuids_in_str(ifp.read())
        if content:
            with open(
                self.target_repo.get_dry_run_location(), "w", encoding="utf8"
            ) as ofp:
                ofp.write(content)


class MergingMode(Enum):
    ONLY_NEW = 1
    OVER_WRITE = 2
