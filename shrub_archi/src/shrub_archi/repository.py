import concurrent.futures
import os
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from typing import Optional, List

from defusedxml import ElementTree
from shrub_archi.identity import Identity, Identities


class Repository:
    def __init__(self, location: str):
        self.location = location
        self._identities: Optional[Identities] = None


    def read(self) -> "Repository":
        if self._identities is None:
            self._identities = {}
        else:
            return self
        with ThreadPoolExecutor(max_workers=128) as exec:
            futures = {}
            for dirpath, dirs, file in RepositoryIterator(self):
                futures[exec.submit(self.read_identity, dirpath, file)] = file
            for future in concurrent.futures.as_completed(futures):
                identity = future.result()
                if identity:
                    self._identities[identity.unique_id] = identity

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
    @property
    def identities(self) -> List[Identity]:
        return self._identities.values() if self._identities else {}

class IteratorMode(Enum):
    MODE_FILES = 1
    MODE_FILE = 2

class RepositoryIterator:
    def __init__(self, repo: "Repository", mode: "" = IteratorMode.MODE_FILE):
        self.repo: Repository = repo
        self.walker = None
        self.files = []
        self.root = None
        self.dir = None
        self.mode: IteratorMode = mode
    def __iter__(self):
        self.walker = os.walk(self.repo.location)
        return self

    def __next__(self):
        if self.mode == IteratorMode.MODE_FILE:
            if len(self.files) == 0:
                self.root, self.dirs, self.files = next(self.walker)
            file = self.files[0]
            self.files = self.files[1:]
            return self.root, self.dirs, file
        else:
            return next(self.walker)



