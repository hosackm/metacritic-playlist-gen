import pytest
import requests
from datetime import datetime
from freezegun import freeze_time
from unittest.mock import MagicMock
from typing import Generator

from metafy.metacritic import MetacriticSource, gt_80_lt_1_week, DetailedMetacriticSource


def test_albums_parse_correctly_from_html(ScrapedAlbums):
    assert len(ScrapedAlbums) == 200


def test_first_and_last_albums_have_correct_data(ScrapedAlbums):
    first, last = ScrapedAlbums[0], ScrapedAlbums[-1]

    assert first["artist"] == "Jeff Tweedy"
    assert first["title"] == "Together At Last"
    assert first["rating"] == 77

    firstd = datetime.strptime(first["date"], "%b %d %Y")
    assert firstd.day == 23 and firstd.month == 6

    assert last["artist"] == "Los Angeles Police Department"
    assert last["title"] == "Los Angeles Police Department"  # self-titled
    assert last["rating"] == 80

    lastd = datetime.strptime(last["date"], "%b %d %Y")
    assert lastd.day == 28 and lastd.month == 4


def test_tbd_rating_correctly_returns_0(MakeAlbum):
    html = MakeAlbum(1, "Fake Title", "Jun 4", "Fake Album")
    m = MetacriticSource()
    album = m.parse(html)

    assert album[0]["rating"] == 1

    html = MakeAlbum("tbd", "Fake Title", "Jun 4", "Fake Album")
    album = m.parse(html)

    assert album[0]["rating"] == 0


def test_request_failure_raises_exception(MetacriticFailingMock):
    with pytest.raises(Exception) as exc:
        assert str(exc.value) == "Couldn't get metacritic HTML"


@freeze_time("2000-07-04")
def test_filtering_function():
    good = [
        {"date": "Jun 27 2000", "rating": 85},
        {"date": "Jun 28 2000", "rating": 85},
        {"date": "Jun 29 2000", "rating": 85},
        {"date": "Jun 30 2000", "rating": 85},
        {"date": "Jul 1 2000", "rating": 80},
        {"date": "Jul 2 2000", "rating": 81},
        {"date": "Jul 3 2000", "rating": 82},
        {"date": "Jul 4 2000", "rating": 83},
    ]
    bad = [
        {"date": "Jul 4 2000", "rating": 79},
        {"date": "Jun 26 2000", "rating": 80},
        {"date": "Jul 5 2000", "rating": 80},
    ]

    for t in good:
        assert gt_80_lt_1_week(t)

    for t in bad:
        assert not gt_80_lt_1_week(t)


@freeze_time(f"{datetime.now().year}-04-28")
def test_parse_yields_albums_from_generator(MetacriticRequestMock):
    m = MetacriticSource()
    p = m.gen_albums()

    # there are 9 albums in the test HTML that pass the >80 and less than a week old filter
    num_albums = 9

    assert len(list(p)) == num_albums


@freeze_time(f"2020-04-03")
def test_metacritic_detailed_source_yeilds_8_albums(MetacriticRequestMock):
    m = DetailedMetacriticSource()
    p = m.gen_albums()

    num_albums = 15
    assert len(list(p)) == num_albums
