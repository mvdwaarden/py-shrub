import json
from shrub_archi.iam.model.iam_model import IamLocalView


def iam_read_json(local_view: IamLocalView, file: str) -> IamLocalView:
    with open(f"{file}.json", "r") as ifp:
        local_view.from_dict(json.loads(ifp.read()))

    return local_view
