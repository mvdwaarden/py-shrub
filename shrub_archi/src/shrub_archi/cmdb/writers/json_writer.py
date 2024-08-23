import json
from ..model.cmdb_model import CmdbLocalView


def cmdb_write_json(local_view: CmdbLocalView, file: str):
    with open(f"{file}.json", "w") as opf:
        opf.write(json.dumps(local_view.to_dict()))

