import concurrent.futures
import logging

from spotipy.oauth2 import SpotifyOAuth
from spotipy import Spotify
import requests
from typing import List
from shrub_ui.ui.select_ui import do_show_select_ui, TableSelectModel
from concurrent.futures import ThreadPoolExecutor


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

        self.songs: List[Song] = []

    def add_song(self, song: Song):
        self.songs.append(song)


class MusicServiceApi:
    def __init__(self):
        ...

    def search_song(self, name, artist) -> Song:
        ...

    def get_playlist(self, playlist: PlayList) -> PlayList:
        ...

    def get_playlists(self) -> List[PlayList]:
        ...

    def create_or_update_playlist(self, playlist: PlayList):
        ...


class AppleMusicApi(MusicServiceApi):
    APPLE_MUSIC_API_BASE = "https://api.music.apple.com/v1/"

    def __init__(self, dev_token, user_token):
        super().__init__()
        self.dev_token = dev_token
        self.user_token = user_token

    def search_song(self, name, artist) -> Song:
        query = f"{name} {artist}"
        response = requests.get(
            url=f"{self.APPLE_MUSIC_API_BASE}/catalog/us/search",
            headers=self._get_headers(),
            params={'term': query, 'limit': 1, 'types': 'songs'}
        )
        try:
            results = response.json()
            item = results["results"]["songs"]["data"][0]
            result = Song(
                id=item["id"],
                artist=item["attributes"]["artistName"],
                name=item["attributes"]["name"],
                href=item["href"],
                album=item["attributes"]["albumName"]
            )
        except Exception as ex:
            logging.getLogger().error(f"problem finding song name({name}),artist({artist}) : error({ex})")
            result = None
        return result

    def create_or_update_playlist(self, playlist: PlayList):
        data = {
            'attributes': {
                'name': playlist.name,
                'description': playlist.description
            },
            'relationships': {
                'tracks': {
                    'data': [{'id': song.id, 'type': 'songs'} for song in playlist.songs]
                }
            }
        }
        response = requests.post(
            url=f"{self.APPLE_MUSIC_API_BASE}/me/library/playlists",
            headers=self._get_headers(has_request=True),
            json=data)
        if response.status_code == 201:
            print("Apple Music playlist created.")
        else:
            print("Failed to create Apple Music playlist:", response.text)

    def get_playlists(self) -> List[PlayList]:
        ...

    def get_playlist(self, playlist: PlayList) -> PlayList:
        response = requests.get(
            url=f"{self.APPLE_MUSIC_API_BASE}/me/library/playlists",
            headers=self._get_headers(has_request=True))

        if response.status_code == 201:
            print("Apple Music playlist created.")
        else:
            print("Failed to create Apple Music playlist:", response.text)

    def _get_headers(self, has_request: bool = False):
        headers = {
            'Authorization': f'Bearer {self.dev_token}',
            'Music-User-Token': self.user_token
        }
        if has_request:
            headers['Content-Type'] = 'application/json'
        return headers


