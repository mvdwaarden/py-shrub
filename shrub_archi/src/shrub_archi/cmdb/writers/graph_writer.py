import shrub_util.core.logging as logging
from shrub_util.generation.template_renderer import TemplateRenderer, get_dictionary_loader
from enum import Enum
from ..model.cmdb_model import CmdbLocalView, NamedItem, ConfigurationItem
from typing import Callable


class GraphType(Enum):
    DOT = "dot"
    GRAPHML = "graphml"
    CYPHER = "cypher"


DOT_TEMPLATE = """
           digraph "{{g.name}}" {
               rankdir=LR
               {% for s,d in g.edges %}
                   {% set relation_type = g.get_edge_data(s,d)["relation_type"] %}
                   "{{ s.name }}" -> "{{ d.name }}" [label={{relation_type}}]
               {% endfor %}
               {% for n in g.nodes %}
                   "{{ n.name }}" [shape={{ dot_shaper(n) }}]
               {% endfor %}
           }
           """

GRAPHML_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<graphml edgedefault="directed" 
        xmlns="http://graphml.graphdrawing.org/xmlns" 
        xmlns:java="http://www.yworks.com/xml/yfiles-common/1.0/java" 
        xmlns:sys="http://www.yworks.com/xml/yfiles-common/markup/primitives/2.0" 
        xmlns:x="http://www.yworks.com/xml/yfiles-common/markup/2.0" 
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
        xmlns:y="http://www.yworks.com/xml/graphml" 
        xmlns:yed="http://www.yworks.com/xml/yed/3" 
        xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns http://www.yworks.com/xml/schema/graphml/1.1/ygraphml.xsd">
    <key for="node" id="d0" yfiles.type="nodegraphics"/>
    <key for="edge" id="d1" yfiles.type="edgegraphics"/>
    <key for="node" id="d2" yfiles.foldertype="group"/>        
    <key for="node" id="d3" attr.name="description" attr.type="string"/>
    <key for="node" id="d4" attr.name="text" attr.type="string"/>
    <graph id="{{ g.name }}">  
        {% for n in g.nodes %}
        <node id="{{ n.id }}">
            <data key="d0">
                <y:ShapeNode>
                  <y:NodeLabel>{{ n.name }}</y:NodeLabel>
                  <y:Shape type="roundrectangle"/>
                </y:ShapeNode>
            </data>
        </node>
        {% endfor %}  
        {% for s,d in g.edges %}
        {% set relation_type = g.get_edge_data(s,d)["relation_type"] %}
        <edge id="{{ s.name }}-({{ relation_type }})->{{ d.name }}" source="{{ s.id }}" target="{{ d.id }}">
            <data key="d1">
                <y:PolyLineEdge>
                  <y:Arrows source="none" target="standard"/>
                  <y:EdgeLabel placement="anywhere" side="anywhere" sideReference="relative_to_edge_flow">{{ relation_type }}</y:EdgeLabel>
                  <y:BendStyle smoothed="true"/>
                </y:PolyLineEdge>
            </data>
        </edge>
        {% endfor %}      
    </graph>       
</graphml>
"""

CYPHER_TEMPLATE = """
{% for n in g.nodes %}
{% set node_type = n.type if n.__class__.__name__ == "ConfigurationItem" else n.__class__.__name__ %}
CREATE ({{ n.__class__.__name__ }}{{ n.id }}:{{ node_type }} {name: '{{ n.name }}'})
{% endfor %}  
{% for s,d in g.edges %}
{% set relation_type = g.get_edge_data(s,d)["relation_type"] %}
CREATE ({{ s.__class__.__name__ }}{{ s.id }}) -[:{{ 'relation_type' }}]-> ({{ d.__class__.__name__ }}{{ d.id }})
{% endfor %}                 
"""


def write_named_item_graph(local_view: CmdbLocalView, graph_type: GraphType, file: str,
                           node_filter: Callable[[NamedItem], bool] = False):
    local_view.build_graph(node_filter=node_filter)
    with open(f"{file}.{graph_type.value}", "w") as ofp:
        def dot_shaper(n) -> str:
            if isinstance(n, ConfigurationItem):
                if n.type and  n.type in ["application", "subapplication"]:
                    return "component"
                elif n.type and n.type in ["database"]:
                    return "cylinder"
            return "Mrecord"

        tr = TemplateRenderer({
            GraphType.DOT.value: DOT_TEMPLATE,
            GraphType.GRAPHML.value: GRAPHML_TEMPLATE,
            GraphType.CYPHER.value:  CYPHER_TEMPLATE}, get_loader=get_dictionary_loader)
        graph_output = tr.render(graph_type.value, g=local_view.graph, node_filter=node_filter, dot_shaper=dot_shaper)
        ofp.write(graph_output)