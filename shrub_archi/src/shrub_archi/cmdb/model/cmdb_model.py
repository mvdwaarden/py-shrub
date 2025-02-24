from typing import Optional, TypeVar, Callable

from networkx import DiGraph

T = TypeVar("T")

""" CMDB class relations
    A NamedItemRelation 
        relates a source NamedItem to a destination NamedItem 
        is of a certain type
    A ConfigurationItem
        has a Manager
        is assigned to a Department
        has a ConfigAdminGroup
        is related to ServiceComponents
        has a business owner which is a Manager
        has a system owner which is a Manager
        can have a Vendor
"""


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
        the_dict["@type"] = self.__class__.__name__
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
        self.system_owner: Optional[Manager] = None
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
        if self.system_owner:
            the_dict["system_owner"] = self.system_owner.id if isinstance(self.system_owner,
                                                                          Manager) else self.system_owner
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
        if "system_owner" in the_dict:
            self.system_owner = the_dict["system_owner"]
        if "config_admin" in the_dict:
            self.config_admin = the_dict["config_admin"]
        if "business_owner" in the_dict:
            self.business_owner = the_dict["business_owner"]
        if "related_service_component" in the_dict:
            self.related_service_component = the_dict["related_service_component"]
        if "vendor" in the_dict:
            self.vendor = the_dict["vendor"]

    def resolve_references(self, id_entity_map: dict):
        if isinstance(self.system_owner, int) and self.system_owner in id_entity_map:
            self.system_owner = id_entity_map[self.system_owner]
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
        # extra logic
        if not self.name and self.email:
            self.name = self.email


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


class ObjectReferenceRelation(NamedItemRelation):
    def __init__(self):
        super().__init__()
        ...


class CmdbLocalView:
    def __init__(self):
        self.uuid = 0
        self.all_maps = []
        self.map_configuration_items: dict = {}
        self.all_maps.append(("configuration_items", self.map_configuration_items, ConfigurationItem))
        self.map_managers: dict = {}
        self.all_maps.append(("managers", self.map_managers, Manager))
        self.map_config_admins: dict = {}
        self.all_maps.append(("config_admins", self.map_config_admins, ConfigAdmin))
        self.map_departments: dict = {}
        self.all_maps.append(("departments", self.map_departments, Department))
        self.map_service_components: dict = {}
        self.all_maps.append(("service_components", self.map_service_components, ServiceComponent))
        self.map_vendors: dict = {}
        self.all_maps.append(("vendors", self.map_vendors, Vendor))
        self.map_relations: dict = {}
        self.all_maps.append(("relations", self.map_relations, ConfigurationItemRelation))
        self.graph: DiGraph = None

    def __resolve_named_item(self, named_item: T, map_named_item: dict, custom_key: str = None) -> T:
        result = named_item
        check_key = named_item.get_resolve_key()
        if check_key in map_named_item:
            result = map_named_item[check_key]
        else:
            named_item.id = self.uuid
            map_named_item[check_key] = named_item
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
        return self.__resolve_named_item(named_item_relation, self.map_relations)

    def to_dict(self) -> dict:
        the_dict = {}

        def add_named_entity_map_to_dict(name: str, named_entity_map: dict):
            the_dict[name] = []
            for v in named_entity_map.values():
                the_dict[name].append(v.to_dict())

        for name, named_entity_map, constructur in self.all_maps:
            add_named_entity_map_to_dict(name, named_entity_map)

        return the_dict

    def from_dict(self, the_dict: dict):
        map_all_named_entities = {}
        deferred_resolve_references = []

        def add_dict_to_named_entity_to_map(name: str, named_entity_map: dict, constructor: T):
            for v in the_dict[name]:
                ne = constructor()
                ne.from_dict(v)
                named_entity_map[ne.get_resolve_key()] = ne
                map_all_named_entities[ne.id] = ne
                deferred_resolve_references.append(ne.resolve_references)

        for name, named_entity_map, constructor in self.all_maps:
            add_dict_to_named_entity_to_map(name, named_entity_map, constructor)

        for resolve in deferred_resolve_references:
            resolve(map_all_named_entities)

    def refresh_object_reference_relations(self, include_object_reference: bool):
        def add_config_item_relations(ci: ConfigurationItem):
            def _resolve_relation(dst: NamedItem, relation_type):
                if dst:
                    relation = ObjectReferenceRelation()
                    relation.src = ci
                    relation.dst = dst
                    relation.type = relation_type
                    self.resolve_relation(relation)

            _resolve_relation(ci.vendor, "vendor")
            _resolve_relation(ci.system_owner, "system_owner")
            _resolve_relation(ci.business_owner, "business owner")
            _resolve_relation(ci.related_service_component, "related_service_component")
            _resolve_relation(ci.config_admin, "config_admin")
            _resolve_relation(ci.department, "department")

        # delete the old object relation references
        rel_to_delete = []
        for rel in self.map_relations.values():
            if isinstance(rel, ObjectReferenceRelation):
                rel_to_delete.append(rel.get_resolve_key())
        for k in rel_to_delete:
            del self.map_relations[k]
        if include_object_reference:
            # add the objecct relation references
            for ci in self.map_configuration_items.values():
                add_config_item_relations(ci)

    def build_graph(self, include_object_reference: bool = True,
                    node_filter: Callable[[NamedItem], bool] = None) -> DiGraph:
        g = DiGraph()
        if not node_filter:
            def no_filter(n: NamedItem) -> bool:
                return True

            node_filter = no_filter
        else:
            param_node_filter = node_filter

            def local_node_filter(n: NamedItem) -> bool:
                if include_object_reference:
                    return param_node_filter(n)
                elif not isinstance(n, ConfigurationItem):
                    return False
                else:
                    return param_node_filter(n)

            node_filter = local_node_filter

        self.refresh_object_reference_relations(include_object_reference)
        for key, named_entity_map, constructor in self.all_maps:
            if issubclass(constructor, NamedItemRelation):
                for v in [v for v in named_entity_map.values() if node_filter(v.src) and node_filter(v.dst)]:
                    g.add_edge(v.src, v.dst, relation_type=v.type)
            else:
                for v in named_entity_map.values():
                    if node_filter(v):
                        g.add_node(v)

        return g
