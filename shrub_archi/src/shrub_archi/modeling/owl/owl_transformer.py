from shrub_util.generation.template_renderer import TemplateRenderer, DictionaryRenderer
from owlready2 import get_ontology, Ontology
import networkx as nx
import matplotlib.pyplot as plt

# Jinja2 template for textual representation
OWL_RENDERER = "OWL_RENDERER"
OWL_2_TEXT_RENDERER_TEMPLATE = """
Ontology Classes and Properties:

{% for cls in classes %}
Class: {{ cls.name }}
SuperClass: {{ cls.is_a[0].name if cls.is_a is not none else "tha root "}}
{% endfor %}

Object Properties:

{% for prop in properties %}
Property: {{ prop.name }}
Domain: {{ prop.domain[0]  if prop.domain is not none else "" }}
Range: {{ prop.range[0] if prop.range is not none else "" }}
{% endfor %}
"""


def owl_get_verbalization_renderer():
    return DictionaryRenderer({
        OWL_RENDERER: OWL_2_TEXT_RENDERER_TEMPLATE
    })


def owl_read_ontology(file: str) -> Ontology:
    return get_ontology(file).load()


def owl_verbalize(ontology: Ontology) -> str:
    return owl_renderer_transform(ontology, owl_get_verbalization_renderer())


def owl_renderer_transform(ontology: Ontology, renderer: TemplateRenderer):
    classes = list(ontology.classes())
    properties = list(ontology.object_properties())
    for cls in classes:
        print(cls)
        super_cls = cls.is_a
        super_cls_name = cls.is_a[0].name if cls.is_a else ""
    for prop in properties:
        print(prop)
        if prop.domain:
            domain = prop.domain
            print(prop.domain[0])
        if prop.range:
            _range = prop.range
            print(prop.range[0])
    result = renderer.render(OWL_RENDERER, classes=classes, properties=properties)
    return result


def owl_graph_transform(onto):
    # Create a NetworkX graph
    G = nx.DiGraph()

    # Add nodes and edges from the ontology
    for cls in onto.classes():
        G.add_node(cls.name)
        for sub_cls in cls.subclasses():
            G.add_edge(cls.name, sub_cls.name, label="subclass")

    for prop in onto.object_properties():
        for domain in prop.domain:
            for range_ in prop.range:
                G.add_edge(domain.name, range_.name, label=prop.name)

    # Draw the graph
    pos = nx.spring_layout(G)
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw(G, pos, with_labels=True, node_size=3000, node_color="skyblue", font_size=10, font_weight="bold")
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red')

    # Show the plot
    plt.show()
