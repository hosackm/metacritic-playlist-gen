import collections
import json
import os
from base64 import b64encode as b64e
from datetime import datetime as dt, timedelta as td
from typing import Optional, List, Dict
from urllib.parse import quote_plus as qp

import requests
from fuzzywuzzy import fuzz


class SpotifyAlbum:
    def __init__(self, artist: str, title: str, album_id: str):
        self.artist = artist
        self.title = title
        self.album_id = album_id

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return "SpotifyAlbum(artist='{artist}', title='{title}', id='{id}')".format(
                    artist=self.artist,
                    title=self.title,
                    id=self.album_id)

    @classmethod
    def from_album_json(cls, album: Dict):
        return cls(artist=album["artists"][0]["name"],
                   title=album["name"],
                   album_id=album["uri"].split(":")[-1])  # strip spotify:album

    def match(self, query: str):
        """
        Returns a percentage of confidence that an album matches a query string
        """
        artist_and_title = "{} {}".format(self.title, self.artist)
        return fuzz.token_set_ratio(query, artist_and_title)


class SpotifyTrack:
    def __init__(self, artist: str, title: str, track_id: str):
        self.artist = artist
        self.title = title
        self.track_id = track_id

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SpotifyTrack):
            raise NotImplementedError
        return self.__dict__ == other.__dict__

    def __repr__(self) -> str:
        return "SpotifyTrack(artist='{artist}', title='{title}', id='{id}')".format(
                    artist=self.artist,
                    title=self.title,
                    id=self.track_id)

    @classmethod
    def from_track_json(cls, track: Dict):
        """
        Convert a JSON track object from the Spotify API into a SpotifyTrack
        """
        return cls(artist=track.get("artists")[0].get("name"),
                   track_id=track.get("id"),
                   title=track.get("name"))

    def to_uri(self) -> str:
        return "spotify:track:{}".format(self.track_id)


class SpotifyAuth(requests.auth.AuthBase):
    auth_url = "https://accounts.spotify.com/api/token"

    def __init__(self, client_id, client_secret, ref_tk):
        self.client_id = client_id
        self.client_secret = client_secret
        self.ref_tk = ref_tk
        self.get_token()

    def get_token(self) -> None:
        "Go through authorization workflow and store the token"
        data = {"grant_type": "refresh_token", "refresh_token": self.ref_tk}
        id_secret = b64e(f"{self.client_id}:{self.client_secret}".encode("utf8"))
        headers = {"Authorization": f"Basic {id_secret.decode('utf8')}"}

        # perform HTTP request using the refresh token and auth header
        resp = requests.post(self.auth_url, data=data, headers=headers)
        if resp.status_code != 200:
            raise Exception(f"Unable to refresh auth token: {resp.json()}")

        # get expiration date and token from the response JSON
        j = resp.json()
        self.token = j["access_token"]
        self.expiration = dt.now() + td(int(j["expires_in"]))

    def __call__(self, req) -> requests.Request:
        if self.expiration - dt.now() < td(seconds=10):
            self.get_token()

        req.headers["Authorization"] = f"Bearer {self.token}"
        return req


