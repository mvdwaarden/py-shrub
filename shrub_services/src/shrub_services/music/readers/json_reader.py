from shrub_services.music.music_model import MusicLocalView
import json

def music_read_json(local_view: MusicLocalView, file: str):
    with open(f"{file}.json", "r") as opf:
        local_view.from_dict(json.loads(opf.read()))