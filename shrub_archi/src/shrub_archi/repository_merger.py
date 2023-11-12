from enum import Enum
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from typing import Optional, List

import shrub_util.core.logging as logging
from shrub_archi.identity import Identities
from shrub_archi.identity_resolver import ResolvedIdentity, \
    IdentityResolver, Comparator, NaiveIdentityComparator, ResolutionStore
from shrub_archi.repository import Repository, RepositoryIterator, IteratorMode


class RepositoryMerger:
    def __init__(self, repo1: Repository, repo2: Repository,
                 resolution_store: ResolutionStore = None):
        self.repo1 = repo1
        self.repo2 = repo2
        self.identity_repo1: Optional[Identities] = None
        self.identity_repo2: Optional[Identities] = None
        self.resolved_identities: List[ResolvedIdentity] = []
        self._identity_resolver: Optional[IdentityResolver] = None
        self._identity_comparator: Optional[Comparator] = None
        self._resolution_store: Optional[
            ResolutionStore] = resolution_store if resolution_store else None

    def do_merge(self):
        self.read_repositories([self.repo2])
        self.merge()

    def do_resolve(self):
        self.read_repositories([self.repo1, self.repo2])
        self.resolve_identities()

    def update_uuids(self, content) -> str:
        for key, value in self.resolution_store.resolutions.items():
            if value[1] is True:
                content = content.replace(value[0], key)

    def read_repositories(self, repos: List[Repository]):
        with ThreadPoolExecutor() as exec:
            futures = {
                exec.submit(repo.read): repo for repo in repos
            }
            for future in concurrent.futures.as_completed(futures):
                repo = future.result()
                print(f"finished {futures[future]} identities {len(repo.identities)}")

    def resolve_identities(self):
        self.resolved_identities = list(
            self.identity_resolver.resolve(ids1=self.repo1,
                                           ids2=self.repo2,
                                           comparator=self.identity_comparator))

    @property
    def identity_resolver(self) -> IdentityResolver:
        if not self._identity_resolver:
            self._identity_resolver = IdentityResolver()

        return self._identity_resolver

    @property
    def identity_comparator(self) -> Comparator:
        if not self._identity_comparator:
            self._identity_comparator = NaiveIdentityComparator(cutoff_score=85)
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
        for dirpath, dirs, file in RepositoryIterator(self.repo2,
                                                      IteratorMode.MODE_FILE):
            identity = self.repo2.read_identity(dirpath, file)
            verified = self.resolution_store.is_resolved(identity.unique_id)
            if verified is False:
                try:
                    with open(identity.source, "r", encoding='utf-8') as ifp:
                        content = ifp.read()
                    content = self.update_uuids(content)
                    print(f"copied {identity.source}")
                except Exception as ex:
                    logging.get_logger().error(f"proflem readding {identity.source}",
                                               ex=ex)


class MergingMode(Enum):
    ONLY_NEW = 1
    OVER_WRITE = 2
