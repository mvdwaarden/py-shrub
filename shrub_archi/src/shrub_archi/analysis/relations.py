from shrub_util.generation.template_renderer import TemplateRenderer, DictionaryRenderer
from owlready2 import get_ontology, Ontology
import networkx as nx
import matplotlib as plt
import csv
import uuid

# Jinja2 template for textual representation
REL_RENDERER = "REL_RENDERER"
REL_2_CYPHER_RENDERER_TEMPLATE = """
    {% for n in g.nodes %}
    {% set node_type = n.type if n.__class__.__name__ == "ConfigurationItem" else n.__class__.__name__ %}
    CREATE ({{ n.__class__.__name__ }}{{ n.id }}:{{ node_type }} {{ cypher_node_namer(n) }})
    {% endfor %}  
    {% for s,d in g.edges %}
    {% set relation_type = g.get_edge_data(s,d)["relation_type"] %}
    CREATE ({{ s.__class__.__name__ }}{{ s.id }}) -[:{{ cypher_relation_namer(relation_type) }}]-> ({{ d.__class__.__name__ }}{{ d.id }})
    {% endfor %}                 
    """



class Node:
    def __init__(self, key: str, ci_type: str, ci_sub_type: str):
        self.key = key
        self.ci_type = ci_type
        self.ci_sub_type = ci_type


class Relation:
    def __init__(self, src: Node, dest: Node, name: str, classification: str):
        self.name = name
        self.src = src
        self.dest = src
        self.classification = classification

def relations_get_visualization_renderer():
    return DictionaryRenderer({
        REL_RENDERER: REL_2_CYPHER_RENDERER_TEMPLATE
    })

def read_relations(file):
    def create_node_key(ci_type: str, ci_sub_type: str):
        return f"{src_ci_type}{src_ci_sub_type}".replace(" ","").lower()

    def create_relation_key(src_node: Node, dest_node: Node, name: str):
        return f"{src_node.key}{dest_node.key}{name}".replace(" ","").lower()

    src_type_idx = 0
    src_sub_type_idx = 1
    relation_idx = 2
    dest_type_idx = 3
    dest_sub_type_idx = 4
    classification_idx = 5
    nodes = {}
    relations = {}
    with open(file,"r") as ifp:
        reader = csv.reader(ifp,dialect="excel", delimiter=";" )
        for row in reader:
            src_ci_type = row[src_type_idx]
            src_ci_sub_type = row[src_sub_type_idx]
            dest_ci_type = row[dest_type_idx]
            dest_ci_sub_type = row[dest_sub_type_idx]
            relation_name = row[relation_idx]
            classification = row[classification_idx]
            node_key = create_node_key(src_ci_type, src_ci_sub_type)
            if node_key not in nodes:
                src_node = Node(node_key, src_ci_type, src_ci_sub_type)
                nodes[node_key] = src_node
            else:
                src_node = nodes[node_key]
            node_key = create_node_key(dest_ci_type, dest_ci_sub_type)
            if node_key not in nodes:
                dest_node = Node(node_key, src_ci_type, src_ci_sub_type)
                nodes[node_key] = dest_node
            else:
                dest_node = nodes[node_key]
            rel_key = create_relation_key(src_node, dest_node, relation_name)
            if rel_key not in relations:
                relation = Relation(src_node, dest_node,relation_name, classification)
                relations[relations] = relation
            else:
                relations = relations[rel_key]


def relations_write_cypher(relations: List[Relation], nodes: List[Nodes]):
    g = local_view.build_graph(include_object_reference=include_object_reference, node_filter=node_filter)

    with open(f"{file}.{graph_type.value}", "w", encoding="utf-8") as ofp:
        def dot_shaper(n) -> str:
            return "Mrecord"

        def dot_node_namer(n) -> str:
            if isinstance(n, ConfigurationItem):
                email = n.system_owner.email if n.system_owner else "n.a."
                bo_email = n.business_owner.email if n.business_owner else "n.a."
                department = n.department.name if n.department else "n.a."
                aic = n.aic if n.aic else "n.a."
                return f"{{{{{n.key}|{n.status}|{aic}}} | {{{n.name} | {n.type} | {n.sub_type}}} | {{{bo_email} | {email} | {department}}}}} "
            elif isinstance(n, Manager):
                return f"{{{n.email} | {n.name}}} | {{ Manager }}"
            elif isinstance(n, ConfigAdmin):
                return f"{{{n.functional_email} | {n.name}}} | {{ ConfigAdmin }}"
            else:
                return f"{{{n.name}}} | {{ {n.__class__.__name__} }}"

        def cypher_node_namer(n) -> str:
            if isinstance(n, ConfigurationItem):
                email = n.system_owner.email if n.system_owner else "n.a."
                bo_email = n.business_owner.email if n.business_owner else "n.a."
                department = n.department.name if n.department else "n.a."
                aic = n.aic if n.aic else "n.a."
                return (f"{{name:'{n.name}', system_owner: '{email}', department: '{department}'"
                        f", business_owner: '{bo_email}', type: '{n.type}', sub_type: '{n.sub_type}'"
                        f", status: '{n.status}', key: '{n.key}', aic: '{aic}'}}")
            elif isinstance(n, Manager):
                return f"{{name: '{n.name}', email: '{n.email}'}}"
            elif isinstance(n, ConfigAdmin):
                return f"{{name: '{n.name}', functional_email: '{n.functional_email}'}}"
            else:
                return f"{{name: '{n.name}'}}"

        def cypher_relation_namer(org_name: str) -> str:
            if org_name:
                return org_name.replace(' ', '_')
            else:
                return "relates_to"

        def node_namer(n):
            return n.name

        tr = DictionaryRenderer({GraphType.DOT.value: DOT_TEMPLATE, GraphType.GRAPHML.value: GRAPHML_TEMPLATE,
                                 GraphType.CYPHER.value: CYPHER_TEMPLATE})
        graph_output = tr.render(graph_type.value, g=g, node_filter=node_filter, dot_shaper=dot_shaper,
                                 default_node_namer=node_namer, dot_node_namer=dot_node_namer,
                                 cypher_node_namer=cypher_node_namer, cypher_relation_namer=cypher_relation_namer)
        ofp.write(graph_output)