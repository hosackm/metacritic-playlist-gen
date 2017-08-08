import os
import json
import requests
import collections
from datetime import datetime, timedelta
from fuzzywuzzy import fuzz
from base64 import b64encode
from urllib.parse import quote_plus as qp


class Auth:
    auth_url = "https://accounts.spotify.com/api/token"

    def __init__(self,
                 client_id=None,
                 client_secret=None,
                 ref_tk=None):
        self.client_id = client_id or os.environ["MPGEN_CLIENT_ID"]
        self.client_secret = client_secret or os.environ["MPGEN_CLIENT_SECRET"]
        self.ref_tk = ref_tk or os.environ["MPGEN_REF_TK"]
        self.token = None
        self.token_expires = None

    def reauthorize(self):
        """
        Run through Spotify Authorization using the refresh token to acquire
        a new authorization token.  This function returns the json response.
        """
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.ref_tk,
        }

        # base64 encode client_id:client_secret for authorization POST
        id_secret = "{}:{}".format(self.client_id, self.client_secret)
        base64_id_secret = b64encode(id_secret.encode("utf8")).decode("utf8")
        headers = {
            "Authorization": "Basic {}".format(base64_id_secret)
        }

        # POST request and check that it was successful
        resp = requests.post(self.auth_url, data=data, headers=headers)
        if resp.status_code != 200:
            raise Exception("Unable to refresh auth token: {}".format(resp.json()))

        # parse json response and store the token and expiration date
        payload = resp.json()
        self.token = payload.get("access_token")
        self.token_expires = datetime.now() + timedelta(seconds=int(payload.get("expires_in")))

    def token_expired(self):
        """
        Returns True if a token has expired or will expire in less than 10 seconds (just to be safe)
        """
        timeleft = self.token_expires - datetime.now()
        return True if timeleft < timedelta(seconds=10) else False

    def get_token(self):
        """
        Try to get cached token or reauthorize
        """
        if self.token is None or self.token_expired():
            self.reauthorize()

        return self.token

    def get_token_as_header(self):
        """
        Return authorization token as a request header
        """
        token = self.get_token()
        return {"Authorization": "Bearer {}".format(token)}


