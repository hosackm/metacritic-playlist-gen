import json
import time
import os
import requests
import collections
from random import choice
from base64 import b64encode as b64e
from datetime import datetime as dt, timedelta as td
from typing import Optional, Type, Union, List, Dict, Callable
from urllib.parse import quote_plus as qp
from io import BytesIO

from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz
from boto3 import Session


version = "0.1.1"
URL = "https://www.metacritic.com/browse/albums/release-date/new-releases/date"
MONTH_DAY_YEAR_FMT = "%b %d %Y"


def acquire_user_agent():
    "Return a User Agent that metacritic won't expect a scraper to use"
    url = "https://www.whatismybrowser.com/guides/the-latest-user-agent/chrome"
    resp = requests.get(url)
    return choice([a.text
                   for a in BeautifulSoup(
                       resp.content, "html.parser").select("span.code")])


def get_html(retries: int=3) -> bytes:
    "Return the HTML content from metacritic's new releases page"
    rsp = requests.get(URL, headers={"User-Agent": f"{acquire_user_agent()}"})

    if rsp.status_code == 429:
        if retries > 0:
            t = int(rsp.headers.get("Retry-After", 5))
            print(f"Sleeping {t} seconds and retrying")
            time.sleep(t)
            get_html(retries=retries-1)
        raise Exception("Rate limitation exceeeded. Try again later.")
    elif rsp.status_code == 403:
        raise Exception("HTML resource forbidden. Try different User-Agent in request header.")
    elif rsp.status_code != 200:
        raise Exception("Unresolved HTTP error. Status code ({rsp.status_code})")

    return rsp.content


def deduce_and_replace_year(month_and_day: str) -> str:
    """
    Given a month and a day this function will deduce the year and place it into the
    date formatted string.  Albums that come from a different year must be handled
    properly.
    """
    now = dt.now()
    # can't create a datetime on a leap day without the correct year specified
    # good thing I developed this on a leap year...
    if month_and_day == "Feb 29":
        d = dt(month=2, day=29, year=now.year)
    else:
        d = dt.strptime(month_and_day, "%b %d").replace(year=now.year)

    # metacritic doesn't put old or futuristic albums on the front page.
    # I use 4 months as a threshold for "old/futuristic".
    month_diff = now.month - d.month
    if month_diff > 4:
        d = d.replace(year=now.year+1)
    elif month_diff < -4:
        d = d.replace(year=now.year-1)

    return dt.strftime(d, MONTH_DAY_YEAR_FMT)


def strip_select_as_type(soup,
                         selector: str,
                         as_type: Optional[Type]=None) -> Union[int, dt, str]:
    """
    Given a Soup object return the first instance of CSS selector,
    strip the text, and perform an optional type casting
    """
    text = soup.select(selector)[0].text
    text = text.replace("Release Date:", "").strip()

    if as_type == int:
        try:
            return int(text)
        except ValueError:
            return 0  # "tbd" is an acceptible value for score
    elif as_type == dt:
        return deduce_and_replace_year(text)
    return text


def gt_80_lt_1_week(album: Dict) -> bool:
    "Return True if the album was released in the past week"
    now = dt.now()
    weekago = now - td(days=7)
    date = dt.strptime(album["date"], MONTH_DAY_YEAR_FMT)

    # older than now, newer than a week ago, and gte to 80
    if date <= now and date >= weekago and album["score"] >= 80:
        return True
    return False


def parse(text: bytes) -> List[Dict]:
    "Parse out album information from the provided HTML string"
    soup = BeautifulSoup(text, "html.parser")
    return [
        {
            "date": strip_select_as_type(p, "li.release_date", dt),
            "score": strip_select_as_type(p, "div.metascore_w", int),
            "album": strip_select_as_type(p, "div.product_title > a"),
            "artist": strip_select_as_type(p, "li.product_artist > span.data")
        } for p in soup.select("div.product_wrap")
    ]


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

def lambda_handler(e, ctx):
    print("Scraping metacritic")

    html = get_html()
    albums = parse(html)
    albums = list(filter(gt_80_lt_1_week, albums))

    if not albums:
        print("No albums scraped")
        return

    print("Updating Spotify new releases playlist")
    api = Spotify(playlist_id="65RYrUbKJgX0eJHBIZ14Fe")

    print("Clearing playlist")
    api.clear_playlist()
    for album in albums:
        query = f"{album['album']} {album['artist']}"
        print(f"Searching for: {query}")
        hit = api.search_for_album(query)
        if hit:
            print(f"Found {query}. Adding to playlist")
            tracks = api.get_tracks_from_album(hit)
            api.add_tracks_to_playlist(tracks)

    description = f"""(Updated {dt.strftime(dt.today(), '%b %d %Y')}). \
This playlist was created using a script written by Matt Hosack.  The new \
release page from metacritic.com was scraped and albums realeased more \
recently than a week ago that scored higher than 80 were \
added to this playlist. \
See github.com/hosackm/metacritic-playlist-gen for more info."""
    api.update_playlist_description(description)

    return {"status": "completed successfully"}
