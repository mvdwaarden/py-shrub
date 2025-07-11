import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List

import requests
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth

from shrub_services.music.model.music_model import Album, Artist, PlayList, Song, MusicLocalView
from shrub_ui.ui.select_ui import do_show_select_ui, TableSelectModel


class MusicServiceApi:
    def __init__(self, local_view: MusicLocalView = None):
        if not local_view:
            self.local_view = MusicLocalView()
        else:
            self.local_view: MusicLocalView = local_view

    def search_song(self, name, artist) -> Song:
        ...

    def get_playlist(self, playlist: PlayList) -> PlayList:
        ...

    def get_playlists(self) -> List[PlayList]:
        ...

    def get_followed_artists(self) -> List[Artist]:
        ...

    def get_liked_albums(self) -> List[Album]:
        ...

    def create_or_update_playlist(self, playlist: PlayList):
        ...


class MusicLocalViewApi(MusicServiceApi):
    def __init__(self, local_view: MusicLocalView):
        super().__init__(local_view)

    def search_song(self, name, artist) -> Song:
        ...

    def get_playlist(self, playlist: PlayList) -> PlayList:
        return self.local_view.resolve_playlist(playlist=playlist)

    def get_playlists(self) -> List[PlayList]:
        return list(self.local_view.map_playlists.values())

    def create_or_update_playlist(self, playlist: PlayList):
        ...


