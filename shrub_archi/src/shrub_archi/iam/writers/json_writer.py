import json
from shrub_archi.iam.model.iam_model import IamLocalView


def iam_write_json(local_view: IamLocalView, file: str):
    with open(f"{file}.json", "w") as ofp:
        ofp.write(json.dumps(local_view.to_dict()))
    with open(f"{file}-users-only.json", "w") as ofp:
        ofp.write(json.dumps([u.email for u in local_view.map_identities.values() if u.email]))

