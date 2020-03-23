import re
import os
import json
import pytest
import requests_mock
from unittest import mock
from bs4 import BeautifulSoup as Soup

from metafy.metacritic import MetacriticSpider
from metafy.spotify import Auth, Spotify

from scrapy.http import TextResponse


RESOURCES = os.path.join(os.path.dirname(__file__), "resources")


@pytest.fixture
def AuthEnv():
    os.environ["SPOTIFY_CLIENT_ID"] = "TEST_CLIENT_ID"
    os.environ["SPOTIFY_CLIENT_SECRET"] = "TEST_CLIENT_SECRET"
    os.environ["SPOTIFY_REF_TK"] = "TEST_REF_TK"
    return Auth()


@pytest.fixture
def scraper():
    s = MetacriticSpider

    with requests_mock.Mocker() as reqmock:
        f = open(os.path.join(RESOURCES, "metacritic_sample.html"))

        reqmock.get(s.start_urls[0], text=f.read())

        yield s

        f.close()


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
def albums(scraper):
    return scraper.scrape_html()


@pytest.fixture
def MakeAlbum():
    def make(score, title, datestr, album):
        html = """
        <li>
            <div class="product_score">{0}</div>
            <div class="product_title">{1}</div>
            <li class="release_date"><span class="data">{2}</span></li>
            <li class="product_artist"><span class="data">{3}</span></li>
        </li>
        """.format(score, title, datestr, album)
        s = Soup(html, "html.parser")
        return Album.from_list_item(s)
    return make


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


@pytest.fixture
def ScrapyMetacriticResponse():
    return TextResponse(
        body=open(os.path.join(RESOURCES, "metacritic_sample.html")).read(),
        encoding="utf8",
        url=MetacriticSpider.start_urls[0]
    )


@pytest.fixture
def ScrapedAlbums(ScrapyMetacriticResponse):
    resp = ScrapyMetacriticResponse
    spider = MetacriticSpider()
    return list(spider.parse(resp))
