from enum import Enum
from typing import Callable

from shrub_archi.cmdb.model.cmdb_model import CmdbLocalView, NamedItem, ConfigurationItem, Manager, ConfigAdmin, \
    NamedItemRelation
from shrub_util.generation.template_renderer import TemplateRenderer, get_dictionary_loader


class GraphType(Enum):
    DOT = "dot"
    GRAPHML = "graphml"
    CYPHER = "cypher"


DOT_TEMPLATE = """
           digraph "{{g.name}}" {
               rankdir=LR
               {% for s,d in g.edges %}
                   {% set relation_type = g.get_edge_data(s,d)["relation_type"] %}
                   "{{ s.name }}" -> "{{ d.name }}" [label="{{ relation_type }}"]
               {% endfor %}
               {% for n in g.nodes %}
                   "{{ n.name }}" [label="{{ dot_node_namer(n) }}", shape={{ dot_shaper(n) }}]
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
CREATE ({{ n.__class__.__name__ }}{{ n.id }}:{{ node_type }} {{ cypher_node_namer(n) }})
{% endfor %}  
{% for s,d in g.edges %}
{% set relation_type = g.get_edge_data(s,d)["relation_type"] %}
CREATE ({{ s.__class__.__name__ }}{{ s.id }}) -[:{{ cypher_relation_namer(relation_type) }}]-> ({{ d.__class__.__name__ }}{{ d.id }})
{% endfor %}                 
"""


def cmdb_write_named_item_graph(local_view: CmdbLocalView, graph_type: GraphType, file: str,
                                include_object_reference: bool = True, node_filter: Callable[[NamedItem], bool] = False):
    g = local_view.build_graph(include_object_reference=include_object_reference, node_filter=node_filter)

    with open(f"{file}.{graph_type.value}", "w") as ofp:
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

        tr = TemplateRenderer({GraphType.DOT.value: DOT_TEMPLATE, GraphType.GRAPHML.value: GRAPHML_TEMPLATE,
            GraphType.CYPHER.value: CYPHER_TEMPLATE}, get_loader=get_dictionary_loader)
        graph_output = tr.render(graph_type.value, g=g, node_filter=node_filter, dot_shaper=dot_shaper,
                                 default_node_namer=node_namer, dot_node_namer=dot_node_namer,
                                 cypher_node_namer=cypher_node_namer, cypher_relation_namer=cypher_relation_namer)
        ofp.write(graph_output)
