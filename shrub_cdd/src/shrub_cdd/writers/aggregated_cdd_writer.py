from typing import Tuple

from networkx import Graph, write_graphml

from shrub_cdd.model.model import EDGE_ATTRIBUTE_WEIGHT
from shrub_util.generation.template_renderer import DictionaryRenderer

DOT_TEMPLATE = """
digraph "{{g.name}}" {
    rankdir=LR
    {% for n in g.nodes %}
        "{{ n.attribute }}" [shape=Mrecord]
    {% endfor %}
    {% for s,d in g.edges %}
        {% set weight = g.get_edge_data(s,d)["weight"] %}
        {% set thinkness = 100*(weight-min_weight)/(max_weight - min_weight) + 1 %}
        "{{ s.attribute }}" -> "{{ d.attribute }}" [weight={{weight}}, penwidth={{thinkness}}]
    {% endfor %}
}
"""


def write_aggregated_dot(g: Graph, file: str):
    with open(f"{file}.dot", "w") as ofp:
        tr = DictionaryRenderer({"tha_template": DOT_TEMPLATE})
        min_weight, max_weight = get_edge_weight_range(g)
        dot = tr.render("tha_template", g=g, min_weight=min_weight, max_weight=max_weight)
        ofp.write(dot)


def write_aggregated_graph(g: Graph, file: str):
    min_weight, max_weight = get_edge_weight_range(g)
    write_graphml(g, f"{file}.graphml")
    write_aggregated_dot(g, file)


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
