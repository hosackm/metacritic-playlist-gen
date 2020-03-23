from datetime import datetime


def test_albums_parse_correctly_from_html(ScrapedAlbums):
    assert len(ScrapedAlbums) == 200


def test_first_and_last_albums_have_correct_data(ScrapedAlbums):
    datefmt = "%b %d %Y"
    first, last = ScrapedAlbums[0], ScrapedAlbums[-1]
    firstd = datetime.strptime(first["date"], datefmt)
    lastd = datetime.strptime(last["date"], datefmt)

    assert first["artist"] == "Jeff Tweedy"
    assert first["album"] == "Together At Last"
    assert first["score"] == 77
    assert firstd.day == 23 and firstd.month == 6

    assert last["artist"] == "Los Angeles Police Department"
    assert last["album"] == "Los Angeles Police Department"  # self-titled
    assert last["score"] == 80
    assert lastd.day == 28 and lastd.month == 4
