import re
import os
import json
import pytest
import requests_mock
from unittest import mock

from metafy.metacritic import MetacriticSource, DetailedMetacriticSource
from metafy.pitchfork import PitchforkSource
from metafy.scraper import Scraper
from metafy.spotify import SpotifyAuth, Spotify


RESOURCES = os.path.join(os.path.dirname(__file__), "resources")


# Spotify fixtures
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
        j = {"access_token": "YOURTOKEN", "expires_in": 3600}
        rm.register_uri("POST", "https://accounts.spotify.com/api/token", json=j)
        yield rm


@pytest.fixture
def AuthEnv(RequestsMockedSpotifyAPI):
    os.environ["SPOTIFY_CLIENT_ID"] = "client_id"
    os.environ["SPOTIFY_CLIENT_SECRET"] = "client_secret"
    os.environ["SPOTIFY_REF_TK"] = "ref_token"
    return SpotifyAuth(os.environ["SPOTIFY_CLIENT_ID"],
                       os.environ["SPOTIFY_CLIENT_SECRET"],
                       os.environ["SPOTIFY_REF_TK"])


@pytest.fixture
def MockedSpotifyAPI(AuthEnv, RequestsMockedSpotifyAPI):
    s = Spotify()
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
        m = MetacriticSource()
        yield m.parse(f.read())


@pytest.fixture
def MetacriticFailingMock():
    with requests_mock.Mocker() as m:
        m.register_uri("GET", MetacriticSource.URL, text="failed to retrieve HTML", status_code=400)


@pytest.fixture
def MetacriticRateLimitMock():
    with requests_mock.Mocker() as m:
        m.register_uri("GET", MetacriticSource.URL, text="rate limited", status_code=429, headers={"Retry-After": "5"})


@pytest.fixture
def MetacriticRequestMock():
    with requests_mock.Mocker() as rm:
        with open(os.path.join(RESOURCES, "metacritic_sample.html")) as f:
            rm.register_uri("GET", MetacriticSource.URL, text=f.read())
        with open(os.path.join(RESOURCES, "metacritic_sample_detailed.html")) as f:
            rm.register_uri("GET", DetailedMetacriticSource.URL, text=f.read())
        rm.register_uri("GET",
                        "https://www.whatismybrowser.com/guides/the-latest-user-agent/chrome",
                        text="<span class='code'>some-agent</span>")
        yield rm


@pytest.fixture
def ScraperWithMetacriticSource(MetacriticRequestMock):
    s = Scraper()
    s.register_source(MetacriticSource())
    return s


@pytest.fixture
def ScraperWithMetacriticDetailedSource(MetacriticRequestMock):
    s = Scraper()
    s.register_source(DetailedMetacriticSource())
    return s


@pytest.fixture
def PitchforkReq():
    with requests_mock.Mocker() as rm:
        with open(os.path.join(RESOURCES, "pitchfork.html")) as f:
            rm.register_uri("GET", PitchforkSource.URL, text=f.read())
        yield rm
