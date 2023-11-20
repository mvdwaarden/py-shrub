import concurrent.futures
import os
import time
from abc import abstractmethod
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from typing import Optional, List

import shrub_util.core.logging as logging
from shrub_archi.resolver.identity_resolver import ResolvedIdentity, RepositoryResolver, \
    IdentityResolver, NaiveIdentityResolver
from shrub_archi.resolver.resolution_store import ResolutionStore
from shrub_archi.model.model import Views
from shrub_archi.repository.repository import CoArchiRepository, Repository


class RepositoryImporter:
    """Merges repository 2 to repository 1, considers
            - if identities in repo1 already exists, the copied identity is ignored
            - if an artefact is copied, all resolved id's that exist in repo 1 are replaced
         """

    def __init__(self, target_repo: Repository, source_repo: Repository,
                 source_filter: Views, resolution_store: ResolutionStore = None,
                 compare_cutoff_score=None):
        self.target_repo: Repository = target_repo
        self.source_repo: Repository = source_repo
        self.source_filter = source_filter
        self.resolutions: List[ResolvedIdentity] = []
        self._identity_resolver: Optional[RepositoryResolver] = None
        self._identity_comparator: Optional[IdentityResolver] = None
        self._resolution_store: Optional[
            ResolutionStore] = resolution_store if resolution_store else None
        self.compare_cutoff_score = compare_cutoff_score if compare_cutoff_score else 85

    def do_import(self):
        # make sure to read source repository
        self.read_repositories([self.source_repo])
        self.import_()

    def do_resolve(self):
        self.read_repositories([self.target_repo, self.source_repo])
        self.resolve_identities(source_filter=self.source_filter)

    def read_repositories(self, repos: List[Repository]):
        with ThreadPoolExecutor() as exec:
            futures = {exec.submit(repo.read): repo for repo in repos}
            for future in concurrent.futures.as_completed(futures):
                repo = future.result()
                print(f"finished {futures[future]} identities {len(repo.identities)}")

    def resolve_identities(self, source_filter: Views = None):
        st = time.time()
        self.resolutions = list(
            self.resolver.resolve(repo1=self.target_repo, repo2=self.source_repo,
                                  repo2_filter=source_filter,
                                  comparator=self.identity_comparator))
        print(
            f"took {time.time() - st} seconds to determine {len(self.resolutions)} resolutions")

    @property
    def resolver(self) -> RepositoryResolver:
        if not self._identity_resolver:
            self._identity_resolver = RepositoryResolver()

        return self._identity_resolver

    @property
    def identity_comparator(self) -> IdentityResolver:
        if not self._identity_comparator:
            self._identity_comparator = NaiveIdentityResolver(
                cutoff_score=self.compare_cutoff_score)
        return self._identity_comparator

    @property
    def resolution_store(self) -> ResolutionStore:
        return self._resolution_store

    @resolution_store.setter
    def resolution_store(self, resolution_store: ResolutionStore):
        self._resolution_store = resolution_store

    @abstractmethod
    def import_(self):
        ...


class CoArchiRepositoryImporter(RepositoryImporter):
    """Merges repository 2 to repository 1, considers
        - if identities in repo1 already exists, the copied identity is ignored
        - if an artefact is copied, all resolved id's that exist in repo 1 are replaced
     """

    def __init__(self, target_repo: Repository, source_repo: CoArchiRepository,
                 source_filter: Views, resolution_store: ResolutionStore = None,
                 compare_cutoff_score=None):
        super().__init__(target_repo=target_repo, source_repo=source_repo,
                         source_filter=source_filter, resolution_store=resolution_store,
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
                found, resolved_result = self.resolution_store.is_resolved(
                    identity.unique_id)
            else:
                found = resolved_result = False
            if not found or resolved_result is not True:
                try:
                    with open(filename, "r", encoding='utf-8') as ifp:
                        content = ifp.read()
                    content = self.update_uuids(content)
                    self.copy(filename, self.source_repo.location,
                              self.target_repo.location, content)
                except Exception as ex:
                    logging.get_logger().error(f"problem readding {filename}", ex=ex)

    def update_uuids(self, content) -> str:
        for (id1, id2), value in self.resolution_store.resolutions.items():
            if value is True:
                content = content.replace(id2, id1)
        return content

    def copy(self, filename: str, base_path: str, target_base_path: str, content: str):
        norm_filename = os.path.normpath(filename)
        relative_filename = norm_filename[len(base_path) + 1:]
        target_filename = os.path.join(target_base_path,
                                       relative_filename + "_delete_me")
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

    def __init__(self, target_repo: Repository, source_repo: Repository,
                 source_filter: Views, resolution_store: ResolutionStore = None,
                 compare_cutoff_score=None):
        super().__init__(target_repo=target_repo, source_repo=source_repo,
                         source_filter=source_filter, resolution_store=resolution_store,
                         compare_cutoff_score=compare_cutoff_score)

    def import_(self):
        # use repo1 items, and copy everything which is in repo2 but has no equivalent in repo1
        # read ID from repo 2, check if it is resolved
        # resolved: do not copy
        # not resolved : copy, make sure to replace all resolved ID's with repo 1 UUID
        for dirpath, dirs, file in self.source_repo:
            filename = os.path.join(dirpath, file)
            identity = self.source_repo.read_identity(dirpath, file)
            if identity:
                found, resolved_result = self.resolution_store.is_resolved(
                    identity.unique_id)
            else:
                found = resolved_result = False
            if not found or resolved_result is not True:
                try:
                    with open(filename, "r", encoding='utf-8') as ifp:
                        content = ifp.read()
                    content = self.update_uuids(content)
                    self.copy(filename, self.source_repo.location,
                              self.target_repo.location, content)
                except Exception as ex:
                    logging.get_logger().error(f"problem readding {filename}", ex=ex)

    def update_uuids(self, content) -> str:
        for (id1, id2), value in self.resolution_store.resolutions.items():
            if value is True:
                content = content.replace(id2, id1)
        return content

    def copy(self, filename: str, base_path: str, target_base_path: str, content: str):
        norm_filename = os.path.normpath(filename)
        relative_filename = norm_filename[len(base_path) + 1:]
        target_filename = os.path.join(target_base_path,
                                       relative_filename + "_delete_me")
        drive, tmp = os.path.splitdrive(target_filename)
        path, tmp = os.path.split(tmp)
        if not os.path.exists(path):
            os.makedirs(path)
        print(f"copy {filename} -> {target_filename}")
        with open(target_filename, "w", encoding='utf-8') as ofp:
            ofp.write(content)


class MergingMode(Enum):
    ONLY_NEW = 1
    OVER_WRITE = 2
