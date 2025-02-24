import itertools
import os
from abc import ABC, abstractmethod
from typing import Optional, List, Tuple
from xml.etree.ElementTree import SubElement, Element, register_namespace


import shrub_util.core.logging as logging
from defusedxml import ElementTree

from shrub_archi.config.consts import ShrubArchi
from shrub_archi.modeling.archi.model.archi_model import (
    View,
    Relation,
    Relations,
    RelationsLookup,
    Entity,
    Entities,
    Views,
    PropertyDefinition,
    PropertyDefinitions,
)
from shrub_archi.modeling.archi.repository.repository_consts import XMI_EMPTY_REPOSITORY
from shrub_util.core.config import Config


class RepositoryFilter:
    def __init__(self, include_elements: bool = True, include_relations: bool = True):
        self.include_elements = include_elements
        self.include_relations = include_relations

    def include(self, entity: Entity):
        return (
                self.include_elements
                and isinstance(entity, Entity)
                and not isinstance(entity, Relation)
        ) or (self.include_relations and isinstance(entity, Relation))

    def clone(self, target: "RepositoryFilter" = None):
        if not target:
            target = RepositoryFilter()
        target.include_elements = self.include_elements
        target.include_relations = self.include_relations
        return target


class Repository(ABC):
    def __init__(self, location: str):
        self.name = ""
        self.description = ""
        self.location = os.path.normpath(location)
        self._entities: Optional[Entities] = None
        self._relations_lookup: Optional[RelationsLookup] = None
        self._relations: Optional[Relations] = None
        self._elements: Optional[Entities] = None
        self._views: Optional[Views] = None
        self._property_definitions: Optional[PropertyDefinitions] = None


    def read(self) -> "Repository":
        if self._entities is None:
            self._entities = {}
            self._elements = {}
            self._relations = {}
            self._views = {}
            self._property_definitions = {}
        else:
            return self
        return self._read()

    @abstractmethod
    def _read(self) -> "Repository":
        ...

    @abstractmethod
    def _write(self) -> "Repository":
        ...

    def add_view(self, view: View):
        ...

    def add_element(self, element: Entity):
        ...

    def del_element(self, element: Entity):
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
    def file_name(self) -> str:
        if self.location:
            drive, full_filename = os.path.splitdrive(self.location)
            path, filename_with_extension = os.path.split(full_filename)
            filename, extension = os.path.splitext(filename_with_extension)
            return filename
        else:
            return "n.a."

    @property
    def entities(self) -> List[Entity]:
        return list(self._entities.values()) if self._entities else []

    @property
    def views(self) -> List[View]:
        result = list(self._views.values()) if self._views else []
        return result

    def filter(self, repo_filter: RepositoryFilter):
        return [
            entity
            for entity in self.entities
            if not repo_filter or repo_filter.include(entity)
        ]

    @property
    def relations(self) -> List[Relation]:
        return list(self._relations.values()) if self._relations else []

    @property
    def elements(self) -> List[Entity]:
        return list(self._elements.values()) if self._elements else []

    @property
    def property_definitions(self) -> List[Entity]:
        return (
            list(self._property_definitions.values())
            if self._property_definitions
            else []
        )

    def get_entity_by_id(self, identifier: str) -> Entity:
        if identifier in self._entities:
            return self._entities[identifier]
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
            if relation.source_id in self._entities:
                relation.source = self._entities[relation.source_id]
            if relation.target_id in self._entities:
                relation.target = self._entities[relation.target_id]
            self._relations_lookup[i] = relation
            i += 1
            self._relations_lookup[(relation.source_id, relation.target_id)] = relation
        return self._relations_lookup

    def get_implicit_relations_not_in_view(self, view: View) -> List[str]:
        implicit_relations: List[str] = []

        def connects_one_off(rel: Relation, combinations: [()]) -> bool:
            for a, b in combinations:
                if rel.connects(a, b):
                    return True
            return False

        combos: [()] = list(itertools.combinations(view.referenced_elements, 2))
        relations_potentially_not_in_view = [
            rel for rel in self._relations.values() if connects_one_off(rel, combos)
        ]
        for rel in relations_potentially_not_in_view:
            if rel.unique_id not in view.referenced_relations:
                implicit_relations.append(rel.unique_id)
                print(f"added implicit relation {rel}")
        return implicit_relations


