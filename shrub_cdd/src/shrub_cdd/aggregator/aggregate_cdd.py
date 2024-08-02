from networkx import Graph, DiGraph

from shrub_cdd.model.model import Node, EDGE_ATTRIBUTE_WEIGHT


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
