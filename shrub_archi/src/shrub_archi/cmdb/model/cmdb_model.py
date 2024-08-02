import json
from typing import Optional, TypeVar

from networkx import DiGraph

import shrub_util.core.logging as logging
from shrub_util.generation.template_renderer import TemplateRenderer, get_dictionary_loader

T = TypeVar("T")


class NamedItem:
    def __init__(self):
        self.id: int = None
        self.name: str = None

    def __hash__(self):
        return self.id

    def __str__(self):
        return f"{self.__class__.__name__},{self.id},{self.name}"

    def get_resolve_key(self):
        return self.name

    def resolve_references(self, id_entity_map: dict):
        ...

    def to_dict(self) -> dict:
        the_dict = {"@type": self.__class__.__name__, "id": self.id, "name": self.name}

        return the_dict

    def from_dict(self, the_dict):
        if "id" in the_dict:
            self.id = the_dict["id"]
        if "name" in the_dict:
            self.name = the_dict["name"]


class NamedItemRelation(NamedItem):
    def __init__(self):
        super().__init__()
        self.src: NamedItem = None
        self.dst: NamedItem = None
        self.type: str = None

    def get_resolve_key(self):
        resolve_key = None
        if isinstance(self.src, int) and isinstance(self.dst, int):
            resolve_key = f"{self.src}-({self.type})->{self.dst}"
        else:
            resolve_key = f"{self.src.get_resolve_key()}-({self.type})->{self.dst.get_resolve_key()}"
        return resolve_key

    def to_dict(self) -> dict:
        the_dict = super().to_dict()
        the_dict["@type"] =  self.__class__.__name__
        the_dict["src"] = self.src.id
        the_dict["dst"] = self.dst.id
        the_dict["type"] = self.type
        return the_dict

    def from_dict(self, the_dict: dict):
        super().from_dict(the_dict)
        self.src = the_dict["src"]
        self.dst = the_dict["dst"]
        self.type = the_dict["type"]

    def resolve_references(self, id_entity_map: dict):
        if isinstance(self.src, int) and self.src in id_entity_map:
            self.src = id_entity_map[self.src]
        if isinstance(self.dst, int) and self.dst in id_entity_map:
            self.dst = id_entity_map[self.dst]