class ViewRepositoryFilter(RepositoryFilter):
    def __init__(
            self,
            views: List[View],
            include_elements: bool = True,
            include_relations: bool = True,
            include_views: bool = True,
    ):
        super().__init__(
            include_elements=include_elements, include_relations=include_relations
        )
        self.views: List[View] = views
        self._aggregated_entity_ids: Optional[List[str]] = None

    def include(self, entity: Entity):
        return super().include(entity) and (
                entity.unique_id in self.aggregate_entity_ids
                or isinstance(entity, Relation)
                and entity.source_id in self.aggregate_entity_ids
                and entity.target_id in self.aggregate_entity_ids
        )

    @property
    def aggregate_entity_ids(self) -> List[str]:
        if self.views and not self._aggregated_entity_ids:
            self._aggregated_entity_ids = []
            for view in self.views:
                if self.include_elements:
                    self._aggregated_entity_ids += view.referenced_elements
                if self.include_relations:
                    self._aggregated_entity_ids += view.referenced_relations
            return self._aggregated_entity_ids
        elif not self._aggregated_entity_ids:
            self._aggregated_entity_ids = []
        return self._aggregated_entity_ids

    def clone(self, target: "ViewRepositoryFilter" = None):
        if not target:
            target = ViewRepositoryFilter(None)
        super().clone(target)
        target.views = []
        target.views += self.views
        return target

    def contains(self, check_view: View) -> bool:
        for view in self.views:
            if check_view.unique_id == view.unique_id:
                return True
        return False


