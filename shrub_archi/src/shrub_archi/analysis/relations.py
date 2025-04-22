import shrub_util.core.logging as logging

from shrub_util.generation.template_renderer import DictionaryRenderer
import csv
from typing import List, Tuple

REL_2_CYPHER_RENDERER = "REL_RENDERER"
REL_2_CYPHER_RENDERER_TEMPLATE = """
    {% for n in nodes %}
    {% set node_type = n.ci_type  %}
    CREATE ({{n.key}}{{ cypher_node_namer(n) }})
    {% endfor %}  
    {% for r in relations %}
    CREATE ({{ r.src.key }}) -[{{ cypher_relation_namer(r) }}]-> ({{ r.dest.key }})
    {% endfor %}                 
    """



class Node:
    def __init__(self, key: str, ci_type: str, ci_sub_type: str):
        self.key = key
        self.ci_type = ci_type
        self.ci_sub_type = ci_sub_type


class Relation:
    def __init__(self, src: Node, dest: Node, name: str, ok: bool, classification: str):
        self.name = name
        self.src = src
        self.dest = dest
        self.ok = ok
        self.classification = classification

def relations_get_visualization_renderer():
    return DictionaryRenderer({
        REL_2_CYPHER_RENDERER: REL_2_CYPHER_RENDERER_TEMPLATE
    })


def relations_2_cypher(file: str):
    nodes, relations = read_relations(file)

    relations_write_cypher(file, nodes=nodes, relations=relations)

def read_relations(file: str) -> Tuple[List[Node], List[Relation]]:
    def create_node_key(ci_type: str, ci_sub_type: str):
        return f"{ci_type}{ci_sub_type}".replace(" ","").replace("*","Any").replace("-","").lower()

    def create_relation_key(src: Node, dest: Node, name: str):
        return f"{src.key}{dest.key}{name}".replace(" ","").lower()

    src_type_idx = 0
    src_sub_type_idx = 1
    relation_idx = 2
    dest_type_idx = 3
    dest_sub_type_idx = 4
    ok_idx = 5
    classification_idx = 6

    nodes = {}
    relations = {}
    with open(file,mode="r", newline='', encoding='utf-8') as ifp:
        reader = csv.reader(ifp, delimiter="," )
        skipped_first = False
        for row in reader:
            if not skipped_first:
                skipped_first = True
                continue
            try:
                src_ci_type = row[src_type_idx]
                src_ci_sub_type = row[src_sub_type_idx]
                dest_ci_type = row[dest_type_idx]
                dest_ci_sub_type = row[dest_sub_type_idx]
                relation_name = row[relation_idx]
                ok = True if row[ok_idx].lower() == 'ok' else False
                classification = row[classification_idx]
                node_key = create_node_key(src_ci_type, src_ci_sub_type)
                if node_key not in nodes:
                    src_node = Node(node_key, src_ci_type, src_ci_sub_type)
                    nodes[node_key] = src_node
                else:
                    src_node = nodes[node_key]
                node_key = create_node_key(dest_ci_type, dest_ci_sub_type)
                if node_key not in nodes:
                    dest_node = Node(node_key, dest_ci_type, dest_ci_sub_type)
                    nodes[node_key] = dest_node
                else:
                    dest_node = nodes[node_key]
                rel_key = create_relation_key(src_node, dest_node, relation_name)
                if rel_key not in relations:
                    relation = Relation(src_node, dest_node, relation_name, ok, classification)
                    if relation.classification == 'Perfect':
                        relations[rel_key] = relation
                else:
                    relation = relations[rel_key]
            except Exception as ex:
                logging.get_logger().error(f"problem processing row from {file}", ex=ex)

    return list(nodes.values()), list(relations.values())


def relations_write_cypher(file: str, nodes: List[Node], relations: List[Relation]):
    with open(f"{file}.cypher", "w", encoding="utf-8") as ofp:
        def cypher_node_namer(n) -> str:
            if isinstance(n, Node):
                ci_type = n.ci_type.replace('*','Any')
                ci_sub_type = n.ci_sub_type.replace('*','Any')
                class_name = ci_type if ci_sub_type == 'Any' else ci_sub_type
                class_name = class_name.replace(" ", "").replace("-","")
                return (f":{ class_name } {{name: '{class_name}', type:'{ci_type}', sub_type: '{ci_sub_type}'}}")
            else:
                return f"{{name: '?'}}"

        def cypher_relation_namer(r) -> str:
            if isinstance(r, Relation):
                name = r.name.replace(" ","_").replace("*","any")
                return (f":{name} {{classification:'{r.classification}', ok: '{r.ok}'}}")
            else:
                return "relates_to"


        tr = DictionaryRenderer({REL_2_CYPHER_RENDERER : REL_2_CYPHER_RENDERER_TEMPLATE})
        graph_output = tr.render(REL_2_CYPHER_RENDERER, relations=relations, nodes=nodes,
                                 cypher_node_namer=cypher_node_namer, cypher_relation_namer=cypher_relation_namer)
        ofp.write(graph_output)