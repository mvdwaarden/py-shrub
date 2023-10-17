from defusedxml import ElementTree
from xml.dom.pulldom import parse, parseString
from shrub_util.core.arguments import Arguments
from networkx import Graph
import networkx as nx
from matplotlib.pyplot import show
import os
from xml.sax.handler import ContentHandler
from xml.sax import parseString as saxParseString
from xml.dom.minidom import Element as minidomElement
from xml.etree.ElementTree import register_namespace
import json
import re

import xmltodict


def clone_xml(xml: str) -> str:
    for event, el in parse(xml):
        print(f"{type(el)}{event}")
        if event == "START_ELEMENT":
            print(f"{type(event)}{event}{type(el)}{el} -> {el.tagName}")



    return "ok"


def xml_to_graph_eltree(xml: str):
    et = ElementTree.fromstring(xml)
    for el in et.iter():
        ns = tag = ""
        match re.match("({(.*)})(.*)", el.tag).groups():
            case [_, ns, tag]:
                ns, tag = ns, tag
            case [tag]:
                tag = tag
            case _:
                print("wtf")

        match ns, tag, el:
            case _:
                print(f"{ns}, {tag}, {el.attrib}, {type(el)}")



def xml_to_graph_sax(xml: str) -> Graph:
    class l_ContentHandler(ContentHandler):
        def startElement(self, name, attrs):
            match name, attrs:
                case name, {"id":id}:
                    print(f"id element : {name}")
                case _:
                    print(f"{name}{attrs}")

        def endElement(self, name):
            pass

    saxParseString(xml,  l_ContentHandler())

def xml_to_graph(xml: str) -> Graph:
    g = Graph()
    node_stack = []
    for event, _el in parseString(xml):
        el = type(_el).__name__
        match event:
            case "START_DOCUMENT":
                print(f"start doc {el}")
            case "END_DOCUMENT":
                print(f"end doc {el}")
            case "START_ELEMENT":
                g.add_node(_el,**{"name": _el.tagName})
                if len(node_stack) > 0:
                    g.add_edge(node_stack[-1], _el, **{"name" : "child"})
                node_stack.append(_el)
                match _el:
                    case minidomElement(childNodes=id,tagName=tag):
                        print(f"start id el {el}: {tag}")
                    case _:
                        print(f"start el {el}, {_el}")
            case "END_ELEMENT":
                node_stack = node_stack[:-1]
                print(f"end el {el}")
            case "CHARACTERS":
                print(f"chars {el}")
            case "COMMENT":
                print(f"comment")
            case "PROCESSING_INSTRUCTION":
                print(f"proc instr {el}")
            case "IGNORABLE_WHITESPACE":
                print(f"whitespace {el}")
            case _:
                print(f"{event}")

    return g

DEF_XML = """<?xml version="1.0"?>
<bck:catalog xmlns="book_namespace" xmlns:bck="book_namespace">
<!-- COMMENT -->   
    <book id="bk101">
        <author>Gambardella, Matthew</author>
        <title>XML Developer's Guide</title>
        <genre>Computer</genre>
        <price>44.95</price>
        <publish_date>2000-10-01</publish_date>
        <description>An in-depth look at creating applications with XML.</description>
    </book>
    <book id="bk102">
        <author>Ralls, Kim</author>
        <title>Midnight Rain</title>
        <genre>Fantasy</genre>
        <price>5.95</price>
        <publish_date>2000-12-16</publish_date>
        <description>A former architect battles corporate zombies, 
        an evil sorceress, and her own childhood to become queen 
        of the world.</description>
    </book>
    <book id="bk103">
        <author>Corets, Eva</author>
        <title>Maeve Ascendant</title>
        <genre>Fantasy</genre>
        <price>5.95</price>
        <publish_date>2000-11-17</publish_date>
        <description>After the collapse of a nanotechnology 
        society in England, the young survivors lay the 
        foundation for a new society.</description>
    </book>
    <book id="bk104">
        <author>Corets, Eva</author>
        <title>Oberon's Legacy</title>
        <genre>Fantasy</genre>
        <price>5.95</price>
        <publish_date>2001-03-10</publish_date>
        <description>In post-apocalypse England, the mysterious 
        agent known only as Oberon helps to create a new life 
        for the inhabitants of London. Sequel to Maeve 
        Ascendant.</description>
    </book>
</bck:catalog>
"""


def test_replace_xml(xml: str):
    namespaces = {"bck": "book_namespace"}
    et = ElementTree.fromstring(xml)
    for pref, uri in namespaces.items():
        register_namespace(pref, uri)
    for el in et.findall("./bck:book[@id='bk104']", namespaces=namespaces):
        el.set("id", "bk104_new_id")
        print(el)
    print(ElementTree.tostring(et).decode("utf8"))



def transform_xml(xml_file: str, xslt_file: str):
    et = ElementTree.parse(xml_file)
    xsl = ElementTree.parse(xslt_file)


def main():
    args = Arguments()
    file = args.get_arg("file")
    xml = None
    if file:
        if os.path.exists(file):
            with open(file) as ofp:
                xml = ofp.read()
    else:
        file = "/tmp/default_file.dat"
    if not xml:
        xml = DEF_XML
    # g = xml_to_graph_sax(xml)
    # g = xml_to_graph(xml)
    # g = xml_to_graph_eltree(xml)
    xml_dict = xmltodict.parse(xml)
    with open(f"/tmp/{os.path.split(file)[-1]}2.json", "w") as ofp:
        ofp.write(json.dumps(xml_dict))
    if False:
        g = relabel_nodes(g, lambda n: f"{n.tagName}-{hash(n)}")
        nx.write_network_text(g)
        ag = nx.nx_agraph.to_agraph(g)
        #ag.draw(f"/tmp/{os.path.split(file)[-1]}.png", prog="neato")
        labels = nx.get_node_attributes(g, "name")

        #nx.draw(g, with_labels=True, labels=labels)
        nx.write_gml(g, f"/tmp/{os.path.split(file)[-1]}2.gml")
        #show()
    elif True:
        test_replace_xml(DEF_XML)


if __name__ == "__main__":
    main()