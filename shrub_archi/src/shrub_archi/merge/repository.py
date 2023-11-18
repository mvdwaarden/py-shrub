import concurrent.futures
import os
from concurrent.futures import ThreadPoolExecutor
from shrub_util.core.file import FileLocationIterator, FileLocationIteratorMode
from typing import Optional, List
from abc import ABC, abstractmethod
from defusedxml import ElementTree

from shrub_archi.merge.identity import Identity, Identities
from shrub_archi.merge.relation import Relation, Relations, RelationsLookup


class Repository(ABC):
    def __init__(self, location: str):
        self.location = os.path.normpath(location)
        self._identities: Optional[Identities] = None
        self._relations_lookup: Optional[RelationsLookup] = None
        self._relations: Optional[Relations] = None
        self._elements: Optional[Identities] = None

    def read(self) -> "Repository":
        if self._identities is None:
            self._identities = {}
            self._elements = {}
            self._relations = {}
        else:
            return self
        return self.do_read()

    @abstractmethod
    def do_read(self) -> "Repository":
        ...

    @property
    def identities(self) -> List[Identity]:
        return self._identities.values() if self._identities else []

    @property
    def relations(self) -> List[Relation]:
        return self._relations.values() if self._relations else []

    @property
    def elements(self) -> List[Identity]:
        return self._elements.values() if self._elements else []

    def _create_relations_lookup(self):
        self._relations_lookup = {}
        i = 0
        for relation in self._relations.values():
            if relation.source_id in self._identities:
                relation.source = self._identities[relation.source_id]
            if relation.target_id in self._identities:
                relation.target = self._identities[relation.target_id]
            self._relations_lookup[i] = relation
            i += 1
            self._relations_lookup[(relation.source_id, relation.target_id)] = relation
        return self._relations_lookup


class XmiArchiRepository(Repository):
    def __init__(self, location: str):
        super().__init__(location)

    def do_read(self) -> "XmiArchiRepository":
        try:
            et: ElementTree = ElementTree.parse(self.location)
            root = et.getroot()
            namespaces = {
                "xsi": "http://www.w3.org/2001/XMLSchema-instance",
                "xmi": "http://www.opengroup.org/xsd/archimate/3.0/"
            }
            for el in root.findall("xmi:elements/xmi:element", namespaces=namespaces):
                identity = self.read_identity_from_xml_element(el, namespaces)
                if identity and identity.unique_id:
                    self._identities[identity.unique_id] = identity
                    self._elements[identity.unique_id] = identity
            for el in root.findall("xmi:relationships/xmi:relationship",
                                   namespaces=namespaces):
                relation = self.read_relation_from_xml_element(el, namespaces)
                if relation and relation.unique_id:
                    self._identities[relation.unique_id] = relation
                    self._relations[relation.unique_id] = relation

        except Exception as ex:
            print(f"problem with file {self.location}", ex)

        self._create_relations_lookup()
        return self

    def read_identity_from_xml_element(self, el, namespaces) -> Identity:
        result = None
        try:
            name = documentation = None
            for child in el:
                if child.tag.endswith("name"):
                    name = child.text
                elif child.tag.endswith("documentation"):
                    documentation = child.text
            result = identity = Identity(
                unique_id=el.get("identifier"),
                name=name,
                description=documentation,
                classification=el.get(f"{{{namespaces['xsi']}}}type"),
                source=self.location)
        except Exception as ex:
            print(f"problem reading element {el}", ex)
        return result

    def read_relation_from_xml_element(self, el, namespaces) -> Relation:
        result = None
        try:
            name = documentation = None
            for child in el:
                if child.tag.endswith("name"):
                    name = child.text
                elif child.tag.endswith("documentation"):
                    documentation = child.text
            xsi_type = el.get(f"{{{namespaces['xsi']}}}type")
            result = relation = Relation(
                unique_id=el.get("identifier"),
                name=name,
                description=documentation,
                classification=f"{xsi_type}Relationship",
                source=self.location,
                source_id=el.get("source"),
                target_id=el.get("target")
            )
        except Exception as ex:
            print(f"problem reading element {el}", ex)
        return result


class CoArchiRepository(Repository):
    def __init__(self, location: str):
        super().__init__(location)

    def do_read(self) -> "CoArchiRepository":
        with ThreadPoolExecutor(max_workers=128) as exec:
            futures = {}
            for dirpath, dirs, file in self:
                if "relationship" in file.lower():
                    futures[exec.submit(self._read_relation_from_file, dirpath,
                                        file)] = file
                else:
                    futures[exec.submit(self._read_identity_from_file, dirpath,
                                        file)] = file
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                match result:
                    case Relation():
                        self._relations[result.unique_id] = result
                        # relation can also be a target
                        self._identities[result.unique_id] = result
                    case Identity():
                        self._elements[result.unique_id] = result
                        self._identities[result.unique_id] = result
        self._create_relations_lookup()
        return self

    def _read_identity_from_file(self, dirpath, file) -> Identity:
        result = None
        full_filename = os.path.join(dirpath, file)
        # print(f"start reading id from {full_filename}")
        try:
            et = ElementTree.parse(full_filename)
            root = et.getroot()
            identity = Identity(unique_id=root.get("id"), name=root.get("name"),
                                description=root.get("documentation"),
                                classification=root.tag.split("}")[-1],
                                source=full_filename)
            if identity.unique_id and identity.name:
                result = identity
        except Exception as ex:
            print(f"problem with file {full_filename}", ex)
        return result

    def _read_relation_from_file(self, dirpath, file) -> Relation:
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
                                description=root.get("documentation"),
                                classification=root.tag.split("}")[-1],
                                source_id=source.get("href").split("#")[1],
                                target_id=target.get("href").split("#")[1],
                                source=full_filename)
            if relation.unique_id:
                result = relation
        except Exception as ex:
            print(f"problem with file {full_filename}", ex)
        return result

    def __iter__(self):
        return FileLocationIterator(self.location,
                                    mode=FileLocationIteratorMode.MODE_FILE)
