import json
import hashlib
from shrub_archi.iam.model.iam_model import IamLocalView


def iam_read_json(local_view: IamLocalView, file: str) -> IamLocalView:
    l_file = f"{file}.json"
    with open(l_file, "r") as ifp:
        data = ifp.read()
        print(f"read {l_file} with SHA1 hash {hashlib.sha1(data.encode()).hexdigest()}")
        local_view.from_dict(json.loads(data))

    return local_view
