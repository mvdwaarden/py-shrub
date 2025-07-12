from typing import List, TypeVar, MutableMapping
import uuid

T = TypeVar("T")

class Album:
    def __init__(self, **kwargs):
        self.id = self.name = self.href = self.liked = None
        self.artists = []
        if "id" in kwargs:
            self.id = kwargs["id"]
        if "name" in kwargs:
            self.name = kwargs["name"]
        if "href" in kwargs:
            self.href = kwargs["href"]
        if "liked" in kwargs:
            self.liked = kwargs["liked"]
        if "artist" in kwargs:
            self.artists.append(kwargs["artist"])
        if "artists" in kwargs:
            for artist in kwargs["artists"]:
                self.artists.append(artist)

    def to_dict(self) -> dict:
        the_dict = {}
        if self.id:
            the_dict["id"] = self.id
        if self.name:
            the_dict["name"] = self.name
        if self.href:
            the_dict["href"] = self.href
        if self.liked:
            the_dict["liked"] = self.liked
        if self.artists:
            the_dict["artists"] = list([artist.id for artist in self.artists])

        return the_dict

    def from_dict(self, the_dict: dict):
        self.__init__(**the_dict)

class Artist:
    def __init__(self, **kwargs):
        self.id = self.name = self.href = self.followed = None
        if "id" in kwargs:
            self.id = kwargs["id"]
        if "name" in kwargs:
            self.name = kwargs["name"]
        if "href" in kwargs:
            self.href = kwargs["href"]
        if "followed" in kwargs:
            self.followed = kwargs["followed"]

    def to_dict(self) -> dict:
        the_dict = {}
        if self.id:
            the_dict["id"] = self.id
        if self.name:
            the_dict["name"] = self.name
        if self.href:
            the_dict["href"] = self.href
        if self.followed:
            the_dict["followed"] = self.followed
        return the_dict

    def from_dict(self, the_dict: dict):
        self.__init__(**the_dict)

class Song:
    def __init__(self, **kwargs):
        self.id = self.name = self.album = self.href = None
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
            the_dict["artists"] = list([artist.id for artist in self.artists])
        if self.album:
            the_dict["album"] = self.album.id
        return the_dict

    def from_dict(self, the_dict: dict):
        self.__init__(**the_dict)



class PlayList:
    def __init__(self, **kwargs):
        self.id = self.href = self.name = self.description = self.owner = self.public = None
        self.songs: List[Song] = []
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
        if "songs" in kwargs:
            self.songs = kwargs["songs"]

    def add_song(self, song: Song):
        self.songs.append(song)

    def to_dict(self) -> dict:
        the_dict = {}
        if self.id:
            the_dict["id"] = self.id
        if self.name:
            the_dict["name"] = self.name
        if self.href:
            the_dict["href"] = self.href
        if self.description:
            the_dict["description"] = self.description
        if self.public:
            the_dict["public"] = self.public
        the_dict["songs"] = list([song.id for song in self.songs])

        return the_dict

    def from_dict(self, the_dict: dict):
        self.__init__(**the_dict)


class MusicLocalView:
    def __init__(self):
        self.uuid = 0
        self.all_maps = []
        self.map_playlists: MutableMapping[str,PlayList] = {}
        self.map_songs: MutableMapping[str, Song] = {}
        self.map_artists: MutableMapping[str, Artist] = {}
        self.map_albums: MutableMapping[str, Album] = {}
        self.all_maps.append(("playlists", self.map_playlists, PlayList))
        self.all_maps.append(("songs", self.map_songs, Song))
        self.all_maps.append(("albums", self.map_albums, Album))
        self.all_maps.append(("artists", self.map_artists, Artist))

    def _find_item_by_name(self,name: str,  item_map: MutableMapping[str, T]):
        result = None
        for item in item_map.values():
            if hasattr(item, "name"):
                if item.name == name:
                    result = item
                    break
        return result

    def resolve_item(self, item: T, item_map: MutableMapping[str,T]) -> T:
        result = item
        if (not hasattr(item,"id") or not item.id) and hasattr(item, "name"):
            resolved_item = self._find_item_by_name(item.name, item_map)
            if resolved_item:
                result = resolved_item
            else:
                item.id = f"shrub_generated-{uuid.uuid4()}"
                item_map[item.id] = item
        elif item.id not in item_map:
            item_map[item.id] = item
        else:
            result = item_map[item.id]
        return result


    def resolve_playlist(self, playlist: PlayList) -> PlayList:
        return self.resolve_item(playlist, self.map_playlists)

    def resolve_song(self, song: Song) -> Song:
        return self.resolve_item(song, self.map_songs)

    def resolve_artist(self, artist: Artist) -> Artist:
        return self.resolve_item(artist, self.map_artists)

    def resolve_album(self, album: Album) -> Album:
        return self.resolve_item(album, self.map_albums)


    def to_dict(self) -> dict:
        the_dict = {}

        def add_item_map_to_dict(name: str, item_map: MutableMapping[str, T]):
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

        for playlist in self.map_playlists.values():
            for i in range(0, len(playlist.songs)):
                playlist.songs[i] = self.resolve_song(Song(id=playlist.songs[i]))

        for song in self.map_songs.values():
            song.artists = [self.resolve_artist(Artist(id=id)) for id in song.artists]
            song.album = self.resolve_album(Album(id=song.album))

        for album in self.map_albums.values():
            album.artists = [self.resolve_artist(Artist(id=id)) for id in album.artists]