class ConfigurationItem(NamedItem):
    def __init__(self):
        super().__init__()
        self.key = None
        self.aic = None
        self.status = None
        self.sub_type = None
        self.type = None
        self.config_admin: Optional[ConfigAdmin] = None
        self.department: Optional[Department] = None
        self.business_owner: Optional[Manager] = None
        self.manager: Optional[Manager] = None
        self.description = None
        self.title = None
        self.related_service_component: Optional[ServiceComponent] = None
        self.vendor: Optional[Vendor] = None
        self.environments = []
        self.iam_provisioning_methods = []

    def to_dict(self) -> dict:
        the_dict = super().to_dict()
        if self.key:
            the_dict["key"] = self.key
        if self.aic:
            the_dict["aic"] = self.aic
        if self.status:
            the_dict["status"] = self.status
        if self.sub_type:
            the_dict["sub_type"] = self.sub_type
        if self.type:
            the_dict["type"] = self.type
        if self.config_admin:
            the_dict["config_admin"] = self.config_admin.id if isinstance(self.config_admin,
                                                                          ConfigAdmin) else self.config_admin
        if self.department:
            the_dict["department"] = self.department.id if isinstance(self.department, Department) else self.department
        if self.business_owner:
            the_dict["business_owner"] = self.business_owner.id if isinstance(self.business_owner,
                                                                              Manager) else self.business_owner
        if self.manager:
            the_dict["manager"] = self.manager.id if isinstance(self.manager, Manager) else self.manager
        if self.description:
            the_dict["description"] = self.description
        if self.title:
            the_dict["title"] = self.title
        if self.related_service_component:
            the_dict["related_service_component"] = self.related_service_component.id if isinstance(
                self.related_service_component, ServiceComponent) else self.related_service_component
        if self.vendor:
            the_dict["vendor"] = self.vendor.id if isinstance(self.vendor, Vendor) else self.vendor
        if self.environments:
            the_dict["environments"] = self.environments
        if self.iam_provisioning_methods:
            the_dict["iam_provisioning_methods"] = self.iam_provisioning_methods

        return the_dict

    def from_dict(self, the_dict: dict):
        super().from_dict(the_dict)
        if "key" in the_dict:
            self.key = the_dict["key"]
        if "aic" in the_dict:
            self.aic = the_dict["aic"]
        if "status" in the_dict:
            self.status = the_dict["status"]
        if "type" in the_dict:
            self.type = the_dict["type"]
        if "sub_type" in the_dict:
            self.sub_type = the_dict["sub_type"]
        if "title" in the_dict:
            self.title = the_dict["title"]
        if "description" in the_dict:
            self.description = the_dict["description"]
        if "environments" in the_dict:
            self.environments = the_dict["environments"]
        if "iam_provisioning_methods" in the_dict:
            self.iam_provisioning_methods = the_dict["iam_provisioning_methods"]
        if "department" in the_dict:
            self.department = the_dict["department"]
        if "manager" in the_dict:
            self.manager = the_dict["manager"]
        if "config_admin" in the_dict:
            self.config_admin = the_dict["config_admin"]
        if "business_owner" in the_dict:
            self.business_owner = the_dict["business_owner"]
        if "related_service_component" in the_dict:
            self.related_service_component = the_dict["related_service_component"]
        if "vendor" in the_dict:
            self.vendor = the_dict["vendor"]

    def resolve_references(self, id_entity_map: dict):
        if isinstance(self.manager, int) and self.manager in id_entity_map:
            self.manager = id_entity_map[self.manager]
        if isinstance(self.vendor, int) and self.vendor in id_entity_map:
            self.vendor = id_entity_map[self.vendor]
        if isinstance(self.business_owner, int) and self.business_owner in id_entity_map:
            self.business_owner = id_entity_map[self.business_owner]
        if isinstance(self.config_admin, int) and self.config_admin in id_entity_map:
            self.config_admin = id_entity_map[self.config_admin]
        if isinstance(self.related_service_component, int) and self.related_service_component in id_entity_map:
            self.related_service_component = id_entity_map[self.related_service_component]
        if isinstance(self.department, int) and self.department in id_entity_map:
            self.department = id_entity_map[self.department]


class ConfigAdmin(NamedItem):
    def __init__(self):
        super().__init__()
        self.functional_email = None

    def to_dict(self) -> dict:
        the_dict = super().to_dict()
        if self.functional_email:
            the_dict["functional_email"] = self.functional_email
        return the_dict

    def from_dict(self, the_dict: dict):
        super().from_dict(the_dict)
        if "functional_email" in the_dict:
            self.functional_email = the_dict["functional_email"]


class Manager(NamedItem):
    def __init__(self):
        super().__init__()
        self.email: str = None

    def to_dict(self) -> dict:
        the_dict = super().to_dict()
        if self.email:
            the_dict["email"] = self.email
        return the_dict

    def get_resolve_key(self):
        return self.email

    def from_dict(self, the_dict: dict):
        super().from_dict(the_dict)
        if "email" in the_dict:
            self.email = the_dict["email"]


class Department(NamedItem):
    def __init__(self):
        super().__init__()


class ServiceComponent(NamedItem):
    def __init__(self):
        super().__init__()


class Vendor(NamedItem):
    def __init__(self):
        super().__init__()


class ConfigurationItemRelation(NamedItemRelation):
    def __init__(self):
        super().__init__()
        ...


