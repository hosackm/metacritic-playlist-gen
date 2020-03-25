import os
import json
from datetime import datetime
from io import BytesIO
from boto3 import Session

from .spotify import Spotify
from .metacritic import get_html, parse, gt_80_lt_1_week, upload


def spotify_lambda(e, ctx):
    print("Updating Spotify new releases playlist")

    bucket = os.environ["S3_BUCKET_NAME"]
    object_name = os.environ["S3_OBJECT_NAME"]
    region = os.environ["S3_BUCKET_REGION"]
    secret_key = os.environ["SECRET_KEY"]
    key_id = os.environ["KEY_ID"]

    api = Spotify(playlist_id="65RYrUbKJgX0eJHBIZ14Fe")

    session = Session(aws_access_key_id=key_id, aws_secret_access_key=secret_key, region_name=region)
    bucket = session.resource("s3").Bucket(bucket)

    with BytesIO() as f:
        bucket.download_fileobj(Key=object_name, Fileobj=f)
        f.seek(0)
        albums = json.loads(f.read().decode("utf8"))

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
