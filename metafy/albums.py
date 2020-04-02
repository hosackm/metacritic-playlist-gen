from dataclasses import dataclass


class AlbumSource:
    def __init__(self):
        self.name = "no source name provided"

    def gen_albums(self):
        raise NotImplementedError


@dataclass
class Album:
    title: str
    artist: str
    source: AlbumSource
    img: str
    rating: int
    date: str