class Spotify:
    urlbase = "https://api.spotify.com/v1/"

    def __init__(self,
                 user_id="hosackm",
                 playlist_id="65RYrUbKJgX0eJHBIZ14Fe"):
        self.auth = Auth()
        self.user_id = user_id
        self.playlist_id = playlist_id

    def clear_playlist(self):
        """
        Removes all tracks from the playlist
        """
        tracks = self.get_tracks_from_playlist()
        self.delete_tracks_from_playlist(tracks)

        return tracks

    def get_tracks_from_playlist(self):
        """
        Returns a list of SpotifyTrack objects for the specified playlist
        """
        url = "{}users/{}/playlists/{}/tracks".format(
            self.urlbase, self.user_id, self.playlist_id)

        query = "?fields=items(track(name, id, artists(name)))"

        resp = requests.get(url+query, headers=self.auth.get_token_as_header())

        if resp.status_code != 200:
            raise Exception("Unable to get playlist tracks from Spotify API: {}".format(resp.json()))

        items = resp.json().get("items")

        return [SpotifyTrack.from_track_json(track.get("track")) for track in items]

    def add_tracks_to_playlist(self, tracks):
        """
        Adds the given SpotifyTracks to the playlist_id
        """
        if not isinstance(tracks, collections.Iterable):
            tracks = [tracks]

        data = {"uris": [track.to_uri() for track in tracks]}
        url = "{}users/{}}/playlists/{}/tracks".format(self.urlbase,
                                                       self.user_id,
                                                       self.playlist_id)

        # POST http request to API and ensure it returns 201
        resp = requests.post(url, headers=self.auth.get_token_as_header(), data=json.dumps(data))
        if resp.status_code != 201:
            raise Exception("Unable to add tracks to the playlist: {}".format(resp.json()))

    def delete_tracks_from_playlist(self, tracks):
        """
        Removes the given SpotifyTracks from the playlist_id
        """
        if not isinstance(tracks, collections.Iterable):
            tracks = [tracks]

        # convert uris into a json object
        data = {"tracks": [{"uri": track.to_uri()} for track in tracks]}
        url = "{}users/{}/playlists/{}/tracks".format(self.urlbase,
                                                      self.user_id,
                                                      self.playlist_id)

        # DELETE http request to delete the tracks and ensure 200 was returned
        resp = requests.delete(url,
                               headers=self.auth.get_token_as_header(),
                               data=json.dumps(data))
        if resp.status_code != 200:
            raise Exception("Unable to delete tracks")

    def update_playlist_description(self, description):
        """
        Update the text description diplayed on the page when viewing a
        playlist in Spotify's web player
        """
        url = "{}users{}/playlists/{}".format(self.urlbase, self.user_id, self.playlist_id)
        header = self.auth.get_token_as_header()
        header["Content-Type"] = "application/json"
        data = json.dumps({"description": description})

        # PUT http request to update description of playlist
        resp = requests.put(url, headers=header, data=data)
        if resp.status_code != 200:
            raise Exception("Unable to update playlist description: {}".format(resp.json()))

    def search_for_album(self, album_query_string):
        """
        Search for an album by album title and return first result
        """
        q = "q=album:{}&type=album".format(qp(album_query_string))
        url = "{}search?{}".format(self.urlbase, q)

        resp = requests.get(url, headers=self.auth.get_token_as_header())
        if resp.status_code != 200:
            raise Exception("Search request to API failed{}".format(resp.json()))

        albums = [SpotifyAlbum.from_album_json(album)
                  for album in resp.json()["albums"]["items"]]

        return self._get_best_album(album_query_string, albums)

    def get_tracks_from_album(self, album):
        """
        Return a SpotifyTrack for every track in album
        """
        url = "https://api.spotify.com/v1/albums/{}/tracks".format(album.album_id)

        resp = requests.get(url, headers=self.auth.get_token_as_header())
        if resp.status_code != 200:
            raise Exception("API Failed to retrieve tracks for album: {}".format(resp.json()))

        items = resp.json().get("items")

        return [SpotifyTrack.from_track_json(track) for track in items]

    def _get_best_album(self, match_string, albums):
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


class SpotifyAlbum:
    def __init__(self, artist, title, album_id):
        self.artist = artist
        self.title = title
        self.album_id = album_id

    def __repr__(self):
        return "SpotifyAlbum(artist='{artist}', title='{title}', id='{id}')".format(
                    artist=self.artist,
                    title=self.title,
                    id=self.album_id)

    @classmethod
    def from_album_json(cls, album):
        return cls(artist=album["artists"][0]["name"],
                   title=album["name"],
                   album_id=album["uri"].split(":")[-1])  # strip spotify:album

    def match(self, query):
        """
        Returns a percentage of confidence that an album matches a query string
        """
        artist_and_title = "{} {}".format(self.title, self.artist)
        return fuzz.token_set_ratio(query, artist_and_title)


class SpotifyTrack:
    def __init__(self, artist, title, track_id):
        self.artist = artist
        self.title = title
        self.track_id = track_id

    def __repr__(self):
        return "SpotifyTrack(artist='{artist}', title='{title}', id='{id}')".format(
                    artist=self.artist,
                    title=self.title,
                    id=self.track_id)

    @classmethod
    def from_track_json(cls, track):
        """
        Convert a JSON track object from the Spotify API into a SpotifyTrack
        """
        return cls(artist=track.get("artists")[0].get("name"),
                   track_id=track.get("id"),
                   title=track.get("name"))

    def to_uri(self):
        return "spotify:track:{}".format(self.track_id)
