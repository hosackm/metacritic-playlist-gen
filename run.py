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
        hit = api.search_for_album(album.title)
        if hit is not None:
            # get the tracks for the album
            print(album.artist, album.title)
            print(hit.album_id)
            tracks = api.get_tracks_from_album(hit.album_id)
            # add the tracks to the playlist
            api.add_tracks_to_playlist(tracks)

            print("Added {n} tracks from {album}".format(n=len(tracks),
                                                         album=album.title))

if __name__ == "__main__":
    run()
