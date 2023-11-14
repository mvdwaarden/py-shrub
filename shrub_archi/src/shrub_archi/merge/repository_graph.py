import concurrent.futures
import os
import time
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from typing import Optional, List

import shrub_util.core.logging as logging
from shrub_archi.merge.identity import Identities
from shrub_archi.merge.identity_resolver import ResolvedIdentity, \
    RepositoryResolver, IdentityResolver, NaiveIdentityResolver, ResolutionStore
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
        nx.write_graphml(g, "/tmp/graph.gml", prettyprint=True)
