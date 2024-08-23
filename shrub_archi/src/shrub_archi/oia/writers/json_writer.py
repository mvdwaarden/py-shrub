import json
from shrub_archi.oia.model.oia_model import OiaLocalView


def oia_write_json(local_view: OiaLocalView, file: str):
    with open(file, "w") as ofp:
        ofp.write(json.dumps(local_view.to_dict()))