from defusedxml import ElementTree
from dataclasses import dataclass
from typing import Dict, List, Tuple
from difflib import SequenceMatcher
import itertools
import os


MAX_RESOLVED_SCORE: int = 100


@dataclass
class ResolvedIdentity:
    identity1: "Identity"
    identity2: "Identity"
    score: int
    rule_name: str


@dataclass
class Identity:
    unique_id: str
    name: str
    description: str
    classification: str

    def is_identical_to(self, identity: "Identity") -> Tuple[int, str]:
        result = 0, "NO_MATCH_RULE"
        if self.unique_id == identity.unique_id:
            result = MAX_RESOLVED_SCORE, "ID_EXACT_RULE"
        elif self.name == identity.name and self.classification == identity.classification:
            result = MAX_RESOLVED_SCORE, "NAME_EXACT_RULE"
        elif self.classification == identity.classification:
            name_score = int(SequenceMatcher(a=self.name,
                                             b=identity.name).ratio() * MAX_RESOLVED_SCORE)
            description_score = 0
            if self.description and identity.description and (
            self.description) > 10 and len(identity.description) > 10:
                description_score = int(SequenceMatcher(a=self.description,
                                                        b=identity.description).ratio() * MAX_RESOLVED_SCORE)
            if name_score > 0 and name_score > description_score:
                result = name_score, "NAME_CLASS_RULE"
            elif description_score > 0:
                result = description_score, "DESCRIPTION_CLASS_RULE"

        return result


class IdentityRepository:
    def __init__(self):
        self.identities: Dict[str, Identity] = {}

    def add(self, identity: Identity):
        self.identities[identity.unique_id] = identity


class IdentityResolver:
    def __init__(self, resolved_cutoff_score: int):
        self._resolved_ids: List[ResolvedIdentity] = []
        self.resolved_cutoff_score = resolved_cutoff_score

    def register(self, id1: Identity, id2: Identity, score, rule_name):
        self._resolved_ids.append(
            ResolvedIdentity(identity1=id1, identity2=id2, score=score,
                             rule_name=rule_name))

    def resolve(self, repo1: IdentityRepository, repo2: IdentityRepository):
        for id1, id2 in [(repo1.identities[id1], repo2.identities[id2]) for id1, id2 in
                         itertools.product(repo1.identities, repo2.identities)]:
            score, rule_name = id1.is_identical_to(id2)
            if score >= self.resolved_cutoff_score:
                self.register(id1, id2, score, rule_name)
        return self._resolved_ids

    def lookup(self, check_4_resolved_id: str) -> ResolvedIdentity:
        resolved_identity = next(
            filter(lambda o: o.identity1.unique_id == check_4_resolved_id),
            self._resolved_ids)
        return resolved_identity


def test():
    repo1 = IdentityRepository()
    repo2 = IdentityRepository()

    repo1.add(Identity(unique_id="1", name="piet", classification="", description=""))
    repo1.add(Identity(unique_id="2", name="klaas", classification="", description=""))
    repo2.add(Identity(unique_id="11", name="pieto", classification="", description=""))
    repo2.add(
        Identity(unique_id="22", name="klaasj", classification="", description=""))

    for resolved_identity in IdentityResolver(0).resolve(repo1, repo2):
        print(resolved_identity)


def extract_identities(archi_repo_folder: str) -> IdentityRepository:
    result = IdentityRepository()
    for dirpath, dir, files in os.walk(archi_repo_folder):
        for file in files:
            try:
                full_filename = os.path.join(dirpath, file)
                et = ElementTree.parse(full_filename)
                root = et.getroot()
                identity = Identity(unique_id=root.get("id"), name=root.get("name"), description=None, classification=root.tag)
                if identity.unique_id and identity.name:
                    result.add(identity)
            except Exception as ex:
                print(f"problem with file {full_filename}", ex)

    return result



if __name__ == "__main__":
    test()
    result = extract_identities("/Users/mwa17610/Library/Application Support/Archi4/model-repository/hasuki_archi")
    for id, oid in result.identities.items():
        print(id, oid)
    print(len(result.identities))

    for resolved_identity in IdentityResolver(60).resolve(result, result):
        print(resolved_identity)