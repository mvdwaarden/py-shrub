import concurrent.futures
import os
import time
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from typing import Optional, List

import shrub_util.core.logging as logging
from shrub_archi.merge.identity import  Identity
from shrub_archi.merge.relation import  Relation
import networkx as nx
from shrub_archi.merge.repository import Repository


class RepositoryGrapher:
    """Merges repository 2 to repository 1, considers
        - if identities in repo1 already exists, the copied identity is ignored
        - if an artefact is copied, all resolved id's that exist in repo 1 are replaced
     """

    def create_graph(repo: Repository) -> nx.Graph:
        g = nx.DiGraph()
        for elem in repo.elements:
            g.add_node(elem)
        for rel in repo.relations:
            g.add_edge(rel.source, rel.target)
        def to_stringer(thingy):
            match thingy:
                case Identity():
                    return thingy.name
                case Relation():
                    return thingy.name if thingy.name else ""
                case _: return "?"
        nx.write_gml(g, "/tmp/graph.gml", to_stringer)
