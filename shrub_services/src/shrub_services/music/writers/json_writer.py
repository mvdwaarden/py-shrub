import json
from shrub_services.music.music_model import MusicLocalView


def music_write_json(local_view: MusicLocalView, file: str):
    with open(f"{file}.json", "w") as opf:
        opf.write(json.dumps(local_view.to_dict()))
