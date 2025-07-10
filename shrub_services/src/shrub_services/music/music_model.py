from typing import List, TypeVar

T = TypeVar("T")

class Song:
    def __init__(self, **kwargs):
        self.id = self.name = self.album = None
        self.artists = []
        if "id" in kwargs:
            self.id = kwargs["id"]
        if "name" in kwargs:
            self.name = kwargs["name"]
        if "href" in kwargs:
            self.href = kwargs["href"]
        if "artist" in kwargs:
            self.artists.append(kwargs["artist"])
        if "artists" in kwargs:
            for artist in kwargs["artists"]:
                self.artists.append(artist)
        if "album" in kwargs:
            self.album = kwargs["album"]

    def to_dict(self) -> dict:
        the_dict = {}
        if self.id:
            the_dict["id"] = self.id
        if self.name:
            the_dict["name"] = self.name
        if self.href:
            the_dict["href"] = self.href
        if self.artists:
            the_dict["artists"] = list[(artist for artist in self.artists)]
        if self.album:
            the_dict["album"] = self.album
        return the_dict

    def from_dict(self, the_dict: dict):
        self.__init__(**the_dict)



class PlayList:
    def __init__(self, **kwargs):
        if "id" in kwargs:
            self.id = kwargs["id"]
        if "href" in kwargs:
            self.href = kwargs["href"]
        if "name" in kwargs:
            self.name = kwargs["name"]
        if "description" in kwargs:
            self.description = kwargs["description"]
        if "owner" in kwargs:
            self.owner = kwargs["owner"]
        if "public" in kwargs:
            self.public = kwargs["public"]

        self.songs: List[Song] = []

    def add_song(self, song: Song):
        self.songs.append(song)


class MusicLocalView:
    def __init__(self):
        self.uuid = 0
        self.all_maps = []
        self.map_playlists: dict = {}
        self.all_maps.append(("playlists", self.map_playlists, PlayList))
        self.map_songs: dict = {}
        self.all_maps.append(("songs", self.map_songs, Song))

    def resolve_item(self, item: T, item_map: dict) -> T:
        result = item
        if item.id not in item_map:
            item_map[item.id] = item
        else:
            result = item_map[item.id]
        return result


    def resolve_playlist(self, playlist: PlayList) -> PlayList:
        return self.resolve_item(playlist, self.map_playlists)

    def resolve_song(self, song: Song) -> Song:
        return self.resolve_item(song, self.map_songs)


    def to_dict(self) -> dict:
        the_dict = {}

        def add_item_map_to_dict(name: str, item_map: dict):
            the_dict[name] = []
            for v in item_map.values():
                the_dict[name].append(v.to_dict())

        for name, item_map, constructur in self.all_maps:
            add_item_map_to_dict(name, item_map)

        return the_dict

    def from_dict(self, the_dict: dict):
        def add_dict_to_item_to_map(name: str, item_map: dict, constructor: T):
            for v in the_dict[name]:
                ne = constructor()
                ne.from_dict(v)
                item_map[ne.id] = ne

        for name, item_map, constructor in self.all_maps:
            add_dict_to_item_to_map(name, item_map, constructor)



