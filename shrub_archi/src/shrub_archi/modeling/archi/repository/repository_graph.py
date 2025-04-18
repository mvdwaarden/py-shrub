import os

import networkx as nx

from shrub_archi.modeling.archi.model.archi_model import Relation, Entity
from shrub_archi.modeling.archi.repository.repository import Repository


class RepositoryGrapher:
    """Generates graph GML"""

    def create_graph(self, repo: Repository, work_dir: str = None) -> nx.Graph:
        g = nx.DiGraph()
        for elem in repo.elements:
            g.add_node(elem)
        for rel in repo.relations:
            g.add_edge(rel.source, rel.target)

        def to_stringer(thingy):
            match thingy:
                case Relation():
                    return thingy.name if thingy.name else ""
                case Entity():
                    return thingy.name

                case _:
                    return "?"

        filename = os.path.join(
            f"{work_dir if work_dir else 'tmp'}", f"{repo.file_name}.gml"
        )
        nx.write_gml(g, filename, to_stringer)
        return g
