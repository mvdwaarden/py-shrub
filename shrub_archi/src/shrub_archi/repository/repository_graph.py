import networkx as nx

from shrub_archi.model.model import Relation, Identity
from shrub_archi.repository.repository import CoArchiRepository


class RepositoryGrapher:
    """Merges repository 2 to repository 1, considers
        - if identities in repo1 already exists, the copied identity is ignored
        - if an artefact is copied, all resolved id's that exist in repo 1 are replaced
     """

    def create_graph(repo: CoArchiRepository) -> nx.Graph:
        g = nx.DiGraph()
        for elem in repo.elements:
            g.add_node(elem)
        for rel in repo.relations:
            g.add_edge(rel.source, rel.target)

        def to_stringer(thingy):
            match thingy:
                case Relation():
                    return thingy.name if thingy.name else ""
                case Identity():
                    return thingy.name

                case _:
                    return "?"

        nx.write_gml(g, "/tmp/graph.gml", to_stringer)