class Spotify:
    urlbase = "https://api.spotify.com/v1/"

    def __init__(self,
                 playlist_id: str="65RYrUbKJgX0eJHBIZ14Fe"):
        self.auth = SpotifyAuth(
            os.environ["SPOTIFY_CLIENT_ID"],
            os.environ["SPOTIFY_CLIENT_SECRET"],
            os.environ["SPOTIFY_REF_TK"]
        )
        self.playlist_id = playlist_id

    def clear_playlist(self) -> List[SpotifyTrack]:
        """
        Removes all tracks from the playlist
        """
        tracks = self.get_tracks_from_playlist()
        self.delete_tracks_from_playlist(tracks)

        return tracks

    def get_tracks_from_playlist(self) -> List[SpotifyTrack]:
        """
        Returns a list of SpotifyTrack objects for the specified playlist
        """
        url = "{}playlists/{}/tracks".format(
            self.urlbase, self.playlist_id)
        query = "?fields=items(track(name, id, artists(name)))"

        resp = requests.get(url+query, auth=self.auth)
        if resp.status_code != 200:
            raise Exception("Unable to get playlist tracks from Spotify API: {}".format(resp.json()))

        items = resp.json().get("items")

        return [SpotifyTrack.from_track_json(track.get("track")) for track in items]

    def add_tracks_to_playlist(self, tracks: List[SpotifyTrack]):
        """
        Adds the given SpotifyTracks to the playlist_id
        """
        if not isinstance(tracks, collections.Iterable):
            tracks = [tracks]

        data = {"uris": [track.to_uri() for track in tracks]}
        url = "{}playlists/{}/tracks".format(self.urlbase,
                                             self.playlist_id)

        # POST http request to API and ensure it returns 201
        resp = requests.post(url, auth=self.auth, data=json.dumps(data))
        if resp.status_code != 201:
            raise Exception("Unable to add tracks to the playlist: {}".format(resp.json()))

    def delete_tracks_from_playlist(self, tracks: List[SpotifyTrack]):
        """
        Removes the given SpotifyTracks from the playlist_id
        """
        if not isinstance(tracks, collections.Iterable):
            tracks = [tracks]

        # convert uris into a json object
        data = {"tracks": [{"uri": track.to_uri()} for track in tracks]}
        url = "{}playlists/{}/tracks".format(self.urlbase,
                                             self.playlist_id)

        # DELETE http request to delete the tracks and ensure 200 was returned
        resp = requests.delete(url, auth=self.auth, data=json.dumps(data))
        if resp.status_code != 200:
            raise Exception("Unable to delete tracks")

    def update_playlist_description(self, description: str):
        """
        Update the text description diplayed on the page when viewing a
        playlist in Spotify's web player
        """
        url = "{}playlists/{}".format(self.urlbase, self.playlist_id)
        # header = self.auth.get_token_as_header()
        header = {"Content-Type": "application/json"}
        data = json.dumps({"description": description})

        # PUT http request to update description of playlist
        resp = requests.put(url, auth=self.auth, headers=header, data=data)
        if resp.status_code != 200:
            raise Exception("Unable to update playlist description: {}".format(resp.json()))

    def search_for_album(self, album_query_string: str) -> Optional[SpotifyAlbum]:
        """
        Search for an album by album title and return first result
        """
        q = "q=album:{}&type=album".format(qp(album_query_string))
        url = "{}search?{}".format(self.urlbase, q)

        resp = requests.get(url, auth=self.auth)
        if resp.status_code != 200:
            raise Exception("Search request to API failed{}".format(resp.json()))

        # create an album based on the json results
        albums = [SpotifyAlbum.from_album_json(album)
                  for album in resp.json()["albums"]["items"]]
        if albums:
            # return the highest ranked album
            return self._get_best_album(album_query_string, albums)

    def get_tracks_from_album(self, album: SpotifyAlbum) -> List[SpotifyTrack]:
        """
        Return a SpotifyTrack for every track in album
        """
        url = "{}albums/{}/tracks".format(self.urlbase, album.album_id)

        resp = requests.get(url, auth=self.auth)
        if resp.status_code != 200:
            raise Exception("API Failed to retrieve tracks for album: {}".format(resp.json()))

        items = resp.json().get("items")

        return [SpotifyTrack.from_track_json(track) for track in items]

    def _get_best_album(self, match_string: str, albums: SpotifyAlbum) -> Optional[SpotifyAlbum]:
        """
        Find a matching album given a list of search results from Spotify.

        The album should not be a single and should also fuzzy match the artist
        and title  within a certain threshold
        """
        # filter out single albums or albums that match with less than 90% confidence
        matches = [dict(album=a, match=a.match(match_string)) for a in albums
                   if len(self.get_tracks_from_album(a)) > 1 and
                   a.match(match_string) > 90]

        if matches:
            # return the highest matched album
            topresult = sorted(matches, key=lambda x: x["match"], reverse=True)[0]
            return topresult["album"]
        else:
            return None
