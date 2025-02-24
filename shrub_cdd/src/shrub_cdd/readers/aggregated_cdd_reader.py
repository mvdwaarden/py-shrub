from networkx import DiGraph
import json
import re

from shrub_cdd.model.model import Node


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
