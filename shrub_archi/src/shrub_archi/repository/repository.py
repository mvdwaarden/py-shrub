import concurrent.futures
import itertools
import os
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List, Tuple
from xml.etree.ElementTree import SubElement, Element, register_namespace

from defusedxml import ElementTree

import shrub_util.core.logging as logging
from shrub_archi.model.model import View, Relation, Relations, RelationsLookup, Identity, Identities, Views, \
    PropertyDefinition, PropertyDefinitions
from shrub_util.core.file import FileLocationIterator, FileLocationIteratorMode


class RepositoryFilter:
    def __init__(self, include_elements: bool = True, include_relations: bool = True):
        self.include_elements = include_elements
        self.include_relations = include_relations

    def include(self, identity: Identity):
        return ((self.include_elements and isinstance(identity, Identity) and not isinstance(identity, Relation)) or (
                self.include_relations and isinstance(identity, Relation)))

    def clone(self, target: "RepositoryFilter" = None):
        if not target:
            target = RepositoryFilter()
        target.include_elements = self.include_elements
        target.include_relations = self.include_relations
        return target


class Repository(ABC):
    def __init__(self, location: str):
        self.location = os.path.normpath(location)
        self._identities: Optional[Identities] = None
        self._relations_lookup: Optional[RelationsLookup] = None
        self._relations: Optional[Relations] = None
        self._elements: Optional[Identities] = None
        self._views: Optional[Views] = None
        self._property_definitions: Optional[PropertyDefinitions] = None

    def read(self) -> "Repository":
        if self._identities is None:
            self._identities = {}
            self._elements = {}
            self._relations = {}
            self._views = {}
            self._property_definitions = {}
        else:
            return self
        return self.do_read()

    @abstractmethod
    def do_read(self) -> "Repository":
        ...

    @abstractmethod
    def do_write(self) -> "Repository":
        ...

    def add_view(self, view: View):
        ...

    def add_element(self, element: Identity):
        ...

    def del_element(self, element: Identity):
        ...

    def add_property_definition(self, property_definition: PropertyDefinition):
        ...

    def add_relation(self, relation: Relation):
        ...

    def del_relation(self, relation: Relation):
        ...

    def get_dry_run_location(self, filename: str = None):
        return f"{self.location}{filename if filename else ''}.backup.xml"

    @property
    def name(self) -> str:
        if self.location:
            drive, full_filename = os.path.splitdrive(self.location)
            path, filename_with_extension = os.path.split(full_filename)
            filename, extension = os.path.splitext(filename_with_extension)
            return filename
        else:
            return "n.a."

    @property
    def identities(self) -> List[Identity]:
        return list(self._identities.values()) if self._identities else []

    @property
    def views(self) -> List[View]:
        result = list(self._views.values()) if self._views else []
        return result

    def filter(self, repo_filter: RepositoryFilter):
        return [identity for identity in self.identities if not repo_filter or repo_filter.include(identity)]

    @property
    def relations(self) -> List[Relation]:
        return list(self._relations.values()) if self._relations else []

    @property
    def elements(self) -> List[Identity]:
        return list(self._elements.values()) if self._elements else []

    @property
    def property_definitions(self) -> List[Identity]:
        return list(self._property_definitions.values()) if self._property_definitions else []

    def get_identity_by_id(self, identifier: str) -> Identity:
        if identifier in self._identities:
            return self._identities[identifier]
        else:
            return None

    def get_relation_by_id(self, identifier: str) -> Relation:
        if identifier in self._relations:
            return self._relations[identifier]
        else:
            return None

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


class ViewRepositoryFilter(RepositoryFilter):
    def __init__(self, views: Views, include_elements: bool = True, include_relations: bool = True,
                 include_views: bool = True):
        super().__init__(include_elements=include_elements, include_relations=include_relations)
        self.views: Views = views
        self._aggregate_identities_ids: Optional[List[str]] = None

    def include(self, identity: Identity):
        return super().include(identity) and (
                identity.unique_id in self.aggregate_identities_ids or isinstance(identity,
                                                                                  Relation) and identity.source_id in self.aggregate_identities_ids and identity.target_id in self.aggregate_identities_ids)

    @property
    def aggregate_identities_ids(self) -> List[str]:
        if self.views and not self._aggregate_identities_ids:
            self._aggregate_identities_ids = []
            for view in self.views:
                if self.include_elements:
                    self._aggregate_identities_ids += view.referenced_elements
                if self.include_relations:
                    self._aggregate_identities_ids += view.referenced_relations
            return self._aggregate_identities_ids
        elif not self._aggregate_identities_ids:
            self._aggregate_identities_ids = []
        return self._aggregate_identities_ids

    def clone(self, target: "ViewRepositoryFilter" = None):
        if not target:
            target = ViewRepositoryFilter(None)
        super().clone(target)
        target.views = []
        target.views += self.views
        return target


