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
from shrub_archi.repository.repository import CoArchiRepository, Repository, RepositoryFilter, ViewRepositoryFilter
from shrub_archi.resolver.identity_resolver import ResolvedIdentity, RepositoryResolver, IdentityResolver, \
    ResolverResult, resolutions_is_resolved
from shrub_archi.resolver.resolution_store import ResolutionStore


class NaiveRelationResolver(IdentityResolver):
    def __init__(self, resolutions: List[ResolvedIdentity], cutoff_score: int = 80, parent: IdentityResolver = None):
        super().__init__(parent)
        self.resolutions = resolutions
        self.cutoff_score = cutoff_score

    def do_resolve(self, identity1: Identity, identity2: Identity) -> Optional[ResolverResult]:
        rel_result = source_result = target_result = None

        if isinstance(identity1, Relation) and isinstance(identity2,
                                                          Relation) and identity1.classification == identity2.classification:
            rel1: Relation = identity1
            rel2: Relation = identity2
            source_result = resolutions_is_resolved(self.resolutions, rel2.source_id)
            if source_result:
                target_result = resolutions_is_resolved(self.resolutions, rel2.target_id)
            if target_result:
                if not rel1.name or not rel2.name:
                    ...
                elif rel1.name.lower() == rel2.name.lower():
                    rel_result = ResolverResult(score=ResolverResult.MAX_EQUAL_SCORE + 10,
                                                rule="REL_SOURCE_TARGET_NAME_NAME_EXACT_RULE")
                elif math.fabs(len(identity1.name) - len(identity2.name)) < 10:
                    name_score = int(SequenceMatcher(a=identity1.name.lower(),
                                                     b=identity2.name.lower()).ratio() * ResolverResult.MAX_EQUAL_SCORE)
                    if name_score > 0:
                        rel_result = ResolverResult(score=name_score, rule="REL_SOURCE_TARGET_NAME_CLASS_RULE")

        return rel_result if rel_result and rel_result.score >= self.cutoff_score else None


class NaiveIdentityResolver(IdentityResolver):
    def __init__(self, cutoff_score: int = 80, parent: IdentityResolver = None):
        super().__init__(parent)
        self.cutoff_score = cutoff_score

    def do_resolve(self, identity1: Identity, identity2: Identity) -> Optional[ResolverResult]:
        result = None
        if identity1.unique_id == identity2.unique_id:
            result = ResolverResult(score=ResolverResult.MAX_EQUAL_SCORE + 10, rule="ID_EXACT_RULE")
        elif isinstance(identity1, Relation) and isinstance(identity2, Relation):
            ...
        elif identity1.classification == identity2.classification:
            if not identity1.name or not identity2.name:
                ...
            elif identity1.name.lower() == identity2.name.lower():
                result = ResolverResult(score=ResolverResult.MAX_EQUAL_SCORE + 10, rule="NAME_EXACT_RULE")
            else:
                name_score = 0
                if math.fabs(len(identity1.name) - len(identity2.name)) < 10:
                    name_score = int(SequenceMatcher(a=identity1.name.lower(),
                                                     b=identity2.name.lower()).ratio() * ResolverResult.MAX_EQUAL_SCORE)
                description_score = 0
                if identity1.description and identity2.description and len(identity1.description) > 10 and len(
                        identity2.description) > 10:
                    description_score = int(SequenceMatcher(a=identity1.description,
                                                            b=identity2.description).ratio() * ResolverResult.MAX_EQUAL_SCORE)
                if name_score > 0 and name_score > description_score:
                    result = ResolverResult(score=name_score, rule="NAME_CLASS_RULE")
                elif description_score > 0:
                    result = ResolverResult(score=description_score, rule="DESCRIPTION_CLASS_RULE")

        return result if result and result.score >= self.cutoff_score else None


class RepositoryImporter:
    """Merges repository 2 to repository 1, considers
            - if identities in repo1 already exists, the copied identity is ignored
            - if an artefact is copied, all resolved id's that exist in repo 1 are replaced
         """

    def __init__(self, target_repo: Repository, source_repo: Repository, source_filter: RepositoryFilter,
                 resolution_store: ResolutionStore = None, compare_cutoff_score=None):
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
        repo2_filter_clone = source_filter.clone()
        repo2_filter_clone.include_elements = True
        repo2_filter_clone.include_relations = False
        self.resolutions += list(
            self.resolver.resolve(repo1=self.target_repo, repo2=self.source_repo, repo2_filter=repo2_filter_clone,
                                  comparator=self.identity_comparator))
        print(f"took {time.time() - st} seconds to determine {len(self.resolutions)} element resolutions")

    def resolve_relations(self, source_filter: RepositoryFilter = None):
        repo2_filter_clone = source_filter.clone()
        repo2_filter_clone.include_elements = False
        repo2_filter_clone.include_relations = True
        st = time.time()
        self.resolutions += list(
            self.resolver.resolve(repo1=self.target_repo, repo2=self.source_repo, repo2_filter=repo2_filter_clone,
                                  comparator=self.relation_comparator))
        print(f"took {time.time() - st} seconds to determine {len(self.resolutions)} relation resolutions")

    def is_resolved(self, id2):
        return resolutions_is_resolved(self.resolutions, id2)

    def update_uuids_in_str(self, content: str) -> str:
        for res_id in [res_id for res_id in self.resolutions if res_id.resolver_result.manual_verification is True]:
            content = content.replace(res_id.identity2.unique_id, res_id.identity1.unique_id)
            print(f"replaced {res_id.identity2.unique_id} -> {res_id.identity1.unique_id}")
        return content

    @property
    def resolver(self) -> RepositoryResolver:
        if not self._identity_resolver:
            self._identity_resolver = RepositoryResolver()

        return self._identity_resolver

    @property
    def identity_comparator(self) -> IdentityResolver:
        if not self._identity_comparator:
            self._identity_comparator = NaiveIdentityResolver(cutoff_score=self.compare_cutoff_score)
        return self._identity_comparator

    @property
    def relation_comparator(self) -> IdentityResolver:
        if not self._identity_comparator:
            self._relation_comparator = NaiveRelationResolver(resolutions=self.resolutions,
                                                              cutoff_score=self.compare_cutoff_score)
        return self._identity_comparator

    @abstractmethod
    def import_(self):
        ...

    @abstractmethod
    def import_sweep_update_uuids(self):
        ...


