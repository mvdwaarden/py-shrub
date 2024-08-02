from networkx import DiGraph, Graph
import shrub_util.core.logging as logging
from shrub_util.generation.template_renderer import TemplateRenderer, get_dictionary_loader


class NamedItem:
    def __init__(self):
        self.id: int = None
        self.name: str = None

    def __hash__(self):
        return self.id

    def __str__(self):
        return f"{self.__class__.__name__},{self.id},{self.name}"


class NamedItemRelation:
    def __init__(self):
        self.src: NamedItem = None
        self.dst: NamedItem = None
        self.type: str = None

    def get_key(self):
        return f"{self.src.name}-({self.type})->{self.dst.name}"


class ConfigurationItem(NamedItem):
    def __init__(self):
        super().__init__()
        self.key = None
        self.aic = None
        self.status = None
        self.sub_type = None
        self.type = None
        self.config_admin: ConfigAdmin = None
        self.department = None
        self.functional_email = None
        self.business_owner: Manager = None
        self.manager: Manager = None
        self.description = None
        self.title = None
        self.related_service_component = None
        self.environments = []
        self.iam_provisioning_methods = []


class ConfigAdmin(NamedItem):
    def __init__(self):
        super().__init__()
        self.functional_email = None


class Manager(NamedItem):
    def __init__(self):
        super().__init__()
        self.email: str = None


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

    def __resolve_named_item(self, named_item: NamedItem, map_named_item: dict, custom_key: str = None) -> NamedItem:
        result = named_item
        check_key = custom_key if custom_key else named_item.name
        if check_key in map_named_item:
            result = map_named_item[check_key]
        else:
            named_item.id = self.uuid
            map_named_item[check_key] = named_item
            self.graph.add_node(named_item)
            self.uuid += 1
        return result

    def resolve_manager(self, manager: Manager) -> Manager:
        return self.__resolve_named_item(manager, self.map_managers, custom_key=manager.email.lower())

    def resolve_service_component(self, service_component: ServiceComponent) -> Manager:
        return self.__resolve_named_item(service_component, self.map_service_components)

    def resolve_department(self, department: Department) -> Manager:
        return self.__resolve_named_item(department, self.map_departments)

    def resolve_configuration_item(self, configuration_item: ConfigurationItem) -> ConfigurationItem:
        return self.__resolve_named_item(configuration_item, self.map_configuration_items)

    def resolve_config_admin(self, config_admin: ConfigAdmin) -> ConfigurationItem:
        return self.__resolve_named_item(config_admin, self.map_config_admins)

    def resolve_vendor(self, vendor: Vendor) -> ConfigurationItem:
        return self.__resolve_named_item(vendor, self.map_vendors)

    def resolve_relation(self, named_item_relation: NamedItemRelation) -> NamedItemRelation:
        result = named_item_relation
        ed = self.graph.get_edge_data(named_item_relation.src, named_item_relation.dst)
        if not ed:
            self.map_relations[named_item_relation.get_key()] = named_item_relation
            self.graph.add_edge(named_item_relation.src, named_item_relation.dst,
                                relation_type=named_item_relation.type)
        else:

            logging.get_logger().warning(f"relation already exists {named_item_relation.get_key()}")

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
