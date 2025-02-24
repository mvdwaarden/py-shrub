import json
import hashlib
from shrub_archi.iam.model.iam_model import IamLocalView


def iam_write_json(local_view: IamLocalView, file: str):
    l_file = f"{file}.json"
    with open(l_file, "w") as ofp:
        data = json.dumps(local_view.to_dict())
        print(f"write {l_file} with SHA1 hash {hashlib.sha1(data.encode()).hexdigest()}")
        ofp.write(data)
    l_file = f"{file}-users-only.json"
    with open(l_file, "w") as ofp:
        data = json.dumps([u.email for u in local_view.map_identities.values() if u.email])
        print(f"write {l_file} with SHA1 hash {hashlib.sha1(data.encode()).hexdigest()}")
        ofp.write(data)
