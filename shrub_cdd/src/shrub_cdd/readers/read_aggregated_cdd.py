from networkx import Graph, DiGraph, write_graphml
from shrub_util.generation.template_renderer import TemplateRenderer, get_dictionary_loader
import json
import re
from typing import Tuple

EDGE_ATTRIBUTE_WEIGHT = "weight"


class Node:
    def __init__(self, id: int):
        self.id: int = id
        self.initializer = None
        self.attribute = None
        self.value = None
        self.values = []

    def __hash__(self):
        return self.id

    def __str__(self):
        return str(self.id)


def construct_node_with_initializer(id: int, initializer: str) -> Node:
    matcher = re.compile("Node\\(attr_id='(.*)',.*value='(.*)'\\)")
    m = matcher.match(initializer)
    n = Node(id)
    n.initializer = initializer
    if m:
        n.attribute = m.group(1)
        n.value = m.group(2)
        n.values.append(n.value)
    else:
        n.attribute = "?"
    return n


def read_aggregated_graph(json_str: str, graph_name: str):
    raw_network = json.loads(json_str)
    g = DiGraph()
    g.name = graph_name
    node_map = {}
    for json_node in raw_network[graph_name]["nodes"]:
        k = int(json_node)
        v = str(raw_network[graph_name]["nodes"][json_node])
        n = node_map.get(k)
        if not n:
            n = construct_node_with_initializer(k, v)
            node_map[k] = n
            g.add_node(n)
    for edge in raw_network[graph_name]["edges"]:
        src, dst, cnt = tuple(edge)
        src_node = node_map.get(int(src))
        dst_node = node_map.get(int(dst))
        if src_node and dst_node:
            g.add_edge(src_node, dst_node, unique_name=f"{src_node.id}-{dst_node.id}", weight=cnt)

    return g


def construct_aggregated_node(id: int, node: Node) -> Node:
    aggregated_node = Node(id)
    aggregated_node.attribute = node.attribute
    aggregated_node.values.append(node.value)
    return aggregated_node


def update_aggregated_node(aggregated_node: Node, node: Node) -> Node:
    aggregated_node.values.append(node.value)
    return aggregated_node


def aggregate_graph(g: Graph) -> Graph:
    ag = DiGraph()
    ag.name = f"aggregated {g.name}"
    node_map = {}
    node_id = 0
    for _n in g.nodes:
        n = node_map.get(_n.attribute)
        if not n:
            n = construct_aggregated_node(node_id, _n)
            node_map[n.attribute] = n
            node_id += 1
            ag.add_node(n)
        else:
            update_aggregated_node(n, _n)

    for src_node, dst_node in g.edges:
        src = node_map.get(src_node.attribute)
        dst = node_map.get(dst_node.attribute)
        ed = g.get_edge_data(src_node, dst_node)
        aggregated_ed = ag.get_edge_data(src, dst)
        if aggregated_ed:
            aggregated_ed[EDGE_ATTRIBUTE_WEIGHT] += ed[EDGE_ATTRIBUTE_WEIGHT]
        else:
            ag.add_edge(src, dst, weight=ed[EDGE_ATTRIBUTE_WEIGHT])

    return ag


def get_edge_data_value_range(g: Graph, attribute: str) -> Tuple:
    max_value = None
    min_value = None
    for src, dst in g.edges:
        ed = g.get_edge_data(src, dst)
        v = ed.get(attribute)
        if v:
            if not max_value or v > max_value:
                max_value = v
            if not min_value or v < min_value:
                min_value = v

    return min_value, max_value


def get_edge_weight_range(g: Graph):
    return get_edge_data_value_range(g, EDGE_ATTRIBUTE_WEIGHT)


def write_aggregated_graph(g: Graph, file: str):
    min_weight, max_weight = get_edge_weight_range(g)
    write_graphml(g, f"{file}.graphml")
    write_aggregated_dot(g, file)

DOT_TEMPLATE = """
digraph "{{g.name}}" {
    rankdir=LR
    {% for s,d in g.edges %}
        {% set weight = g.get_edge_data(s,d)["weight"] %}
        {% set thinkness = 100*(weight-min_weight)/(max_weight - min_weight) + 1 %}
        "{{ s.attribute }}" -> "{{ d.attribute }}" [weight={{weight}}, penwidth={{thinkness}}]
    {% endfor %}
}
"""

"""
digraph "{{g.name}}" {
    rankdir=LR
    {% for n in g.nodes %}
        "{{ n.attribute }}"
    {% endfor %}
    {% for s,d,k in g.edges %}
        {% set weight = g.get_edge_data(s,d,k)["weight"] %}
        {% set thinkness = 100*(weight-min_weight)/(max_weight - min_weight) %}
        "{{ s.attribute }}" -> "{{ d.attribute }} [weight = {{weight}}]"
    {% endfor %}
}
"""

def write_aggregated_dot(g: Graph, file: str):
    with open(f"{file}.dot", "w") as ofp:
        tr = TemplateRenderer({"tha_template": DOT_TEMPLATE}, get_loader=get_dictionary_loader)
        min_weight, max_weight = get_edge_weight_range(g)
        dot = tr.render("tha_template", g=g, min_weight=min_weight, max_weight=max_weight)
        ofp.write(dot)
