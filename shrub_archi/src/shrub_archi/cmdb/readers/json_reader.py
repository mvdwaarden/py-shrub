import json
from ..model.cmdb_model import CmdbLocalView


def read_json(local_view: CmdbLocalView, file: str):
    with open(f"{file}.json", "r") as opf:
        local_view.from_dict(json.loads(opf.read()))