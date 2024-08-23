import json
from shrub_archi.oia.model.oia_model import OiaLocalView


def oia_write_json(local_view: OiaLocalView, file: str):
    with open(f"{file}.json", "w") as ofp:
        ofp.write(json.dumps(local_view.to_dict()))
    with open(f"{file}-users-only.json", "w") as ofp:
        ofp.write(json.dumps([u.email for u in local_view.map_identities.values() if u.email]))

