import json
from shrub_archi.oia.model.oia_model import OiaLocalView


def oia_read_json(local_view: OiaLocalView, file: str) -> OiaLocalView:
    with open(f"{file}.json", "r") as ifp:
        local_view.from_dict(json.loads(ifp.read()))

    return local_view