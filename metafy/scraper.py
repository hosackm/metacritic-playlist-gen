from typing import Generator

from .albums import Album


class Scraper:
    def __init__(self):
        self.sources = []

    def register_source(self, source):
        self.sources.append(source)

    def scrape(self) -> Generator[Album, None, None]:
        for src in self.sources:
            for a in src.gen_albums():
                yield a
