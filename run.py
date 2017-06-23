import argparse
import textwrap
from datetime import datetime, timedelta
from mpgen.spotify import Spotify
from mpgen.metacritic import Scraper


def run(minimum_rating=80, cutoff_date=7):
    print(ascii_art_short)
    print()
    print("Searching for albums less than {0} days old that scored "
          "{1} or higher on Metacritic".format(cutoff_date, minimum_rating))

    today = datetime.today()
    week_ago = today - timedelta(days=cutoff_date)

    # get recent albums that have a rating higher than 80
    recent_albums = [a
                     for a in Scraper().scrape_html()
                     if week_ago <= a.date <= today
                     and a.rating >= minimum_rating]

    # create Spotify API instance
    api = Spotify()

    # clear playlist
    api.clear_playlist()

    # search for each album and add it's tracks to playlist
    for album in recent_albums:
        hit = api.search_for_album(" ".join((album.title, album.artist)))
        if hit is not None:
            # get the tracks for the album
            tracks = api.get_tracks_from_album(hit.album_id)
            # add the tracks to the playlist
            api.add_tracks_to_playlist(tracks)
            # notify added tracks
            print("Added {n} tracks from {album} by {artist}".format
                  (n=len(tracks),
                   album=album.title,
                   artist=album.artist))

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
    api.update_playlist_description(description)

version = "0.0.1"
ascii_art_short = """\
   _____ __________  ________
  /     \\\\______   \/  _____/  ____   ____
 /  \ /  \|     ___/   \  ____/ __ \ /    \\
/    Y    \    |   \    \_\  \  ___/|   |  \\
\____|__  /____|    \______  /\___  >___|  /
        \/                 \/     \/     \/
version {version}\
""".format(version=version)

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

    args = parser.parse_args()
    run(args.rating, args.days_ago)