class SpotifyApi(MusicServiceApi):
    SCOPE = "playlist-read-private playlist-modify-private playlist-modify-public"

    def __init__(self, client_id, client_secret, redirect_uri):
        super().__init__()
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.sp_handle: Spotify = None

    def _get_spotify_handle(self) -> Spotify:
        if not self.sp_handle:
            self.sp_handle = Spotify(auth_manager=SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=SpotifyApi.SCOPE
            ))
        return self.sp_handle

    def get_playlists(self) -> List[PlayList]:
        result = self._get_spotify_handle().current_user_playlists()
        playlists = []
        for item in result["items"]:
            playlists.append(
                PlayList(id=item["id"], description=item["description"], name=item["name"], href=item["href"],
                         owner=item["owner"]["display_name"]))
        return playlists

    def get_playlist(self, playlist: PlayList) -> PlayList:
        offset = 0
        while True:
            result = self._get_spotify_handle().playlist_items(playlist_id=playlist.id, limit=100, offset=offset,
                                                               fields="items(track(id,name,href,album(name),artists(name)")
            result_count = 0
            if "items" in result:
                result_count = len(result["items"])
            for item in result["items"]:
                if "track" in item:
                    try:
                        playlist.add_song(
                            Song(
                                id=item["track"]["id"],
                                artists=[artist["name"] for artist in item["track"]["artists"]],
                                name=item["track"]["name"], album=item["track"]["album"]["name"],
                                href=item["track"]["href"]))
                    except Exception as ex:
                        ...
            if result_count < 100:
                break
            else:
                offset += result_count
        return playlist

    def search_song(self, name, artist):
        query = f"{name} {artist}"
        result = self._get_spotify_handle().search(q=query, type='track', limit=1)
        try:
            return result['tracks']['items'][0]['uri']
        except IndexError:
            return None

    def create_or_update_playlist(self, playlist: PlayList):
        user_id = self._get_spotify_handle().current_user()['id']
        playlist = self._get_spotify_handle().user_playlist_create(user=user_id, name=playlist.name, public=False)
        self._get_spotify_handle().playlist_add_items(playlist_id=playlist['id'],
                                                      items=[song.href for song in playlist.songs])
        print(f"Spotify playlist created: {playlist['external_urls']['spotify']}")


class Synchronizer:
    def __init__(self, src: MusicServiceApi, dst: MusicServiceApi):
        self.src: MusicServiceApi = src
        self.dst: MusicServiceApi = dst

    def select_playlists(self, playlists: List[PlayList]):
        class PlaylistSelectModel(TableSelectModel):
            COL_COUNT = 4  # Number of columns including checkbox
            HEADER_LABELS = ["", "Name", "Descriptions", "Owner", "#Songs"]  # Headers for your columns

            def column_value_for(self, row, column: int):
                if column == 0:  # Assuming the first column is for checkbox
                    return ""
                elif column == 1:
                    return row.name
                elif column == 2:
                    return row.description
                elif column == 3:
                    return row.owner
                elif column == 4:
                    return len(row.songs)

            def hit_row(self, row, search_text: str):
                return (
                        search_text in row.name.lower()
                        or search_text in row.description.lower()
                        or search_text in row.owner.lower()
                )

            def row_hash(self, row):
                return row

        ok, selection = do_show_select_ui(model=PlaylistSelectModel(playlists), ok_text="Select Playlists")

        if ok:
            result = list([playlist for playlist, selected in selection.items() if selected])
        else:
            result = []
        return result

    def sychronize_playlists(self):
        playlists = self.src.get_playlists()

        selected_playlists = self.select_playlists(playlists)
        futures = []
        with ThreadPoolExecutor() as executor:
            for playlist in selected_playlists:
                futures.append(executor.submit(self.synchronize_playlist, playlist))
            for future in concurrent.futures.as_completed(futures):
                print(future.result())

    def synchronize_playlist(self, playlist: PlayList):
        not_found = 0
        target_playlist = PlayList()
        target_playlist.name = playlist.name
        target_playlist.description = playlist.description
        self.src.get_playlist(playlist)
        for song in playlist.songs:
            s = self.dst.search_song(song.name, song.artists[0])
            if not s:
                not_found += 1
            else:
                target_playlist.add_song(s)
            print(f"{song.id} : {song.name}")
        self.dst.create_or_update_playlist(playlist)
        print(f"synchronized playlist {playlist.name}, could not find {not_found} songs")

    def transfer_playlist(self, playlist: PlayList):
        ...
        # print("Fetching Spotify playlist...")
        # tracks = get_spotify_playlist_tracks(playlist_id)
        # print("Searching Apple Music...")
        # apple_ids = [search_apple_music_track(t['name'], t['artist']) for t in tracks]
        # create_apple_music_playlist("From Spotify", apple_ids)
