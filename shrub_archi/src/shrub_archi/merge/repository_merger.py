import concurrent.futures
import os
import time
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from typing import Optional, List

import shrub_util.core.logging as logging
from shrub_archi.merge.identity import Identities
from shrub_archi.merge.identity_resolver import ResolvedIdentity, \
    RepositoryResolver, IdentityResolver, NaiveIdentityResolver, ResolutionStore
from shrub_archi.merge.repository import Repository


class RepositoryMerger:
    """Merges repository 2 to repository 1, considers
        - if identities in repo1 already exists, the copied identity is ignored
        - if an artefact is copied, all resolved id's that exist in repo 1 are replaced
     """

    def __init__(self, repo1: Repository, repo2: Repository,
                 resolution_store: ResolutionStore = None,
                 compare_cutoff_score=None):
        self.repo1 = repo1
        self.repo2 = repo2
        self.identity_repo1: Optional[Identities] = None
        self.identity_repo2: Optional[Identities] = None
        self.resolutions: List[ResolvedIdentity] = []
        self._identity_resolver: Optional[RepositoryResolver] = None
        self._identity_comparator: Optional[IdentityResolver] = None
        self._resolution_store: Optional[
            ResolutionStore] = resolution_store if resolution_store else None
        self.compare_cutoff_score = compare_cutoff_score if compare_cutoff_score else 85

    def do_merge(self):
        self.read_repositories([self.repo2])
        self.merge()

    def do_resolve(self):
        self.read_repositories([self.repo1, self.repo2])
        self.resolve_identities()

    def read_repositories(self, repos: List[Repository]):
        with ThreadPoolExecutor() as exec:
            futures = {
                exec.submit(repo.read): repo for repo in repos
            }
            for future in concurrent.futures.as_completed(futures):
                repo = future.result()
                print(f"finished {futures[future]} identities {len(repo.identities)}")

    def resolve_identities(self):
        st = time.time()
        self.resolutions = list(
            self.resolver.resolve(repo1=self.repo1,
                                  repo2=self.repo2,
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

    def merge(self):
        # use repo1 items, and copy everything which is in repo2 but has no equivalent in repo1
        # read ID from repo 2, check if it is resolved
        # resolved: do not copy
        # not resolved : copy, make sure to replace all resolved ID's with repo 1 UUID
        for dirpath, dirs, file in self.repo2:
            filename = os.path.join(dirpath, file)
            identity = self.repo2.read_identity(dirpath, file)
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
                    self.copy(filename, self.repo2.location, self.repo1.location,
                              content)
                except Exception as ex:
                    logging.get_logger().error(f"problem readding {filename}",
                                               ex=ex)

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