class CoArchiRepositoryImporter(RepositoryImporter):
    """Merges repository 2 to repository 1, considers
        - if identities in repo1 already exists, the copied identity is ignored
        - if an artefact is copied, all resolved id's that exist in repo 1 are replaced
     """

    def __init__(self, target_repo: Repository, source_repo: CoArchiRepository, source_filter: ViewRepositoryFilter,
                 compare_cutoff_score=None):
        super().__init__(target_repo=target_repo, source_repo=source_repo, source_filter=source_filter,
                         compare_cutoff_score=compare_cutoff_score)

    def import_(self):
        # use source items, and copy everything which is in source repo but has no
        # equivalent in target repo
        # read ID from source repo, check if it is resolved
        # resolved:      do not copy
        # not resolved : copy, make sure to replace all resolved ID's with source
        #                repo UUID's
        for dirpath, dirs, file in self.source_repo:
            filename = os.path.join(dirpath, file)
            identity = self.source_repo._read_identity_from_file(dirpath, file)
            if identity:
                found, resolved_result = self.is_resolved(identity.unique_id)
            else:
                found = resolved_result = False
            if not found or resolved_result is not True:
                try:
                    with open(filename, "r", encoding='utf-8') as ifp:
                        content = ifp.read()
                    content = self.update_uuids_in_str(content)
                    self.copy(filename, self.source_repo.location, self.target_repo.location, content)
                except Exception as ex:
                    logging.get_logger().error(f"problem readding {filename}", ex=ex)

    def import_sweep_update_uuids(self):
        ...

    def copy(self, filename: str, base_path: str, target_base_path: str, content: str):
        norm_filename = os.path.normpath(filename)
        relative_filename = norm_filename[len(base_path) + 1:]
        target_filename = self.target_repo.get_dry_run_location(os.path.join(target_base_path, relative_filename))
        drive, tmp = os.path.splitdrive(target_filename)
        path, tmp = os.path.split(tmp)
        if not os.path.exists(path):
            os.makedirs(path)
        print(f"copy {filename} -> {target_filename}")
        with open(target_filename, "w", encoding='utf-8') as ofp:
            ofp.write(content)


class XmiArchiRepositoryImporter(RepositoryImporter):
    """Merges repository 2 to repository 1, considers
        - if identities in repo1 already exists, the copied identity is ignored
        - if an artefact is copied, all resolved id's that exist in repo 1 are replaced
     """

    def __init__(self, target_repo: Repository, source_repo: Repository, source_filter: ViewRepositoryFilter,
                 resolution_store: ResolutionStore = None, compare_cutoff_score=None):
        super().__init__(target_repo=target_repo, source_repo=source_repo, source_filter=source_filter,
                         compare_cutoff_score=compare_cutoff_score)

    def import_(self):
        # use repo1 items, and copy everything which is in repo2 but has no equivalent in repo1
        # read ID from repo 2, check if it is resolved
        # resolved: do not copy
        # not resolved : copy, make sure to replace all resolved ID's with repo 1 UUID
        to_import_identities = []
        for view in self.source_filter.views:
            to_import_identities += view.referenced_elements
            to_import_identities += view.referenced_relations
        # import elements not in target repo, take resolution store info into account
        for unique_id in set(to_import_identities):
            # find identity in source repo
            identity = self.source_repo.get_identity_by_id(unique_id)
            # find resolutions for ID in target repo
            found = False
            target_ids = []
            for resolution in [resolution for resolution in self.resolutions if
                               resolution.identity2.unique_id == unique_id and resolution.resolver_result.manual_verification is True]:
                target_ids += resolution.identity1.unique_id
            # if NOT found -> ADD
            if len(target_ids) == 0:
                match identity:
                    case Relation():
                        self.target_repo.add_relation(identity)
                    case Identity():
                        self.target_repo.add_element(identity)
            # if found -> overwrite? ignore? => ignore for now
            else:
                ...  # overwrite ?

        for property_definition in self.source_repo.property_definitions:
            self.target_repo.add_property_definition(property_definition)

        for view in self.source_filter:
            self.target_repo.add_view(view)

    def import_sweep_update_uuids(self):
        content = None
        with open(self.target_repo.get_dry_run_location(), "r", encoding='utf8') as ifp:
            content = self.update_uuids_in_str(ifp.read())
        if content:
            with open(self.target_repo.get_dry_run_location(), "w", encoding='utf8') as ofp:
                ofp.write(content)


class MergingMode(Enum):
    ONLY_NEW = 1
    OVER_WRITE = 2
