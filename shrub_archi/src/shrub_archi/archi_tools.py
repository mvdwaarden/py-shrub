import concurrent.futures

from defusedxml import ElementTree
from dataclasses import dataclass
from typing import Dict, List, Tuple
from difflib import SequenceMatcher
import itertools
import os
from concurrent.futures import ThreadPoolExecutor


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
        self.cache_resolved_ids: List[ResolvedIdentity] = []
        self.resolved_cutoff_score = resolved_cutoff_score

    def resolve(self, repo1: IdentityRepository, repo2: IdentityRepository, cache=True):
        for id1, id2 in [(repo1.identities[id1], repo2.identities[id2]) for id1, id2 in
                         itertools.product(repo1.identities, repo2.identities)]:
            score, rule_name = id1.is_identical_to(id2)
            if score >= self.resolved_cutoff_score:
                resolved_id = ResolvedIdentity(identity1=id1, identity2=id2, score=score,
                                 rule_name=rule_name)
                if cache:
                    self.cache_resolved_ids.append(resolved_id)
                yield resolved_id


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


def extract_identities(archi_repo_folder: str, repo: IdentityRepository = None) -> IdentityRepository:
    result = repo if repo else IdentityRepository()
    count = 0
    for dirpath, dir, files in os.walk(archi_repo_folder):
        def read_identity(dirpath, file):
            result = None
            full_filename = os.path.join(dirpath, file)
            # print(f"start reading id from {full_filename}")
            try:
                et = ElementTree.parse(full_filename)
                root = et.getroot()
                identity = Identity(unique_id=root.get("id"), name=root.get("name"), description=None,
                                    classification=root.tag)
                if identity.unique_id and identity.name:
                    result =  identity
            except Exception as ex:
                print(f"problem with file {full_filename}", ex)
            return result

        with ThreadPoolExecutor(max_workers=128) as exec:
            futures = {exec.submit(read_identity, dirpath, file) : file for file in files }
            for future in concurrent.futures.as_completed(futures):
                identity = future.result()
                if identity:
                    result.add(identity)
                count += 1
                print(f"{count}")

    return result



if __name__ == "__main__":
    repos = []
    if True:

        with ThreadPoolExecutor() as exec:
            futures = {
                exec.submit(extract_identities, file, repo): (file, repo) for file, repo in [
                    ("C:/projects/model-repository/tribe_20kyc_20tech_20-_20secure_20designs", IdentityRepository()),
                    ("C:/projects/model-repository/tribe_20kyc_20tech_20-_20rdt_20area", IdentityRepository()),
                    #("C:/projects/model-repository/tech_and_compliance_model", IdentityRepository()),
                ]
            }
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                repos.append(result)
                print(f"finished {futures[future]} identities {len(result.identities)}")
    else:
        for repo in [
            extract_identities("C:/projects/model-repository/tribe_20kyc_20tech_20-_20rdt_20area"),
            extract_identities("C:/projects/model-repository/tribe_20kyc_20tech_20-_20secure_20designs"),
            #extract_identities("C:/projects/model-repository/tech_and_compliance_model")
        ]:
            repos.append(repo)
            print(f"finished identities {len(repo.identities.items())}")

    idr = IdentityResolver(80)
    for resolved_identity in idr.resolve(repos[0], repos[1]):
        if resolved_identity.score < 100:
            print(resolved_identity)

    for key, group in itertools.groupby(sorted(idr.cache_resolved_ids, key=lambda x: x.score), lambda x: x.score):
        print (key, len(list(group)))