class XmiArchiRepository(Repository):
    def __init__(self, location: str):
        super().__init__(location)
        self._element_tree: Optional[ElementTree] = None
        self._namespaces = {
            "xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xmi": "http://www.opengroup.org/xsd/archimate/3.0/",
        }

    def _read(self) -> "XmiArchiRepository":
        try:
            root = self.element_tree
            namespaces = self._namespaces

            for el in root.findall("xmi:name", namespaces=namespaces):
                self._name = el.text
                break

            self.name = self._read_name()
            self.description = self._read_description()

            def _check_for_duplicate_entity(entity, entity_dictionary):
                if entity.unique_id in self._entities:
                    print(
                        f"found duplicate entity {entity.unique_id} - {entity.classification} - {entity.name}"
                    )

            for el in root.findall("xmi:elements/xmi:element", namespaces=namespaces):
                entity: Entity = self._read_entity_from_xml_element(
                    el, namespaces, Entity
                )
                if entity and entity.unique_id:
                    _check_for_duplicate_entity(entity, self._entities)
                    self._entities[entity.unique_id] = entity
                    self._elements[entity.unique_id] = entity
            for el in root.findall(
                    "xmi:relationships/xmi:relationship", namespaces=namespaces
            ):
                relation: Relation = self._read_relation_from_xml_element(
                    el, namespaces
                )
                if relation and relation.unique_id:
                    _check_for_duplicate_entity(relation, self._entities)
                    self._entities[relation.unique_id] = relation
                    self._relations[relation.unique_id] = relation
            for el in root.findall(
                    "xmi:views/xmi:diagrams/xmi:view", namespaces=namespaces
            ):
                view: View = self._read_entity_from_xml_element(el, namespaces, View)
                if view and view.unique_id:
                    (
                        view.referenced_elements,
                        view.referenced_relations,
                    ) = self._read_referenced_elements_and_relations_from_xml_element(
                        el, namespaces
                    )
                    view.data = el
                    _check_for_duplicate_entity(view, self._entities)
                    self._entities[view.unique_id] = view
                    self._views[view.unique_id] = view
            for el in root.findall(
                    "xmi:propertyDefinitions/xmi:propertyDefinition", namespaces=namespaces
            ):
                property_definition: PropertyDefinition = (
                    self._read_property_definition_from_xml_element(el, namespaces)
                )
                if property_definition and property_definition.unique_id:
                    self._property_definitions[
                        property_definition.unique_id
                    ] = property_definition

        except Exception as ex:
            logging.get_logger().error(f"problem with file {self.location}", ex=ex)

        self._create_relations_lookup()
        return self

    def _write(self) -> "XmiArchiRepository":
        self._write_name(self.name)
        self._write_description(self.description)
        with open(self.get_dry_run_location(), "w") as ofp:
            ofp.write(str(ElementTree.tostring(self.element_tree), encoding="utf8"))
        return self

    def add_view(self, view: View):
        if view.unique_id not in self._views:
            self._views[view.unique_id] = view
            self._entities[view.unique_id] = view
            self._write_view(view.data, self._namespaces)
            self._write_organization(view, self._namespaces)

    def add_element(self, element: Entity):
        if element.unique_id not in self._elements:
            self._elements[element.unique_id] = element
            self._entities[element.unique_id] = element
            self._write_element(element.data, self._namespaces)
            self._write_organization(element, self._namespaces)

    def del_element(self, element: Entity):
        if element.unique_id in self._elements:
            del self._elements[element.unique_id]
            del self._entities[element.unique_id]
            self._delete_element(element, self._namespaces)
            self._delete_organization(element, self._namespaces)
            logging.get_logger().error(f"deleted element {element}")

    def add_property_definition(self, property_definition: PropertyDefinition):
        if property_definition.unique_id not in self._property_definitions:
            self._property_definitions[
                property_definition.unique_id
            ] = property_definition
            self._write_property_definition(property_definition.data, self._namespaces)

    def add_relation(self, relation: Relation):
        if relation.unique_id not in self._relations:
            self._entities[relation.unique_id] = relation
            self._relations[relation.unique_id] = relation
            self._write_relation(relation.data, self._namespaces)
            self._write_organization(relation, self._namespaces)

    def del_relation(self, relation: Relation):
        if relation.unique_id in self._relations:
            del self._entities[relation.unique_id]
            del self._relations[relation.unique_id]
            self._delete_relation(relation, self._namespaces)
            self._delete_organization(relation, self._namespaces)
            logging.get_logger().error(f"deleted relation {relation}")

    @property
    def element_tree(self) -> ElementTree:
        if not self._element_tree:
            register_namespace("", self._namespaces["xmi"])
            if os.path.exists(self.location):
                self._element_tree = ElementTree.parse(self.location).getroot()
            else:
                empty_repository = XMI_EMPTY_REPOSITORY
                # check if there is an empty repository override in the configuration
                empty_repository_file_name = Config().get_setting(ShrubArchi.CONFIGURATION_SECTION, ShrubArchi.EMPTY_REPOSITORY_FILE_NAME)
                if os.path.exists(empty_repository_file_name):
                    with open(empty_repository_file_name) as ifp:
                        empty_repository = ifp.read()

                self._element_tree = ElementTree.fromstring(empty_repository)

        return self._element_tree

    def _read_name(self) -> str:
        root = self.element_tree
        el = root.find("xmi:name", namespaces=self._namespaces)
        if el is not None:
            return el.text
        else:
            return None

    def _read_description(self) -> str:
        root = self.element_tree
        el = root.find("xmi:documentation", namespaces=self._namespaces)
        if el is not None:
            return el.text
        else:
            return None

    def _read_entity_from_xml_element(
            self, el, namespaces, specialization
    ) -> Entity | View:
        result = None
        try:
            name = documentation = None
            for child in el:
                if child.tag.endswith("name"):
                    name = child.text
                elif child.tag.endswith("documentation"):
                    documentation = child.text
            result = specialization(
                unique_id=el.get("identifier"),
                name=name,
                description=documentation,
                classification=el.get(f"{{{namespaces['xsi']}}}type"),
                location=self.location,
                data=el,
            )
        except Exception as ex:
            logging.get_logger().error(f"problem reading element {el}", ex=ex)
        return result

    def _read_property_definition_from_xml_element(
            self, el, namespaces
    ) -> PropertyDefinition:
        result = None
        try:
            name = documentation = None
            for child in el:
                if child.tag.endswith("name"):
                    name = child.text
                elif child.tag.endswith("documentation"):
                    documentation = child.text
            result = PropertyDefinition(
                unique_id=el.get("identifier"),
                name=name,
                description=documentation,
                classification=el.get("type"),
                location=self.location,
                data=el,
            )
        except Exception as ex:
            logging.get_logger().error(f"problem reading property definition {el}", ex=ex)
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
            result = Relation(
                unique_id=el.get("identifier"),
                name=name,
                description=documentation,
                classification=f"{xsi_type}Relationship",
                location=self.location,
                source_id=el.get("source"),
                target_id=el.get("target"),
                data=el,
            )
        except Exception as ex:
            logging.get_logger().error(f"problem reading element {el}", ex=ex)
        return result

    def _read_referenced_elements_and_relations_from_xml_element(
            self, el, namespaces
    ) -> Tuple[List[str], List[str]]:
        element_refs = []
        relation_refs = []
        try:
            xsi_type = f"{{{namespaces['xsi']}}}type"
            for child in el.findall(
                    f".//xmi:node[@{xsi_type}='Element']", namespaces=namespaces
            ):
                element_refs.append(child.get("elementRef"))
            for child in el.findall(
                    f".//xmi:connection[@{xsi_type}='Relationship']", namespaces=namespaces
            ):
                relation_refs.append(child.get("relationshipRef"))
        except Exception as ex:
            logging.get_logger().error(f"problem reading element {el}", ex=ex)
        return element_refs, relation_refs

    def _write_name(self,  name: str):
        try:
            root = self.element_tree
            el = root.find("xmi:name", namespaces=self._namespaces)
            if el is None:
                el = Element(f"name")
                root.insert(0,el)
            el.text = name
        except Exception as ex:
            logging.get_logger().error(f"problem writing name {self.name}", ex=ex)

    def _write_description(self, description: str):
        try:
            root = self.element_tree
            el = root.find("xmi:documentation", namespaces=self._namespaces)
            if el is None:
                el = Element(f"documentation")
                root.insert(1, el)
            el.text = description
        except Exception as ex:
            logging.get_logger().error(f"problem writing documentation {description}", ex=ex)

    def _write_view(self, view, namespaces):
        try:
            root = self.element_tree
            diagrams = root.findall(
                "xmi:views/xmi:diagrams", namespaces=self._namespaces
            )
            diagrams[0].append(view)
        except Exception as ex:
            logging.get_logger().error(f"problem writing view {view}", ex=ex)

    def _write_element(self, element, namespaces):
        try:
            root = self.element_tree
            elements = root.findall("xmi:elements", namespaces=self._namespaces)
            elements[0].append(element)
        except Exception as ex:
            logging.get_logger().error(f"problem writing element {element}", ex=ex)

    def _delete_element(self, element, namespaces):
        try:
            root = self.element_tree
            relations = root.findall("xmi:elements", namespaces=self._namespaces)
            rel = root.findall(
                f"xmi:elements/xmi:element[@identifier='{element.unique_id}']",
                namespaces=self._namespaces,
            )
            if len(rel):
                relations[0].remove(rel[0])
        except Exception as ex:
            logging.get_logger().error(f"problem deleting element {element}", ex=ex)

    def _write_relation(self, relation, namespaces):
        try:
            root = self.element_tree
            relations = root.findall("xmi:relationships", namespaces=self._namespaces)
            relations[0].append(relation)
        except Exception as ex:
            logging.get_logger().error(f"problem writing relation {relation}", ex=ex)

    def _delete_relation(self, relation, namespaces):
        try:
            root = self.element_tree
            relations = root.findall("xmi:relationships", namespaces=self._namespaces)
            rel = root.findall(
                f"xmi:relationships/xmi:relationship[@identifier='{relation.unique_id}']",
                namespaces=self._namespaces,
            )
            if len(rel):
                relations[0].remove(rel[0])
        except Exception as ex:
            logging.get_logger().error(f"problem deleting relation {relation}", ex=ex)

    def _write_organization(self, entity, namespaces):
        try:
            organization = "Imports"
            root = self.element_tree
            label = root.findall(
                f"xmi:organizations/xmi:item/xmi:label[.='{organization}']",
                namespaces=self._namespaces,
            )
            folder_item = None
            if len(label) == 0:
                organizations = root.findall(
                    "xmi:organizations", namespaces=self._namespaces
                )
                folder_item = SubElement(
                    organizations[0], f"{{{self._namespaces['xmi']}}}item"
                )
                label = SubElement(
                    folder_item,
                    f"{{{self._namespaces['xmi']}}}label",
                    attrib={"xml:lang": "nl"},
                )
                label.text = organization
            else:
                # find folder item (Python has limited XPath support
                # xmi:organizations/xmi:item[xmi:label[.='{organization}']] does not work
                for item in root.findall(
                        "xmi:organizations/xmi:item", namespaces=self._namespaces
                ):
                    if (
                            item.find("xmi:label", namespaces=self._namespaces).text
                            == organization
                    ):
                        folder_item = item
                        break
            item_ref = SubElement(
                folder_item,
                f"{{{self._namespaces['xmi']}}}item",
                attrib={"identifierRef": entity.unique_id},
            )
        except Exception as ex:
            logging.get_logger().error(
                f"problem writing entity {entity} to organizations", ex=ex
            )

    def _delete_organization(self, entity, namespaces):
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

            for item in self.element_tree.findall(
                    f"xmi:organizations/xmi:item", namespaces=namespaces
            ):
                remove_item(item, entity.unique_id)

        except Exception as ex:
            logging.get_logger().error(
                f"problem deleting entity {entity} in organizations", ex=ex
            )

    def _write_property_definition(self, property_definition, namespaces):
        try:
            root = self.element_tree
            property_definitions = root.findall(
                "xmi:propertyDefinitions", namespaces=self._namespaces
            )
            if len(property_definitions) == 0:
                views = root.findall("xmi:views", namespaces=self._namespaces)
                index = list(root).index(views[0])
                root.insert(
                    index, Element(f"{{{namespaces['xmi']}}}propertyDefinitions")
                )
                property_definitions = root.findall(
                    "xmi:propertyDefinitions", namespaces=self._namespaces
                )
            property_definitions[0].append(property_definition)
        except Exception as ex:
            logging.get_logger().error(
                f"problem writing property definition {property_definition}", ex=ex
            )
