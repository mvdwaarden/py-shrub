import concurrent.futures
import math
import time
from abc import abstractmethod
from concurrent.futures import ThreadPoolExecutor
from difflib import SequenceMatcher
from enum import Enum
from typing import Optional, List

from shrub_archi.modeling.archi.model.archi_model import Entity, Relation
from shrub_archi.modeling.archi.repository.repository import (
    Repository,
    RepositoryFilter,
    ViewRepositoryFilter,
)
from shrub_archi.modeling.archi.resolver.entity_resolver import (
    ResolvedEntity,
    RepositoryEntityResolver,
    EntityResolver,
    ResolverResult,
    resolutions_get_resolved_entity,
)


class NaiveRelationResolver(EntityResolver):
    def __init__(
            self,
            resolutions: List[ResolvedEntity],
            cutoff_score: int = 80,
            parent: EntityResolver = None,
    ):
        super().__init__(parent)
        self.resolutions = resolutions
        self.cutoff_score = cutoff_score

    def resolve(
            self, source: Entity, target: Entity
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
                found, source_results = resolutions_get_resolved_entity(
                    self.resolutions, target_rel.source_id
                )
                target_results = []
                # check if the source of the source relation exists in the resolved source ids of the target
                for res_id in source_results:
                    if res_id.source.unique_id == source_rel.source_id:
                        # check if the target of the target relation is resolved
                        found, target_results = resolutions_get_resolved_entity(
                            self.resolutions, target_rel.target_id
                        )
                        source_result = res_id
                        break
                # check if the target of the source relation exists in the resolved source ids for the target
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


class NaiveEntityResolver(EntityResolver):
    def __init__(self, cutoff_score: int = 80, parent: EntityResolver = None):
        super().__init__(parent)
        self.cutoff_score = cutoff_score

    def resolve(
            self, source: Entity, target: Entity
    ) -> Optional[ResolverResult]:
        result = None

        if isinstance(source, Relation) and isinstance(target, Relation):
            ...
        elif source.unique_id == target.unique_id:
            result = ResolverResult(
                score=ResolverResult.MAX_EQUAL_SCORE + 10, rule="ID_EXACT_RULE"
            )
        elif source.classification == target.classification:
            if not source.name or not target.name:
                ...
            elif source.name.lower() == target.name.lower():
                result = ResolverResult(
                    score=ResolverResult.MAX_EQUAL_SCORE + 10, rule="NAME_EXACT_RULE"
                )
            else:
                name_score = 0
                if math.fabs(len(source.name) - len(target.name)) < 10:
                    name_score = int(
                        SequenceMatcher(
                            a=source.name.lower(), b=target.name.lower()
                        ).ratio()
                        * ResolverResult.MAX_EQUAL_SCORE
                    )
                description_score = 0
                if (
                        source.description
                        and target.description
                        and len(source.description) > 10
                        and len(target.description) > 10
                ):
                    description_score = int(
                        SequenceMatcher(
                            a=source.description, b=target.description
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


class RepositoryMerger:
    """Merges repository 2 to repository 1, considers
    - if entities in repo1 already exists, the copied entity is ignored
    - if an artefact is copied, all resolved id's that exist in repo 1 are replaced
    """

    def __init__(
            self,
            target_repo: Repository,
            source_repo: Repository,
            source_filter: RepositoryFilter,
            compare_cutoff_score=None,
    ):
        self.target_repo: Repository = target_repo
        self.source_repo: Repository = source_repo
        self.source_filter: RepositoryFilter = source_filter
        self.resolutions: List[ResolvedEntity] = []
        self._entity_resolver: Optional[RepositoryEntityResolver] = None
        self._entity_comparator: Optional[EntityResolver] = None
        self._relation_comparator: Optional[EntityResolver] = None
        self.compare_cutoff_score = compare_cutoff_score if compare_cutoff_score else 85

    def merge(self):
        # make sure to read source repository
        self.read_repositories([self.target_repo])
        self.merge_()

    def determine_resolutions(self):
        self.read_repositories([self.target_repo, self.source_repo])
        self.resolutions: List[ResolvedEntity] = []
        self.resolve_elements(source_filter=self.source_filter)
        self.resolve_relations(source_filter=self.source_filter)

    def read_repositories(self, repos: List[Repository]):
        with ThreadPoolExecutor() as exec:
            futures = {exec.submit(repo.read): repo for repo in repos}
            for future in concurrent.futures.as_completed(futures):
                repo = future.result()
                print(f"finished {futures[future]} entities {len(repo.entities)}")

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
                comparator=self.entity_comparator,
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
                for target_id in target_ids:
                    content = content.replace(target_id, target_ids[0])
                    print(f"merged {target_id} -> {target_ids[0]}")

        return content

    @property
    def resolver(self) -> RepositoryEntityResolver:
        if not self._entity_resolver:
            self._entity_resolver = RepositoryEntityResolver()

        return self._entity_resolver

    @property
    def entity_comparator(self) -> EntityResolver:
        if not self._entity_comparator:
            self._entity_comparator = NaiveEntityResolver(
                cutoff_score=self.compare_cutoff_score
            )
        return self._entity_comparator

    @property
    def relation_comparator(self) -> EntityResolver:
        if not self._relation_comparator:
            self._relation_comparator = NaiveRelationResolver(
                resolutions=self.resolutions, cutoff_score=self.compare_cutoff_score
            )
        return self._relation_comparator

    @abstractmethod
    def merge_(self):
        ...

    @abstractmethod
    def import_sweep_update_uuids(self):
        ...


class XmiArchiRepositoryMerger(RepositoryMerger):
    """Merges repository 2 to repository 1 (from source -> destination), it:
    - determines resolutions
        => entities that could be the same in the source and the destination.
        => a user needs to identify which entities are the same
    - performs a merge also using the resolution specification
    """

    def __init__(
            self,
            target_repo: Repository,
            source_repo: Repository,
            source_filter: ViewRepositoryFilter,
            compare_cutoff_score=None,
    ):
        super().__init__(
            target_repo=target_repo,
            source_repo=source_repo,
            source_filter=source_filter,
            compare_cutoff_score=compare_cutoff_score,
        )

    def merge_(self):
        # use target items, and copy everything which is in target but has no equivalent in source
        # (note: equivalence is based on resolution file. :see: RepositoryMerger.determine_resolutions()
        # read ID from source, check if it is resolved
        # resolved: do not copy
        # not resolved : copy, make sure to replace all resolved ID's with repo 1 UUID
        to_import_entities = []
        for view in self.source_filter.views:
            to_import_entities += view.referenced_elements
            to_import_entities += view.referenced_relations
            to_import_entities += self.source_repo.get_implicit_relations_not_in_view(
                view
            )

        # import elements not in target repo, take resolution store info into account
        for unique_id in set(to_import_entities):
            # find resolutions for ID in target repo (multiple source entities can map to same target entity)
            found = False
            target_ids = self.get_target_ids_for_source_id(unique_id)
            # if NOT found -> ADD
            if len(target_ids) == 0:
                # find entity in source repo
                entity = self.source_repo.get_entity_by_id(unique_id)
                match entity:
                    case Relation():
                        self.target_repo.add_relation(entity)
                    case Entity():
                        self.target_repo.add_element(entity)

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
