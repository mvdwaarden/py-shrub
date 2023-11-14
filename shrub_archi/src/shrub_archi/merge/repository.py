import concurrent.futures
import os
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from typing import Optional, List

from defusedxml import ElementTree

from shrub_archi.merge.identity import Identity, Identities
from shrub_archi.merge.relation import Relation, Relations, RelationsLookup


class Repository:
    def __init__(self, location: str):
        self.location = os.path.normpath(location)
        self._identities: Optional[Identities] = None
        self._relations: Optional[Relations] = None
        self._relations_lookup: Optional[RelationsLookup] = None


    def get_relative_location(self, artifact_location: str):
        resposity_path = os.path.split(self.location)
        artifact_path = os.path.split(artifact_location)

    def read(self) -> "Repository":
        if self._identities is None or self._relations is None:
            self._identities = {}
            self._relations = {}
        else:
            return self
        with ThreadPoolExecutor(max_workers=128) as exec:
            futures = {}
            for dirpath, dirs, file in self:
                if "relationship" in file.lower():
                    futures[exec.submit(self.read_relation, dirpath, file)] = file
                else:
                    futures[exec.submit(self.read_identity, dirpath, file)] = file
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                match result:
                    case Relation():
                        self._relations[result.unique_id] = result
                        # relation can also be a target
                        self._identities[result.unique_id] = result
                    case Identity():
                        self._identities[result.unique_id] = result
        self._create_relations_lookup()
        return self

    def _create_relations_lookup(self):
        self._relations_lookup = {}
        i = 0
        for relation in self._relations.values():
            if relation.source_id in self._identities:
                relation.source = self._identities[relation.source_id]
            if relation.target_id in self._identities:
                relation.target = self._identities[relation.target_id]
            self._relations_lookup [i] = relation
            i += 1
            self._relations_lookup[(relation.source_id, relation.target_id)] = relation
        return self._relations_lookup

    def read_identity(self, dirpath, file) -> Identity:
        result = None
        full_filename = os.path.join(dirpath, file)
        # print(f"start reading id from {full_filename}")
        try:
            et = ElementTree.parse(full_filename)
            root = et.getroot()
            identity = Identity(unique_id=root.get("id"), name=root.get("name"),
                                description=root.get("documentation"), classification=root.tag,
                                source=full_filename)
            if identity.unique_id and identity.name:
                result = identity
        except Exception as ex:
            print(f"problem with file {full_filename}", ex)
        return result

    def read_relation(self, dirpath, file) -> Relation:
        result = None
        full_filename = os.path.join(dirpath, file)
        # print(f"start reading id from {full_filename}")
        try:
            et = ElementTree.parse(full_filename)
            root = et.getroot()
            for child in root:
                match child.tag:
                    case "source":
                        source = child
                    case "target":
                        target = child

            relation = Relation(unique_id=root.get("id"), name=root.get('name'),
                                description=root.get("documentation"), classification=root.tag,
                                source_id=source.get("href").split("#")[1], target_id=target.get("href").split("#")[1],
                                source=full_filename)
            if relation.unique_id:
                result = relation
        except Exception as ex:
            print(f"problem with file {full_filename}", ex)
        return result

    @property
    def identities(self) -> List[Identity]:
        return self._identities.values() if self._identities else {}

    def __iter__(self):
        class RepositoryIterator:
            def __init__(self, repo: "Repository", mode: "" = IteratorMode.MODE_FILE):
                self.repo: Repository = repo
                self.walker = None
                self.files = []
                self.root = None
                self.dir = None
                self.mode: IteratorMode = mode
                self.walker = os.walk(self.repo.location)

            def __next__(self):
                if self.mode == IteratorMode.MODE_FILE:
                    while len(self.files) == 0:
                        self.root, self.dirs, self.files = next(self.walker)
                    file = self.files[0]
                    self.files = self.files[1:]
                    return self.root, self.dirs, file
                else:
                    return next(self.walker)

        return RepositoryIterator(self, mode=IteratorMode.MODE_FILE)


class IteratorMode(Enum):
    MODE_FILES = 1
    MODE_FILE = 2
