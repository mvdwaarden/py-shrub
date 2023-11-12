import os
from enum import Enum
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
from shrub_archi.identity_resolver import ResolvedIdentity, \
    IdentityResolver, Comparator, NaiveIdentityComparator, ResolutionStore
from shrub_archi.identity import Identities
from shrub_archi.repository import Repository, RepositoryIterator


class RepositoryMerger:
    def __init__(self, repo1: Repository, repo2: Repository, resolution_store_location: str):
        self.repo1 = repo1
        self.repo2 = repo2
        self.identity_repo1: Optional[Identities] = None
        self.identity_repo2: Optional[Identities] = None
        self.resolved_identities: List[ResolvedIdentity] = []
        self.resolution_store_location = resolution_store_location if resolution_store_location else "/tmp"
        self._identity_resolver: Optional[IdentityResolver] = None
        self._identity_comparator: Optional[Comparator] = None
        self._resolution_store: Optional[ResolutionStore] = None

    def do_merge(self):
        self.read_repositories()
        self.resolve_identities()

        #self.merge()

    def do_resolve(self):
        self.read_repositories()
        self.resolve_identities()

    def read_repositories(self):
        with ThreadPoolExecutor() as exec:
            futures = {
                exec.submit(repo.read): repo for repo in [self.repo1, self.repo2]
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
        if self._identity_comparator:
            self._identity_comparator = NaiveIdentityComparator(cutoff_score=85, resolution_store=self.resolution_store)
        return self._identity_comparator

    @property
    def resolution_store(self) -> ResolutionStore:
        if not self._resolution_store:
            self._resolution_store = ResolutionStore(
                location=self.resolution_store_location)
        return self._resolution_store
    def merge(self):
        for root, dirpath, files in RepositoryIterator(self.repo1):
            for file in files:
                full_filename = os.path.join(dirpath, file)


class MergingMode(Enum):
    ONLY_NEW = 1
    OVER_WRITE = 2