class XmiArchiRepository(Repository):
    def __init__(self, location: str):
        super().__init__(location)
        self._element_tree: Optional[ElementTree] = None
        self._namespaces = {"xsi": "http://www.w3.org/2001/XMLSchema-instance",
                            "xmi": "http://www.opengroup.org/xsd/archimate/3.0/"}

    def do_read(self) -> "XmiArchiRepository":
        try:
            root = self.element_tree
            namespaces = self._namespaces

            def _check_for_duplicate_identity(identity, identity_dictionary):
                if identity.unique_id in self._identities:
                    print(
                        f"found duplicate identity {identity.unique_id} - {identity.classification} - {identity.name}")

            for el in root.findall("xmi:elements/xmi:element", namespaces=namespaces):
                identity: Identity = self._read_identity_from_xml_element(el, namespaces, Identity)
                if identity and identity.unique_id:
                    _check_for_duplicate_identity(identity, self._identities)
                    self._identities[identity.unique_id] = identity
                    self._elements[identity.unique_id] = identity
            for el in root.findall("xmi:relationships/xmi:relationship", namespaces=namespaces):
                relation: Relation = self._read_relation_from_xml_element(el, namespaces)
                if relation and relation.unique_id:
                    _check_for_duplicate_identity(relation, self._identities)
                    self._identities[relation.unique_id] = relation
                    self._relations[relation.unique_id] = relation
            for el in root.findall("xmi:views/xmi:diagrams/xmi:view", namespaces=namespaces):
                view: View = self._read_identity_from_xml_element(el, namespaces, View)
                if view and view.unique_id:
                    view.referenced_elements, view.referenced_relations = self._read_referenced_elements_and_relations_from_xml_element(
                        el, namespaces)
                    view.data = el
                    _check_for_duplicate_identity(view, self._identities)

                    def connects_one_off(rel: Relation, combinations: list[()]) -> bool:
                        for a, b in combinations:
                            if rel.connects(a, b):
                                return True
                        return False

                    combos: list[()] = itertools.combinations(view.referenced_elements, 2)
                    relations_potentially_not_in_view = [rel for rel in self._relations.values() if
                                                         connects_one_off(rel, combos)]
                    for rel in relations_potentially_not_in_view:
                        if rel.unique_id not in view.referenced_relations:
                            view.referenced_relations.append(rel.unique_id)
                    self._identities[view.unique_id] = view
                    self._views[view.unique_id] = view
            for el in root.findall("xmi:propertyDefinitions/xmi:propertyDefinition", namespaces=namespaces):
                property_definition: PropertyDefinition = self._read_property_definition_from_xml_element(el,
                                                                                                          namespaces)
                if property_definition and property_definition.unique_id:
                    self._property_definitions[property_definition.unique_id] = property_definition

        except Exception as ex:
            logging.get_logger().error(f"problem with file {self.location}", ex)

        self._create_relations_lookup()
        return self

    def do_write(self) -> "XmiArchiRepository":
        with open(self.get_dry_run_location(), "w") as ofp:
            ofp.write(str(ElementTree.tostring(self.element_tree), encoding="utf8"))
        return self

    def add_view(self, view: View):
        if view.unique_id not in self._views:
            self._views[view.unique_id] = view
            self._identities[view.unique_id] = view
            self._write_view(view.data, self._namespaces)
            self._write_organization(view, self._namespaces)

    def add_element(self, element: Identity):
        if element.unique_id not in self._elements:
            self._elements[element.unique_id] = element
            self._identities[element.unique_id] = element
            self._write_element(element.data, self._namespaces)
            self._write_organization(element, self._namespaces)

    def del_element(self, element: Identity):
        if element.unique_id in self._elements:
            del self._elements[element.unique_id]
            del self._identities[element.unique_id]
            self._delete_element(element, self._namespaces)
            self._delete_organization(element, self._namespaces)
            logging.get_logger().error(f"deleted element {element}")

    def add_property_definition(self, property_definition: PropertyDefinition):
        if property_definition.unique_id not in self._property_definitions:
            self._property_definitions[property_definition.unique_id] = property_definition
            self._write_property_definition(property_definition.data, self._namespaces)

    def add_relation(self, relation: Relation):
        if relation.unique_id not in self._relations:
            self._identities[relation.unique_id] = relation
            self._relations[relation.unique_id] = relation
            self._write_relation(relation.data, self._namespaces)
            self._write_organization(relation, self._namespaces)

    def del_relation(self, relation: Relation):
        if relation.unique_id in self._relations:
            del self._identities[relation.unique_id]
            del self._relations[relation.unique_id]
            self._delete_relation(relation, self._namespaces)
            self._delete_organization(relation, self._namespaces)
            logging.get_logger().error(f"deleted relation {relation}")

    @property
    def element_tree(self) -> ElementTree:
        if not self._element_tree:
            register_namespace('', self._namespaces['xmi'])
            if os.path.exists(self.location):
                self._element_tree = ElementTree.parse(self.location).getroot()
            else:
                self._element_tree = ElementTree.fromstring(f"""<?xml version="1.0" encoding="UTF-8"?>
                            <model xmlns="http://www.opengroup.org/xsd/archimate/3.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.opengroup.org/xsd/archimate/3.0/ http://www.opengroup.org/xsd/archimate/3.1/archimate3_Diagram.xsd" identifier="id-d4622bfd7e0d4cdab01dc008fae135ec">
                              <name xml:lang="en">new</name>
                              <elements>
                                <element identifier="id-63adb6dfcd744d95af09544775c2def7" xsi:type="BusinessObject">
                                  <name xml:lang="en">Business Object</name>
                                </element>
                                <element identifier="id-7d5242910f42421b8d860dd99f788b13" xsi:type="BusinessObject">
                                  <name xml:lang="en">Business Object</name>
                                </element>
                              </elements>
                              <relationships>
                                <relationship identifier="id-769ffc86f4ab495c8ed582ca7c762db1" source="id-63adb6dfcd744d95af09544775c2def7" target="id-7d5242910f42421b8d860dd99f788b13" xsi:type="Association" />
                                <relationship identifier="id-5f46601ce2a84acbb1fa6582fd169463" source="id-63adb6dfcd744d95af09544775c2def7" target="id-63adb6dfcd744d95af09544775c2def7" xsi:type="Association" />
                              </relationships>
                              <organizations>
                                <item>
                                  <label xml:lang="en">Business</label>
                                  <item identifierRef="id-63adb6dfcd744d95af09544775c2def7" />
                                  <item identifierRef="id-7d5242910f42421b8d860dd99f788b13" />
                                </item>
                                <item>
                                  <label xml:lang="en">Relations</label>
                                  <item identifierRef="id-769ffc86f4ab495c8ed582ca7c762db1" />
                                  <item identifierRef="id-5f46601ce2a84acbb1fa6582fd169463" />
                                </item>
                                <item>
                                  <label xml:lang="en">Views</label>
                                  <item identifierRef="id-a391959582744211b3145e30c20e8546" />
                                </item>
                              </organizations>
                              <views>
                                <diagrams>
                                  <view identifier="id-a391959582744211b3145e30c20e8546" xsi:type="Diagram">
                                    <name xml:lang="en">Default View</name>        
                                  </view>
                                </diagrams>
                              </views>
                            </model>
                            """)

        return self._element_tree

    def _read_identity_from_xml_element(self, el, namespaces, specialization) -> Identity | View:
        result = None
        try:
            name = documentation = None
            for child in el:
                if child.tag.endswith("name"):
                    name = child.text
                elif child.tag.endswith("documentation"):
                    documentation = child.text
            result = specialization(unique_id=el.get("identifier"), name=name, description=documentation,
                                    classification=el.get(f"{{{namespaces['xsi']}}}type"), location=self.location,
                                    data=el)
        except Exception as ex:
            logging.get_logger().error(f"problem reading element {el}", ex)
        return result

    def _read_property_definition_from_xml_element(self, el, namespaces) -> PropertyDefinition:
        result = None
        try:
            name = documentation = None
            for child in el:
                if child.tag.endswith("name"):
                    name = child.text
                elif child.tag.endswith("documentation"):
                    documentation = child.text
            result = PropertyDefinition(unique_id=el.get("identifier"), name=name, description=documentation,
                                        classification=el.get("type"), location=self.location, data=el)
        except Exception as ex:
            logging.get_logger().error(f"problem reading property definition {el}", ex)
        return result

    def _read_relation_from_xml_element(self, el, namespaces) -> Relation:
        result = None
        try:
            name = documentation = None
            for child in el:
                if child.tag.endswith("name"):
                    name = child.text
                elif child.tag.endswith("documentation"):
                    documentation = child.text
            xsi_type = el.get(f"{{{namespaces['xsi']}}}type")
            result = Relation(unique_id=el.get("identifier"), name=name, description=documentation,
                              classification=f"{xsi_type}Relationship", location=self.location,
                              source_id=el.get("source"), target_id=el.get("target"), data=el)
        except Exception as ex:
            logging.get_logger().error(f"problem reading element {el}", ex)
        return result

    def _read_referenced_elements_and_relations_from_xml_element(self, el, namespaces) -> Tuple[List[str], List[str]]:
        element_refs = []
        relation_refs = []
        try:
            xsi_type = f"{{{namespaces['xsi']}}}type"
            for child in el.findall(f".//xmi:node[@{xsi_type}='Element']", namespaces=namespaces):
                element_refs.append(child.get("elementRef"))
            for child in el.findall(f".//xmi:connection[@{xsi_type}='Relationship']", namespaces=namespaces):
                relation_refs.append(child.get("relationshipRef"))
        except Exception as ex:
            logging.get_logger().error(f"problem reading element {el}", ex)
        return element_refs, relation_refs

    def _write_view(self, view, namespaces):
        try:
            root = self.element_tree
            diagrams = root.findall("xmi:views/xmi:diagrams", namespaces=self._namespaces)
            diagrams[0].append(view)
        except Exception as ex:
            logging.get_logger().error(f"problem writing view {view}", ex)

    def _write_element(self, element, namespaces):
        try:
            root = self.element_tree
            elements = root.findall("xmi:elements", namespaces=self._namespaces)
            elements[0].append(element)
        except Exception as ex:
            logging.get_logger().error(f"problem writing element {element}", ex)

    def _delete_element(self, element, namespaces):
        try:
            root = self.element_tree
            relations = root.findall("xmi:elements", namespaces=self._namespaces)
            rel = root.findall(f"xmi:elements/xmi:element[@identifier='{element.unique_id}']",
                               namespaces=self._namespaces)
            if len(rel):
                relations[0].remove(rel[0])
        except Exception as ex:
            logging.get_logger().error(f"problem deleting element {element}", ex)

    def _write_relation(self, relation, namespaces):
        try:
            root = self.element_tree
            relations = root.findall("xmi:relationships", namespaces=self._namespaces)
            relations[0].append(relation)
        except Exception as ex:
            logging.get_logger().error(f"problem writing relation {relation}", ex)

    def _delete_relation(self, relation, namespaces):
        try:
            root = self.element_tree
            relations = root.findall("xmi:relationships", namespaces=self._namespaces)
            rel = root.findall(f"xmi:relationships/xmi:relationship[@identifier='{relation.unique_id}']",
                               namespaces=self._namespaces)
            if len(rel):
                relations[0].remove(rel[0])
        except Exception as ex:
            logging.get_logger().error(f"problem deleting relation {relation}", ex)

    def _write_organization(self, identity, namespaces):
        try:
            organization = "Imports"
            root = self.element_tree
            label = root.findall(f"xmi:organizations/xmi:item/xmi:label[.='{organization}']",
                                 namespaces=self._namespaces)
            folder_item = None
            if len(label) == 0:
                organizations = root.findall("xmi:organizations", namespaces=self._namespaces)
                folder_item = SubElement(organizations[0], f"{{{self._namespaces['xmi']}}}item")
                label = SubElement(folder_item, f"{{{self._namespaces['xmi']}}}label", attrib={"xml:lang": "nl"})
                label.text = organization
            else:
                # find folder item (Python has limited XPath support
                # xmi:organizations/xmi:item[xmi:label[.='{organization}']] does not work
                for item in root.findall("xmi:organizations/xmi:item", namespaces=self._namespaces):
                    if item.find("xmi:label", namespaces=self._namespaces).text == organization:
                        folder_item = item
                        break
            item_ref = SubElement(folder_item, f"{{{self._namespaces['xmi']}}}item",
                                  attrib={"identifierRef": identity.unique_id})
        except Exception as ex:
            logging.get_logger().error(f"problem writing identity {identity} to organizations", ex)

    def _delete_organization(self, identity, namespaces):
        try:
            def remove_item(item, unique_id) -> bool:
                removed = False
                to_remove = []
                for child in item.findall("xmi:item", namespaces=namespaces):
                    if child.get("identifierRef") == unique_id:
                        to_remove.append(child)
                for remove_me in to_remove:
                    item.remove(remove_me)
                    removed = True
                if not removed:
                    for child in item.findall("xmi:item", namespaces=namespaces):
                        if remove_item(child, unique_id):
                            removed = True
                return removed

            for item in self.element_tree.findall(f"xmi:organizations/xmi:item", namespaces=namespaces):
                remove_item(item, identity.unique_id)

        except Exception as ex:
            logging.get_logger().error(f"problem deleting identity {identity} in organizations", ex)

    def _write_property_definition(self, property_definition, namespaces):
        try:
            root = self.element_tree
            property_definitions = root.findall("xmi:propertyDefinitions", namespaces=self._namespaces)
            if len(property_definitions) == 0:
                views = root.findall("xmi:views", namespaces=self._namespaces)
                index = list(root).index(views[0])
                root.insert(index, Element(f"{{{namespaces['xmi']}}}propertyDefinitions"))
                property_definitions = root.findall("xmi:propertyDefinitions", namespaces=self._namespaces)
            property_definitions[0].append(property_definition)
        except Exception as ex:
            logging.get_logger().error(f"problem writing property definition {property_definition}", ex)


