from metafy.app import remove_duplicates
from metafy.albums import Album


def test_remove_duplicates():
    albums = [
        Album(artist="Led Zeppelin", title="Led Zeppelin I", rating=100, img="", date="", source="Source 1"),
        Album(artist="Led Zeppelin", title="Led Zeppelin I", rating=100, img="", date="", source="Source 2"),
        Album(artist="Led Zeppelin", title="Led Zeppelin II", rating=100, img="", date="", source="Source 1"),
        Album(artist="Led Zeppelin", title="Led Zeppelin III", rating=100, img="", date="", source="Source 1"),
        Album(artist="Led Zeppelin", title="Led Zeppelin IV", rating=100, img="", date="", source="Source 1"),
    ]

    # the second copy of Led Zeppelin I should be removed
    filtered_albums = remove_duplicates(albums)
    albums.pop(1)
    assert albums == filtered_albums
