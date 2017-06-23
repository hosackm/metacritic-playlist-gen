from datetime import datetime, timedelta
from mpgen.spotify import Spotify
from mpgen.metacritic import Scraper


def run():
    today = datetime.today()
    week_ago = today - timedelta(days=7)

    # get recent albums that have a rating higher than 80
    recent_albums = [a
                     for a in Scraper().scrape_html()
                     if week_ago <= a.date <= today and a.rating >= 80]

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
release page from metacritic.com was scraped and albums scoring higher than \
80 were added to this playlist.

See github.com/hosackm/metacritic-playlist-gen for more info.

Last Updated {}\
""".format(datetime.strftime(datetime.today(), "%b %d %Y"))

    # update playlist description to tell that things worked
    api.update_playlist_description(description)

if __name__ == "__main__":
    run()
