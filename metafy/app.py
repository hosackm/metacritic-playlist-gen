import os
import logging
from datetime import datetime as dt
from collections import defaultdict
from .scraper import Scraper
from .metacritic import MetacriticSource
from .spotify import Spotify
from .pitchfork import PitchforkSource


version = "0.1.1"
logger = logging.getLogger("metafy")
logger.setLevel(logging.DEBUG)
logging.StreamHandler().setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))


def remove_duplicates(albums):
    table = dict()
    for album in albums:
        logger.info(f"album: {album}")
        key = f"{album.title}:{album.artist}"
        if key in table:
            logging.debug(f"Removing duplicate album {album}")
            continue
        table[key] = album

    return [v for _, v in table.items()]


def lambda_handler(e, ctx):
    logger.info("Scraping metacritic")
    env = os.environ

    if env["ENVIRONMENT_TYPE"] == "prod":
        api = Spotify(env["SpotifyPlaylistID"])
    else:
        class MockSpotify:
            def clear_playlist(self): pass

            def search_for_album(self, query): return None

            def get_tracks_from_album(self, hit): pass

            def add_tracks_to_playlist(self, tracks): pass

            def update_playlist_description(self, descr): pass
        api = MockSpotify()

    scraper = Scraper()
    scraper.register_source(MetacriticSource())
    scraper.register_source(PitchforkSource())

    logger.info("Clearing playlist")
    api.clear_playlist()

    albums = remove_duplicates(list(scraper.scrape()))
    for album in albums:
        logger.info(f"Processing: {album}")
        query = f"{album.title} {album.artist}"
        logger.debug(f"Searching for ({album.source}): {query}")
        hit = api.search_for_album(query)
        if hit:
            logger.debug(f"Found {query}. Adding to playlist")
            tracks = api.get_tracks_from_album(hit)
            api.add_tracks_to_playlist(tracks)

    description = f"""(Updated {dt.strftime(dt.today(), '%b %d %Y')}). \
This playlist was created using a script written by Matt Hosack.  The new \
release page from metacritic.com was scraped and albums realeased more \
recently than a week ago that scored higher than 80 were \
added to this playlist. \
See github.com/hosackm/metacritic-playlist-gen for more info."""
    api.update_playlist_description(description)

    return {"status": "completed successfully"}
