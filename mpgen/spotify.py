import os
import json
import requests
import collections
from base64 import b64encode as b64enc
from urllib.parse import quote_plus as qp


class Auth:
    auth_url = "https://accounts.spotify.com/api/token"

    def __init__(self, client_id=None, client_secret=None,
                 auth_tk=None, ref_tk=None, redirect_uri=None):
        self.client_id = client_id or os.environ["MPGEN_CLIENT_ID"]
        self.client_secret = client_secret or os.environ["MPGEN_CLIENT_SECRET"]
        self.auth_tk = auth_tk or os.environ["MPGEN_AUTH_TK"]
        self.ref_tk = ref_tk or os.environ["MPGEN_REF_TK"]
        self.token = None

    def reauthorize(self):
        """
        Run through Spotify Authorization using the refresh token to acquire
        a new authorization token.  This function returns the json response.
        """
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.ref_tk,
        }
        headers = {
            "Authorization": "Basic {}".format(self._get_b64_encoded_string())
        }

        resp = requests.post(self.auth_url, data=data, headers=headers)

        # make sure request succeeded
        if resp.status_code != 200:
            raise Exception("Unable to refresh auth token{}".format(resp.text))

        # parse json response and store the token
        self.token = json.loads(resp.text).get("access_token")

    def get_token(self):
        if self.token is None:
            self.reauthorize()

        return self.token

    def _get_b64_encoded_string(self):
        """
        Returns a base64 encoded string of 'client_id:client_secret'.  This
        returns a string and not a bytes-like object because the Spotify API
        expects a string
        """
        id_sec = "{}:{}".format(self.client_id, self.client_secret)
        encoded = b64enc(bytes(id_sec, encoding="utf8"))
        return encoded.decode("utf8")


class Spotify:
    urlbase = "https://api.spotify.com/v1/"

    def __init__(self):
        self.auth = Auth()
        self.token = self.auth.get_token()

    def clear_playlist(self, playlist_id="65RYrUbKJgX0eJHBIZ14Fe"):
        tracks = self.get_tracks_from_playlist(playlist_id)
        self.delete_tracks_from_playlist(tracks)

    def get_tracks_from_playlist(self, playlist_id="65RYrUbKJgX0eJHBIZ14Fe"):
        """
        Returns a list of SpotifyTrack objects for the specified playlist
        """
        url = "{}users/hosackm/playlists/{}/tracks".format(
            self.urlbase, playlist_id)

        query = "?fields=items(track(name, id, artists(name)))"

        resp = requests.get(url+query, headers=self._get_header())

        if resp.status_code != 200:
            raise Exception(
                "Unable to get playlist tracks from Spotify API {}".format(
                    resp.text))

        items = json.loads(resp.text).get("items")

        return [SpotifyTrack.from_track_json(track.get("track"))
                for track
                in items]

    def add_tracks_to_playlist(self,
                               tracks,
                               playlist_id="65RYrUbKJgX0eJHBIZ14Fe"):
        """
        Adds the given SpotifyTracks to the playlist_id
        """
        if not isinstance(tracks, collections.Iterable):
            tracks = [tracks]

        data = {
            "uris": ["spotify:track:{}".format(track.track_id)
                     for track in tracks]
        }

        url = "{}users/hosackm/playlists/{}/tracks".format(self.urlbase,
                                                           playlist_id)

        resp = requests.post(url, headers=self._get_header(),
                             data=json.dumps(data))

        if resp.status_code != 201:
            raise Exception("Unable to add tracks to the playlist {}".format(
                resp.text))

    def delete_tracks_from_playlist(self,
                                    tracks,
                                    playlist_id="65RYrUbKJgX0eJHBIZ14Fe"):
        """
        Removes the given SpotifyTracks from the playlist_id
        """
        if not isinstance(tracks, collections.Iterable):
            tracks = [tracks]

        # Spotify doesn't allow more simultaneous deletes than 100
        data = {
            "tracks":
                [{"uri": "spotify:track:{}".format(track.track_id)}
                 for track in tracks]
        }

        url = "{}users/hosackm/playlists/{}/tracks".format(self.urlbase,
                                                           playlist_id)
        resp = requests.delete(url,
                               headers=self._get_header(),
                               data=json.dumps(data))
        if resp.status_code != 200:
            raise Exception("Unable to delete tracks")

    def search_for_album(self, album_query_string):
        """
        Search for an album by album title and return first result
        """
        q = "q=album:{}&type=album".format(qp(album_query_string))
        url = "https://api.spotify.com/v1/search?{}".format(q)

        resp = requests.get(url, headers=self._get_header())
        if resp.status_code != 200:
            raise Exception("Search request to API failed{}".format(resp.text))

        try:
            album_json = json.loads(resp.text)["albums"]["items"][0]
        except:
            return None

        return SpotifyAlbum.from_album_json(album_json)

    def get_tracks_from_album(self, album_id):
        """
        Return a SpotifyTrack for every track in album_id
        """
        url = "https://api.spotify.com/v1/albums/{}/tracks".format(album_id)

        resp = requests.get(url, headers=self._get_header())
        if resp.status_code != 200:
            raise Exception(
                "API Failed to retrieve tracks for album. {}".format(
                    resp.text))

        items = json.loads(resp.text).get("items")

        return [SpotifyTrack.from_track_json(track)
                for track
                in items]

    def _get_header(self):
        """
        Returns the authorization header expected by Spotify's API
        """
        return {"Authorization": "Bearer {}".format(self.token)}


class SpotifyAlbum:
    def __init__(self, artist, title, album_id):
        self.artist = artist
        self.title = title
        self.album_id = album_id

    def __repr__(self):
        return ("SpotifyAlbum(artist='{artist}', title='{title}'"
                ", id='{id}')").format(
                    artist=self.artist, title=self.title, id=self.album_id
                )

    @classmethod
    def from_album_json(cls, album):
        return cls(artist=album["artists"][0]["name"],
                   title=album["name"],
                   album_id=album["uri"].split(":")[-1])  # strip spotify:album


class SpotifyTrack:
    def __init__(self, artist, title, track_id):
        self.artist = artist
        self.title = title
        self.track_id = track_id

    def __repr__(self):
        return ("SpotifyTrack(artist='{artist}', title='{title}'"
                ", id='{id}')").format(
                    artist=self.artist, title=self.title, id=self.track_id
                )

    @classmethod
    def from_track_json(cls, track):
        """
        Convert a JSON 'track' object from the Spotify API into a SpotifyTrack
        """
        return cls(artist=track.get("artists")[0].get("name"),
                   track_id=track.get("id"),
                   title=track.get("name")
                   )
