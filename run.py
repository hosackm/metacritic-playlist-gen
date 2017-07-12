import argparse
import textwrap
import logging
import sys
from datetime import datetime, timedelta
from mpgen.spotify import Spotify
from mpgen.metacritic import Scraper


__version__ = "0.0.1"

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s "
                              "- %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)


def run(minimum_rating=80,
        cutoff_date=7,
        user_id="hosackm",
        playlist_id="65RYrUbKJgX0eJHBIZ14Fe"):
    logger.info("Searching for albums less than {0} days old that scored "
                "{1} or higher on Metacritic".format(
                    cutoff_date, minimum_rating))

    today = datetime.today()
    week_ago = today - timedelta(days=cutoff_date)

    # get recent albums that have a rating higher than 80
    recent_albums = [a
                     for a in Scraper().scrape_html()
                     if week_ago <= a.date <= today
                     and a.rating >= minimum_rating]

    # create Spotify API instance
    api = Spotify(user_id=user_id, playlist_id=playlist_id)

    # clear playlist
    removed = api.clear_playlist()
    for t in removed:
        try:
            logger.info("Removed {title} by {artist}".format(
                title=t.title,
                artist=t.artist))
        except UnicodeEncodeError:  # some Spotify unicode characters don't
                                    # play nice with stdout
            logger.info("Removed a track by {artist}".format(artist=t.artist))

    # search for each album and add it's tracks to playlist
    for album in recent_albums:
        try:
            hit = api.search_for_album(" ".join((album.title, album.artist)))
            if hit is not None:
                # get the tracks for the album
                tracks = api.get_tracks_from_album(hit.album_id)
                # add the tracks to the playlist
                api.add_tracks_to_playlist(tracks)
                # notify added tracks
                logger.info("Added {n} tracks from {album} by {artist}".format
                            (n=len(tracks),
                             album=album.title,
                             artist=album.artist))
        except Exception as e:
            logger.error(e)
            sys.exit()

    description = """\
This playlist was created using a script written by Matt Hosack.  The new \
release page from metacritic.com was scraped and albums realeased more
recently than {0} days ago that scored higher than {1} were \
added to this playlist.

See github.com/hosackm/metacritic-playlist-gen for more info.

Last Updated {2}\
""".format(cutoff_date,
           minimum_rating,
           datetime.strftime(datetime.today(), "%b %d %Y"))

    # update playlist description to tell that things worked
    try:
        logger.info("Updating description to: {}".format(description))
        api.update_playlist_description(description)
    except Exception as e:
        logger.error(e)


if __name__ == "__main__":
    desc = """\
        This script will scrape Metacritic's New Releases page and parse the \
        album information.  It will then take the albums that have a minimum \
        rating and were released after a cutoff date and add them to a \
        Spotify playlist.\
        """
    parser = argparse.ArgumentParser(description=textwrap.dedent(desc))
    parser.add_argument("-d", "--days-ago", default=7, metavar="DAYS",
                        help="Only albums newer than this many days ago "
                             "will be added to the playlist")
    parser.add_argument("-r", "--rating", default=80,
                        metavar="RATING",
                        help="Only albums with a higher rating than this "
                             "number will be added to the playlist")
    parser.add_argument("-u", "--user", metavar="USERNAME",
                        help="Username of the Spotify user that owns "
                             "the playlist")
    parser.add_argument("-p", "--playlist", metavar="PLAYLIST-ID",
                        help="Spotify playlist id to add songs to")

    args = parser.parse_args()
    dargs = dict(cutoff_date=args.days_ago, minimum_rating=args.rating)
    if args.user is not None:
        dargs.update({"user_id": args.user})
    if args.user is not None:
        dargs.update({"playlist_id": args.playlist})

    run(**dargs)