class AppleMusicApi(MusicServiceApi):
    APPLE_MUSIC_API_BASE = "https://api.music.apple.com/v1"

    def __init__(self, dev_token, user_token):
        super().__init__()
        self.dev_token = dev_token
        self.user_token = user_token

    def search_song(self, name, artist) -> Song:
        query = f"{name} {artist.name}"
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
            logging.getLogger().info(f"found song name({name}),artist({artist}) -> id({result.id})")
        except Exception as ex:
            logging.getLogger().error(f"problem finding song name({name}),artist({artist}) : error({ex})")
            result = None
        return result

    def create_or_update_playlist(self, playlist: PlayList):
        def create_playlist(playlist: PlayList) -> str:
            data = {
                'attributes': {
                    'name': playlist.name,
                    'description': playlist.description,
                    'isPublic': False  # playlist.public
                }
            }
            response = requests.post(
                url=f"{self.APPLE_MUSIC_API_BASE}/me/library/playlists",
                headers=self._get_headers(has_request=True),
                json=data)
            playlist_id = None
            if response.status_code == 201:
                result = response.json()
                playlist_id = result["data"][0]["id"]
                logging.getLogger().info(f"Apple Music playlist created with name({playlist.name}), id({playlist_id})")
            else:
                logging.getLogger().info(
                    f"Failed to create Apple Music playlist with name({playlist.name}, id({response.text}))")
            return playlist_id

        def add_playlist_songs(playlist_id: str, songs: List[Song]):
            data = {"data": [{
                'id': song.id,
                'type': 'songs'

            } for song in songs]}
            response = requests.post(
                url=f"{self.APPLE_MUSIC_API_BASE}/me/library/playlists/{playlist_id}/tracks",
                headers=self._get_headers(has_request=True),
                json=data
            )
            if 200 <= response.status_code < 300:
                logging.getLogger().info(f"Added {len(songs)} songs to Apple Music playlist name({playlist.name})")

        playlist_id = create_playlist(playlist)
        if playlist_id:
            add_playlist_songs(playlist_id, playlist.songs)

    def get_playlists(self) -> List[PlayList]:
        response = requests.get(
            url=f"{self.APPLE_MUSIC_API_BASE}/me/library/playlists",
            headers=self._get_headers())

        if response.status_code == 201:
            print("Apple Music playlist created.")
        else:
            print("Failed to create Apple Music playlist:", response.text)

    def get_playlist(self, playlist: PlayList) -> PlayList:
        response = requests.get(
            url=f"{self.APPLE_MUSIC_API_BASE}/me/library/playlists",
            headers=self._get_headers())

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
    SCOPE = "playlist-read-private playlist-modify-private playlist-modify-public user-library-read user-follow-read"

    def __init__(self, client_id, client_secret, redirect_uri):
        super().__init__()
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.sp_handle: Spotify = None
        self.api_page_size = 50

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
        playlists = []
        result = self._get_spotify_handle().current_user_playlists(limit=self.api_page_size)
        while result and "items" in result:
            for item in result["items"]:
                playlists.append(self.local_view.resolve_playlist(
                    PlayList(id=item["id"], description=item["description"], name=item["name"], href=item["href"],
                             owner=item["owner"]["display_name"], public=item["public"])))
            if "next" in result:
                result = self._get_spotify_handle().next(result)
            else:
                break

        return playlists

    def get_playlist(self, playlist: PlayList) -> PlayList:
        result = self._get_spotify_handle().playlist_items(playlist_id=playlist.id, limit=self.api_page_size,
                                                           fields="items(track(id,name,href,album(id,name),artists(id,name)")
        while result and "items" in result:
            for item in result["items"]:
                if "track" in item:
                    try:
                        playlist.add_song(
                            self.local_view.resolve_song(Song(
                                id=item["track"]["id"],
                                artists=[self.local_view.resolve_artist(Artist(id=artist["id"], name=artist["name"]))
                                         for artist in item["track"]["artists"]],
                                name=item["track"]["name"], album=self.local_view.resolve_album(
                                    Album(id=item["track"]["album"]["id"], name=item["track"]["album"]["name"])),
                                href=item["track"]["href"])))
                    except Exception as ex:
                        ...
            if "next" in result:
                result = self._get_spotify_handle().next(result)
            else:
                break
        return playlist

    def get_followed_artists(self) -> List[Artist]:
        artists = []
        result = self._get_spotify_handle().current_user_followed_artists(limit=self.api_page_size)
        while result and "artists" in result and "items" in result["artists"]:
            for item in result["artists"]["items"]:
                artist = self.local_view.resolve_artist(Artist(id=item["id"], name=item["name"], href=item["href"]))
                artist.followed = True
                artists.append(artist)
            if "next" in result:
                result = self._get_spotify_handle().next(result)
            else:
                break
        return artists

    def get_liked_albums(self) -> List[Album]:
        albums = []
        result = self._get_spotify_handle().current_user_saved_albums(limit=self.api_page_size)
        while result and "items" in result:
            for item in result["items"]:
                album = self.local_view.resolve_album(
                    Album(id=item["album"]["id"], name=item["album"]["name"], href=item["album"]["href"],
                          artists=[self.local_view.resolve_artist(Artist(id=artist["id"], name=artist["name"], href=artist["href"])) for artist in item["album"]["artists"]]))
                album.liked = True
                albums.append(album)
            if "next" in result:
                result = self._get_spotify_handle().next(result)
            else:
                break
        return albums

    def search_song(self, name, artist):
        query = f"{name} {artist.name}"
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
    def __init__(self, source: MusicServiceApi, target: MusicServiceApi, dry_run):
        self.source: MusicServiceApi = source
        self.target: MusicServiceApi = target
        self.dry_run = dry_run

    @staticmethod
    def select_playlists(playlists: List[PlayList]):
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

    def synchronize_playlists(self):
        playlists = self.source.get_playlists()
        albums = self.source.get_liked_albums()
        artists = self.source.get_followed_artists()
        selected_playlists = Synchronizer.select_playlists(playlists)
        concurrent = False
        if concurrent:
            futures = []
            with ThreadPoolExecutor() as executor:
                for playlist in selected_playlists:
                    futures.append(executor.submit(self.synchronize_playlist, playlist))
                for future in concurrent.futures.as_completed(futures):
                    print(future.result())
        else:
            for playlist in selected_playlists:
                self.synchronize_playlist(playlist)

    def synchronize_playlist(self, playlist: PlayList):
        not_found = 0
        target_playlist = PlayList()
        target_playlist.name = playlist.name
        target_playlist.description = playlist.description
        self.source.get_playlist(playlist)
        for src_song in playlist.songs:
            target_song = self.target.search_song(src_song.name, src_song.artists[0])
            if not target_song:
                not_found += 1
            else:
                target_playlist.add_song(target_song)
        msg = f"could not find {not_found} songs" if not_found > 0 else "found ALL songs"
        logging.getLogger().info(f"synchronized playlist {playlist.name}, {msg}")
        if not self.dry_run:
            self.target.create_or_update_playlist(target_playlist)
