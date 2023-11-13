import concurrent.futures
import os
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from typing import Optional, List

from defusedxml import ElementTree

from shrub_archi.merge.identity import Identity, Identities


class Repository:
    def __init__(self, location: str):
        self.location = os.path.normpath(location)
        self._identities: Optional[Identities] = None

    def get_relative_location(self, artifact_location: str):
        resposity_path = os.path.split(self.location)
        artifact_path = os.path.split(artifact_location)


    def read(self) -> "Repository":
        if self._identities is None:
            self._identities = {}
        else:
            return self
        with ThreadPoolExecutor(max_workers=128) as exec:
            futures = {}
            for dirpath, dirs, file in self:
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

