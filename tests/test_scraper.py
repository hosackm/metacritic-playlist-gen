from datetime import datetime
from typing import Generator
from freezegun import freeze_time
from metafy.scraper import Scraper
from metafy.albums import AlbumSource


def test_scraper_sources_can_be_registered():
    num_sources = 10
    sources = []
    for i in range(num_sources):
        a = AlbumSource()
        a.name = f"name {i}"
        sources.append(a)

    s = Scraper()
    assert len(s.sources) == 0

    for a in sources:
        s.register_source(a)

    assert len(s.sources) == num_sources

    for i, a in enumerate(s.sources):
        assert a.name == sources[i].name


@freeze_time(f"{datetime.now().year}-04-28")
def test_scraper_returns_a_generator(ScraperWithMetacriticSource):
    s = ScraperWithMetacriticSource
    assert len(s.sources) == 1
    assert isinstance(s.scrape(), Generator)
    assert len(list(s.scrape())) == 9
