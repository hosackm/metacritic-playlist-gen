import pytest
from datetime import datetime
from freezegun import freeze_time
from unittest.mock import MagicMock

from metafy.metacritic import MetacriticSource, gt_80_lt_1_week


def test_albums_parse_correctly_from_html(ScrapedAlbums):
    assert len(ScrapedAlbums) == 200


def test_first_and_last_albums_have_correct_data(ScrapedAlbums):
    first, last = ScrapedAlbums[0], ScrapedAlbums[-1]

    assert first["artist"] == "Jeff Tweedy"
    assert first["album"] == "Together At Last"
    assert first["score"] == 77

    firstd = datetime.strptime(first["date"], "%b %d %Y")
    assert firstd.day == 23 and firstd.month == 6

    assert last["artist"] == "Los Angeles Police Department"
    assert last["album"] == "Los Angeles Police Department"  # self-titled
    assert last["score"] == 80

    lastd = datetime.strptime(last["date"], "%b %d %Y")
    assert lastd.day == 28 and lastd.month == 4


def test_tbd_score_correctly_returns_0(MakeAlbum):
    html = MakeAlbum(1, "Fake Title", "Jun 4", "Fake Album")
    m = MetacriticSource()
    album = m.parse(html)

    assert album[0]["score"] == 1

    html = MakeAlbum("tbd", "Fake Title", "Jun 4", "Fake Album")
    album = m.parse(html)

    assert album[0]["score"] == 0


def test_request_failure_raises_exception(MetacriticFailingMock):
    with pytest.raises(Exception) as exc:
        assert str(exc.value) == "Couldn't get metacritic HTML"


@freeze_time("2000-07-04")
def test_filtering_function():
    good = [
        {"date": "Jun 27 2000", "score": 85},
        {"date": "Jun 28 2000", "score": 85},
        {"date": "Jun 29 2000", "score": 85},
        {"date": "Jun 30 2000", "score": 85},
        {"date": "Jul 1 2000", "score": 80},
        {"date": "Jul 2 2000", "score": 81},
        {"date": "Jul 3 2000", "score": 82},
        {"date": "Jul 4 2000", "score": 83},
    ]
    bad = [
        {"date": "Jul 4 2000", "score": 79},
        {"date": "Jun 26 2000", "score": 80},
        {"date": "Jul 5 2000", "score": 80},
    ]

    for t in good:
        assert gt_80_lt_1_week(t)

    for t in bad:
        assert not gt_80_lt_1_week(t)
