import os
from datetime import datetime as dt
from .metacritic import get_html, parse, gt_80_lt_1_week
from .spotify import Spotify


version = "0.1.1"


def lambda_handler(e, ctx):
    print("Scraping metacritic")

    html = get_html()
    albums = parse(html)
    albums = list(filter(gt_80_lt_1_week, albums))

    if os.environ["ENVIRONMENT_TYPE"] == "test":
        print("Skipping over Spotify update while in testing environment")
    else:
        print("Updating Spotify new releases playlist")
        api = Spotify(playlist_id="65RYrUbKJgX0eJHBIZ14Fe")

        print("Clearing playlist")
        api.clear_playlist()
        for album in albums:
            query = f"{album['album']} {album['artist']}"
            print(f"Searching for: {query}")
            hit = api.search_for_album(query)
            if hit:
                print(f"Found {query}. Adding to playlist")
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
