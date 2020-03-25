import os
import json
import boto3
from datetime import datetime

from .spotify import Spotify
from .metacritic import get_html, parse, gt_80_lt_1_week, upload


def spotify_lambda(e, ctx):
    print("Updating Spotify new releases playlist")

    api = Spotify(playlist_id="65RYrUbKJgX0eJHBIZ14Fe")
    kw = {"Bucket": "metacritic-releases", "Key": "albums.json"}
    body = boto3.client("s3").get_object(**kw)["Body"]
    print("Got albums.json from s3")
    albums = json.loads(body.read().decode("utf8"))

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

    description = f"""(Updated {datetime.strftime(datetime.today(), '%b %d %Y')}). \
This playlist was created using a script written by Matt Hosack.  The new \
release page from metacritic.com was scraped and albums realeased more \
recently than a week ago that scored higher than 80 were \
added to this playlist. \
See github.com/hosackm/metacritic-playlist-gen for more info."""
    api.update_playlist_description(description)

    return {"status": "completed successfully"}


def metacritic_lambda(e, ctx):
    print("Entered Metacritic lambda handler")

    do_upload = False
    if "s3-upload" in ctx or os.environ.get("EXECUTION_ENVIRONMENT") == "lambda":
        do_upload = True

    html = get_html()
    albums = parse(html)
    albums = list(filter(gt_80_lt_1_week, albums))
    if do_upload:
        print("Uploading albums.json to s3")
        upload(albums)

    return {"status": "completed successfully"}