class CmdbLocalView:
    def __init__(self):
        self.uuid = 0
        self.map_configuration_items: dict = {}
        self.map_managers: dict = {}
        self.map_config_admins: dict = {}
        self.map_departments: dict = {}
        self.map_service_components: dict = {}
        self.map_vendors: dict = {}
        self.map_relations: dict = {}

        self.graph: DiGraph = DiGraph()

    def __resolve_named_item(self, named_item: T, map_named_item: dict, custom_key: str = None) -> T:
        result = named_item
        check_key = named_item.get_resolve_key()
        if check_key in map_named_item:
            result = map_named_item[check_key]
        else:
            named_item.id = self.uuid
            map_named_item[check_key] = named_item
            self.graph.add_node(named_item)
            self.uuid += 1
        return result

    def resolve_manager(self, manager: Manager) -> Manager:
        return self.__resolve_named_item(manager, self.map_managers)

    def resolve_service_component(self, service_component: ServiceComponent) -> ServiceComponent:
        return self.__resolve_named_item(service_component, self.map_service_components)

    def resolve_department(self, department: Department) -> Department:
        return self.__resolve_named_item(department, self.map_departments)

    def resolve_configuration_item(self, configuration_item: ConfigurationItem) -> ConfigurationItem:
        return self.__resolve_named_item(configuration_item, self.map_configuration_items)

    def resolve_config_admin(self, config_admin: ConfigAdmin) -> ConfigAdmin:
        return self.__resolve_named_item(config_admin, self.map_config_admins)

    def resolve_vendor(self, vendor: Vendor) -> Vendor:
        return self.__resolve_named_item(vendor, self.map_vendors)

    def resolve_relation(self, named_item_relation: T) -> T:
        result = named_item_relation
        ed = self.graph.get_edge_data(named_item_relation.src, named_item_relation.dst)
        if not ed:
            result.id = self.uuid
            self.map_relations[named_item_relation.get_resolve_key()] = named_item_relation
            self.graph.add_edge(named_item_relation.src, named_item_relation.dst,
                                relation_type=named_item_relation.type)
            self.uuid += 1
        else:
            logging.get_logger().warning(f"relation already exists {named_item_relation.get_resolve_key()}")
        return result

    def write_dot_graph(self, file: str):
        DOT_TEMPLATE = """
            digraph "{{g.name}}" {
                rankdir=LR
                {% for s,d in g.edges %}
                    {% set relation_type = g.get_edge_data(s,d)["relation_type"] %}
                    "{{ s.name }}" -> "{{ d.name }}" [label={{relation_type}}]
                {% endfor %}
            }
            """
        with open(f"{file}.dot", "w") as ofp:
            tr = TemplateRenderer({"tha_template": DOT_TEMPLATE}, get_loader=get_dictionary_loader)
            dot = tr.render("tha_template", g=self.graph)
            ofp.write(dot)

    def write_json(self, file):
        with open(f"{file}.json", "w") as opf:
            opf.write(json.dumps(self.to_dict()))

    def read_json(self, file):
        with open(f"{file}.json", "r") as opf:
            self.from_dict(json.loads(opf.read()))

    def to_dict(self) -> dict:
        the_dict = {}

        def add_named_entity_map_to_dict(name: str, named_entity_map: dict):
            the_dict[name] = []
            for v in named_entity_map.values():
                the_dict[name].append(v.to_dict())

        for name, named_entity_map in [("configuration_items", self.map_configuration_items),
                                       ("service_components", self.map_service_components),
                                       ("vendors", self.map_vendors),
                                       ("departments", self.map_departments), ("managers", self.map_managers),
                                       ("config_admins", self.map_config_admins), ("relations", self.map_relations), ]:
            add_named_entity_map_to_dict(name, named_entity_map)

        return the_dict

    def from_dict(self, the_dict: dict):
        map_all_named_entities = {}
        resolve_references = []

        def add_dict_to_named_entity_to_map(name: str, named_entity_map: dict, constructor: T, resolver):
            for v in the_dict[name]:
                ne = constructor()
                ne.from_dict(v)
                named_entity_map[ne.get_resolve_key()] = ne
                map_all_named_entities[ne.id] = ne
                resolve_references.append(ne.resolve_references)
                resolver(ne)

        for name, named_entity_map, constructor, resolver in [
            ("configuration_items", self.map_configuration_items, ConfigurationItem, self.resolve_configuration_item),
            ("service_components", self.map_service_components, ServiceComponent, self.resolve_service_component),
            ("vendors", self.map_vendors, Vendor, self.resolve_vendor),
            ("departments", self.map_departments, Department, self.resolve_department),
            ("managers", self.map_managers, Manager, self.resolve_manager),
            ("config_admins", self.map_config_admins, ConfigAdmin, self.resolve_config_admin),
            ("relations", self.map_relations, ConfigurationItemRelation, self.resolve_relation)]:
            add_dict_to_named_entity_to_map(name, named_entity_map, constructor, resolver)

        for resolve in resolve_references:
            resolve(map_all_named_entities)
