import re
import os
import json
import datetime
import pytest
import requests_mock
from unittest import mock
from bs4 import BeautifulSoup as Soup

from metafy.metacritic import parse, URL
from metafy.spotify import Auth, Spotify


RESOURCES = os.path.join(os.path.dirname(__file__), "resources")


# Spotify fixtures

@pytest.fixture
def AuthEnv():
    os.environ["SPOTIFY_CLIENT_ID"] = "TEST_CLIENT_ID"
    os.environ["SPOTIFY_CLIENT_SECRET"] = "TEST_CLIENT_SECRET"
    os.environ["SPOTIFY_REF_TK"] = "TEST_REF_TK"
    return Auth()


@pytest.fixture
def RequestsMockedSpotifyAPI():
    with requests_mock.Mocker() as rm:
        rm.register_uri("GET",
                        re.compile("https://api.spotify.com/v1/playlists/.*"),
                        json=json.load(open(os.path.join(RESOURCES, "tracks.json"))))
        rm.register_uri("GET",
                        re.compile("https://api.spotify.com/v1/albums.*"),
                        json=json.load(open(os.path.join(RESOURCES, "albums.json"))))
        rm.register_uri("GET",
                        re.compile("https://api.spotify.com/v1/search.*"),
                        json=json.load(open(os.path.join(RESOURCES, "search.json"))))
        yield rm


@pytest.fixture
def FakeAuth(AuthEnv):
    auth = Auth()
    with mock.patch("metafy.spotify.Auth.get_token_as_header") as authmock:
        yield auth


@pytest.fixture
def MockedSpotifyAPI(FakeAuth, RequestsMockedSpotifyAPI):
    s = Spotify()
    s.auth = FakeAuth
    yield s


# Metacritic Fixtures

@pytest.fixture
def MakeAlbum():
    def make(score, title, datestr, album):
        # must be two items so that it contains a list of results after parsing
        return f"""
          <div class="product_wrap">
            <div class="metascore_w">{score}</div>
            <div class="product_title"><a>{title}</a></div>
            <li class="release_date"><span class="data">{datestr}</span></li>
            <li class="product_artist"><span class="data">{album}</span></li>
          </div>
          <div class="product_wrap">
            <div class="metascore_w">{score}</div>
            <div class="product_title"><a>{title}</a></div>
            <li class="release_date"><span class="data">{datestr}</span></li>
            <li class="product_artist"><span class="data">{album}</span></li>
          </div>
        """
    return make


@pytest.fixture
def ScrapedAlbums():
    with open(os.path.join(RESOURCES, "metacritic_sample.html")) as f:
        yield parse(f.read())


@pytest.fixture
def MetacriticFailingMock():
    with requests_mock.Mocker() as m:
        m.register_uri("GET", URL, text="failed to retrieve HTML", status_code=400)


@pytest.fixture
def MetacriticRateLimitMock():
    with requests_mock.Mocker() as m:
        m.register_uri("GET", URL, text="rate limited", status_code=429, headers={"Retry-After": "5"})
