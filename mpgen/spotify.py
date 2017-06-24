import os
import json
import requests
import collections
from fuzzywuzzy import fuzz
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

    def __init__(self,
                 user_id="hosackm",
                 playlist_id="65RYrUbKJgX0eJHBIZ14Fe"):
        self.auth = Auth()
        self.token = self.auth.get_token()
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
        url = "{}users/hosackm/playlists/{}/tracks".format(
            self.urlbase, self.playlist_id)

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

    def add_tracks_to_playlist(self, tracks):
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
                                                           self.playlist_id)

        resp = requests.post(url, headers=self._get_header(),
                             data=json.dumps(data))

        if resp.status_code != 201:
            raise Exception("Unable to add tracks to the playlist {}".format(
                resp.text))

    def delete_tracks_from_playlist(self, tracks):
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
                                                           self.playlist_id)
        resp = requests.delete(url,
                               headers=self._get_header(),
                               data=json.dumps(data))
        if resp.status_code != 200:
            raise Exception("Unable to delete tracks")

    def update_playlist_description(self, description):
        """
        Update the text description diplayed on the page when viewing a
        playlist in Spotify's web player
        """
        url = ("https://api.spotify.com/v1/users/"
               "{}/playlists/{}".format("hosackm", self.playlist_id))
        header = self._get_header()
        header["Content-Type"] = "application/json"
        data = json.dumps({"description": description})

        resp = requests.put(url, headers=header, data=data)
        if resp.status_code != 200:
            raise Exception("Unable to update playlist description."
                            " {}".format(resp.text))

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
            albums_json = json.loads(resp.text)["albums"]["items"]
        except:
            return None

        # ToDo: fuzzy find the correct album that is not a singles album
        album_match = self._fuzzy_find_album(album_query_string, albums_json)

        if album_match:
            return SpotifyAlbum.from_album_json(album_match)

        return None

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

    def _fuzzy_find_album(self, match_string, albums):
        """
        Find a matching album given a list of search results from Spotify.

        The album should not be a single and should also fuzzy match the artist
        and title  within a certain threshold
        """
        # filter out single albums
        non_singles = []
        for album in albums:
            album_id = album["uri"].split(":")[-1]
            if len(self.get_tracks_from_album(album_id)) > 1:
                non_singles.append(album)

        # zip album json and the matching string from the spotify search result
        json_and_album_title_pairs = [
            (a, a["name"] + " " + a["artists"][0]["name"])
            for a in non_singles]

        # do fuzzy string matching on artist and album title
        best_match = (None, 0)
        for album, album_and_title in json_and_album_title_pairs:
            ratio = fuzz.token_set_ratio(match_string, album_and_title)
            if ratio > best_match[1]:
                best_match = (album, ratio)

        # if match ratio is above 90% confidence return the album
        if best_match[1] > 90:
            return best_match[0]
        # otherwise we couldn't find a good match for the album
        return None


class SpotifyAlbum:
    def __init__(self, artist, title, album_id):
        self.artist = artist
        self.title = title
        self.album_id = album_id

    def __repr__(self):
        return ("SpotifyAlbum(artist='{artist}', title='{title}'"
                ", id='{id}')").format(
                    artist=self.artist, title=self.title, id=self.album_id)

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
                    artist=self.artist, title=self.title, id=self.track_id)

    @classmethod
    def from_track_json(cls, track):
        """
        Convert a JSON 'track' object from the Spotify API into a SpotifyTrack
        """
        return cls(artist=track.get("artists")[0].get("name"),
                   track_id=track.get("id"),
                   title=track.get("name")
                   )