class CoArchiRepository(Repository):
    def __init__(self, location: str):
        super().__init__(location)

    def do_read(self) -> "CoArchiRepository":
        with ThreadPoolExecutor(max_workers=128) as exec:
            futures = {}
            for dirpath, dirs, file in self:
                if "relationship" in file.lower():
                    futures[exec.submit(self._read_relation_from_file, dirpath, file)] = file
                else:
                    futures[exec.submit(self._read_identity_from_file, dirpath, file)] = file
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                match result:
                    case Relation():
                        self._relations[result.unique_id] = result
                        # relation can also be a target
                        self._identities[result.unique_id] = result
                    case View():
                        self._views[result.unique_id] = result
                        self._identities[result.unique_id] = result
                    case Identity():
                        self._elements[result.unique_id] = result
                        self._identities[result.unique_id] = result

        self._create_relations_lookup()
        return self

    def do_write(self) -> "Repository":
        return self

    def _read_identity_from_file(self, dirpath, file) -> Identity | View:
        result = None
        full_filename = os.path.join(dirpath, file)
        # logging.get_logger().error(f"start reading id from {full_filename}")
        try:
            et = ElementTree.parse(full_filename)
            root = et.getroot()
            classification = root.tag.split("}")[-1]
            if classification.lower().endswith("diagrammodel"):
                constructor = View
            else:
                constructor = Identity
            identity = constructor(unique_id=root.get("id"), name=root.get("name"),
                                   description=root.get("documentation"), classification=classification,
                                   location=full_filename)
            if identity.unique_id and identity.name:
                result = identity
        except Exception as ex:
            logging.get_logger().error(f"problem with file {full_filename}", ex)
        return result

    def _read_relation_from_file(self, dirpath, file) -> Relation:
        result = None
        full_filename = os.path.join(dirpath, file)
        # logging.get_logger().error(f"start reading id from {full_filename}")
        try:
            et = ElementTree.parse(full_filename)
            root = et.getroot()
            for child in root:
                match child.tag:
                    case "source":
                        source = child
                    case "target":
                        target = child
            relation = Relation(unique_id=root.get("id"), name=root.get('name'), description=root.get("documentation"),
                                classification=root.tag.split("}")[-1], source_id=source.get("href").split("#")[1],
                                target_id=target.get("href").split("#")[1], location=full_filename)
            if relation.unique_id:
                result = relation
        except Exception as ex:
            logging.get_logger().error(f"problem with file {full_filename}", ex)
        return result

    def __iter__(self):
        return FileLocationIterator(self.location, mode=FileLocationIteratorMode.MODE_FILE)
