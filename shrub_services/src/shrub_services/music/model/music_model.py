import shrub_util.core.logging as logging
from typing import List, TypeVar, MutableMapping
import uuid

T = TypeVar("T")

class MusicServiceItem:
    def __init__(self, **kwargs):
        self.id = self.name = self.href = None
        if "id" in kwargs:
            self.id = kwargs["id"]
        if "name" in kwargs:
            self.name = kwargs["name"]
        if "href" in kwargs:
            self.href = kwargs["href"]

    def get_resolve_key(self) -> str:
        result = None
        if self.id:
            result = self.id
        elif self.name:
            result = self.name
        else:
            logging.getLogger().warning(f"unable to determine resolve key")
        return result

    def to_dict(self) -> dict:
        the_dict = {}
        if self.id:
            the_dict["id"] = self.id
        if self.name:
            the_dict["name"] = self.name
        if self.href:
            the_dict["href"] = self.href
        return the_dict

    def from_dict(self, the_dict: dict):
        self.__init__(**the_dict)


class Album(MusicServiceItem):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.liked = None
        self.artists = []
        if "liked" in kwargs:
            self.liked = kwargs["liked"]
        if "artist" in kwargs:
            self.artists.append(kwargs["artist"])
        if "artists" in kwargs:
            for artist in kwargs["artists"]:
                self.artists.append(artist)

    def get_resolve_key(self) -> str:
        result = None
        if self.id:
            result = self.id
        elif self.name and self.artists and len(self.artists) > 0:
            result = f"{self.name}-{self.artists[0].name}"
        elif self.name:
            result = f"{self.name}"
            logging.getLogger().warning(f"using name({self.name}) of the album as resolve key, uniqueness not guaranteed")
        else:
            logging.getLogger().warning(f"unable to determine resolve key for album")
        return result

    def to_dict(self) -> dict:
        the_dict = super().to_dict()
        if self.liked:
            the_dict["liked"] = self.liked
        if self.artists:
            the_dict["artists"] = list([artist.id for artist in self.artists])

        return the_dict


class Artist(MusicServiceItem):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.followed = None
        if "followed" in kwargs:
            self.followed = kwargs["followed"]

    def to_dict(self) -> dict:
        the_dict = super().to_dict()
        if self.followed:
            the_dict["followed"] = self.followed
        return the_dict


class Song(MusicServiceItem):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.artists = []
        if "artist" in kwargs:
            self.artists.append(kwargs["artist"])
        if "artists" in kwargs:
            for artist in kwargs["artists"]:
                self.artists.append(artist)
        if "album" in kwargs:
            self.album = kwargs["album"]

    def to_dict(self) -> dict:
        the_dict = super().to_dict()
        if self.artists:
            the_dict["artists"] = list([artist.id for artist in self.artists])
        if self.album:
            the_dict["album"] = self.album.id
        return the_dict

    def get_resolve_key(self) -> str:
        result = None
        if self.id:
            result = self.id
        elif self.name and self.artists:
            result = f"{self.name}-{self.artists[0].name}"
        else:
            logging.getLogger().warning(f"unable to determine resolve key for song")
        return result



class PlayList(MusicServiceItem):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.description = self.owner = self.public = None
        self.songs: List[Song] = []
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


class MusicLocalView:
    def __init__(self):
        self.uuid = 0
        self.all_maps = []
        self.map_playlists: MutableMapping[str,PlayList] = {}
        self.map_songs: MutableMapping[str, Song] = {}
        self.map_artists: MutableMapping[str, Artist] = {}
        self.map_albums: MutableMapping[str, Album] = {}
        self.all_maps.append(("map_playlists", self.map_playlists, PlayList))
        self.all_maps.append(("map_songs", self.map_songs, Song))
        self.all_maps.append(("map_albums", self.map_albums, Album))
        self.all_maps.append(("map_artists", self.map_artists, Artist))

    def _get_resolve_key(self, item: T) -> str:
        rk = None
        if hasattr(item, "get_resolve_key"):
            rk = item.get_resolve_key()
        if not rk:
            if hasattr(item,"id") and item.id:
                rk = item.id
        if not rk:
            if hasattr(item,"name") and item.name:
                rk = item.name
        return rk

    def _find_item_by_resolve_key(self,name: str,  item_map: MutableMapping[str, T]):
        result = None
        for item in item_map.values():
            if hasattr(item, "name"):
                if item.name == name:
                    result = item
                    break
        return result

    def resolve_item(self, item: T, item_map: MutableMapping[str,T]) -> T:
        result = item
        if not hasattr(item,"id") or not item.id:
            resolved_item = self._find_item_by_resolve_key(self._get_resolve_key(item), item_map)
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
        resolved_album = self.resolve_item(album, self.map_albums)
        if resolved_album != album and (album.artists and len(album.artists) > 0) and resolved_album.artists and len(resolved_album.artists) == 0:
            for artist in album.artists:
                resolved_album.artists.append(artist)
        return resolved_album


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
                if v:
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
            if not hasattr(song, "album"):
                logging.getLogger().error(f"song ({song.name}) has no album")
            else:
                song.album = self.resolve_album(Album(id=song.album))

        for album in self.map_albums.values():
            album.artists = [self.resolve_artist(Artist(id=id)) for id in album.artists]


