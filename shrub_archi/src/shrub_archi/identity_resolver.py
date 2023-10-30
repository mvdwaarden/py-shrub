import concurrent.futures

from dataclasses import dataclass
from typing import Dict, List, Optional
from difflib import SequenceMatcher
import itertools
from abc import ABC, abstractmethod
from enum import Enum
import concurrent.futures
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List

from defusedxml import ElementTree


class ResolvedIdentityAction(Enum):
    REPLACE_TARGET_ID = 1
    REPLACE_TARGET_NAME = 2
    REPLACE_TARGET_DESCRIPTION = 4
    def part_of(self,stacked_action: int):
        return stacked_action & self.value > 0




@dataclass
class ResolvedIdentity:
    identity1: "Identity"
    identity2: "Identity"
    compare_result: "IdentityCompareResult"


@dataclass
class Identity:
    unique_id: str
    name: str
    classification: str = None
    description: Optional[str] = None
    source: Optional[str] = None


@dataclass
class IdentityCompareResult:
    score: int
    rule: str
    verified: bool = False
    MAX_RESOLVED_SCORE: int = 100

    def has_max_score(self):
        return self.score == self.MAX_RESOLVED_SCORE


class Comparator(ABC):
    @abstractmethod
    def compare(self, identity: Identity, identity2: Identity) -> IdentityCompareResult:
        return IdentityCompareResult(0, "")


class NaiveIdentityComparator(Comparator):
    def __init__(self, cutoff_score: int = 80):
        self.cutoff_score = cutoff_score

    def compare(self, identity1: Identity, identity2: Identity) -> Optional[
        IdentityCompareResult]:
        result: Optional[IdentityCompareResult] = None
        if identity1.unique_id == identity2.unique_id:
            result = IdentityCompareResult(
                score=IdentityCompareResult.MAX_RESOLVED_SCORE, rule="ID_EXACT_RULE",
                verified=True)
        elif identity1.classification == identity2.classification:
            if identity1.name == identity2.name:
                result = IdentityCompareResult(
                    score=IdentityCompareResult.MAX_RESOLVED_SCORE + 10,
                    rule="NAME_EXACT_RULE")
            else:
                name_score = int(SequenceMatcher(a=identity1.name,
                                                 b=identity2.name).ratio() * IdentityCompareResult.MAX_RESOLVED_SCORE)
                description_score = 0
                if identity1.description and identity2.description and len(
                        identity1.description) > 10 and len(identity2.description) > 10:
                    description_score = int(SequenceMatcher(a=identity1.description,
                                                            b=identity2.description).ratio() * IdentityCompareResult.MAX_RESOLVED_SCORE)
                if name_score > 0 and name_score > description_score:
                    result = IdentityCompareResult(score=name_score,
                                                   rule="NAME_CLASS_RULE")
                elif description_score > 0:
                    result = IdentityCompareResult(score=description_score,
                                                   rule="DESCRIPTION_CLASS_RULE")

        return result if result and result.score >= self.cutoff_score else None


Identities = Dict[str, Identity]


class RepositoryIterator:
    def __init__(self, repo: "Repository"):
        self.repo: Repository = repo
        self.walker = None
    def __iter__(self):
        self.walker = os.walk(self.repo.location)
        return self

    def __next__(self):
        return next(self.walker)

class Repository:
    def __init__(self, location: str):
        self.location = location
        self.identities: Identities = {}


    def read(self) -> "Repository":
        count = 0
        for dirpath, dir, files in RepositoryIterator(self):
            with ThreadPoolExecutor(max_workers=128) as exec:
                futures = {exec.submit(self.read_identity, dirpath, file): file for file in
                           files}
                for future in concurrent.futures.as_completed(futures):
                    identity = future.result()
                    if identity:
                        self.identities[identity.unique_id] = identity
                    count += 1
                    print(f"{count}")

        return self

    def read_identity(self, dirpath, file):
        result = None
        full_filename = os.path.join(dirpath, file)
        # print(f"start reading id from {full_filename}")
        try:
            et = ElementTree.parse(full_filename)
            root = et.getroot()
            identity = Identity(unique_id=root.get("id"), name=root.get("name"),
                                description=None, classification=root.tag,
                                source=full_filename)
            if identity.unique_id and identity.name:
                result = identity
        except Exception as ex:
            print(f"problem with file {full_filename}", ex)
        return result



class IdentityResolver:
    def __init__(self):
        self.cache_resolved_ids: List[ResolvedIdentity] = []

    @property
    def resolved_ids(self) -> List[ResolvedIdentity]:
        return self.cache_resolved_ids
    def resolve(self, ids1: Repository, ids2: Repository, cache=True,
                comparator: Comparator = None):
        comparator = comparator if comparator else NaiveIdentityComparator()
        for id1, id2 in [(id1, id2) for id1, id2 in
                         itertools.product(ids1.identities.values(), ids2.identities.values())]:
            compare_result = comparator.compare(id1, id2)
            if compare_result:
                resolved_id = ResolvedIdentity(identity1=id1, identity2=id2,
                                               compare_result=compare_result)
                if cache:
                    self.cache_resolved_ids.append(resolved_id)
                yield resolved_id

class RepoMerger:
    def __init__(self, repo1: Repository, repo2: Repository):
        self.repo1 = repo1
        self.repo2 = repo2
        self.identity_repo1: Optional[Identities] = None
        self.identity_repo2: Optional[Identities] = None
        self.resolved_identities: List[ResolvedIdentity] = []

    def do_merge(self):
        self.read_repositories()
        self.resolve_identities()
        self.merge()

    def read_repositories(self):
        self.repo1.read()
        self.repo2.read()

    def resolve_identities(self):
        self.resolved_identities = List[
            self.get_identity_resolver().resolve(ids1=self.repo1,
                                                 ids2=self.repo2,
                                                 comparator=self.get_identity_comparator())]

    def get_identity_resolver(self) -> IdentityResolver:
        return IdentityResolver()

    def get_identity_comparator(self) -> Comparator:
        return NaiveIdentityComparator(cutoff_score=85)


    def merge(self):
        for root, dirpath, files in RepositoryIterator(self.repo1):
            for file in files:
                full_filename = os.path.join(dirpath, file)
                
