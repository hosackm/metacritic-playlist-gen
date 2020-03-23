import os
import shutil
import glob
import sys
import tempfile
import platform
from datetime import datetime

import click
import boto3
import json
from scrapy.crawler import CrawlerProcess

from . import version
from .spotify import Spotify
from .metacritic import MetacriticSpider
from .code import codeflow


@click.group()
def cli():
    click.echo("Running metafy version {}".format(version))


def copy_file_or_dir(src, dst):
    """
    Copy files or directories to the dst folder. Ignore __pycache__ and
    easy_install.sh
    """
    if "__pycache__" in src or "easy_install.py" in src:
        return

    print("copying {}".format(src))
    try:
        shutil.copytree(src, os.path.join(dst, os.path.basename(src)))
    except NotADirectoryError:
        shutil.copy(src, dst)


@cli.command()
@click.option("--output", default="lambda_package.zip", help="filename of zip package")
def build_pkg(output):
    """
    Package mpgen and dependent Python packages into zip for uploading to
    AWS Lambda instance.  Everything is flattened into the same zip folder.
    """
    click.echo("Building AWS Lambda package ({})".format(output))

    # make temporary working dir
    with tempfile.TemporaryDirectory(prefix="metafy") as tmpdir:
        # copy src files
        for f in glob.glob("metafy/*.py"):
            copy_file_or_dir(f, os.path.join(tmpdir, "metafy"))

        # copy packages
        if "Windows" in platform.platform():
            packages_glob = "venv/Lib/site-packages/*"
        else:
            mj, mn = sys.version_info[:2]
            packages_glob = "venv/lib/python{0}.{1}/site-packages/*".format(mj, mn)

        for f in glob.glob(packages_glob):
            copy_file_or_dir(f, tmpdir)

        # zip everything up and remove tmp folder
        shutil.make_archive("metafy", "zip", tmpdir)


@cli.command()
def scrape():
    click.echo("Scraping Metacritic new releases page")

    settings = {
        "ITEM_PIPELINES": {
            'main.AlbumsPipeline': 300,
        },
        "AWS_SECRET_ACCESS_KEY": os.environ["KEY_ID"],
        "AWS_ACCESS_KEY_ID": os.environ["SECRET_KEY"],
    }
    crawler = CrawlerProcess(settings)
    crawler.crawl(MetacriticSpider)
    crawler.start()


@cli.command()
def update_playlist():
    click.echo("Updating Spotify new releases playlist")

    api = Spotify(playlist_id="65RYrUbKJgX0eJHBIZ14Fe")
    data = boto3.client("s3").get_object(Bucket="metacritic-releases", Key="albums.json")["Body"].read().decode("utf8")
    albums = json.loads(data)

    api.clear_playlist()
    for album in albums:
        query = "{} {}".format(album["album"], album["artist"])
        hit = api.search_for_album(query)
        if hit:
            tracks = api.get_tracks_from_album(hit)
            api.add_tracks_to_playlist(tracks)

    description = ("(Updated {}).  "
                   "This playlist was created using a script written by Matt Hosack.  The new "
                   "release page from metacritic.com was scraped and albums realeased more"
                   "recently than a week ago that scored higher than 80 were "
                   "added to this playlist."
                   "See github.com/hosackm/metacritic-playlist-gen for more info.".format(
                       datetime.strftime(datetime.today(), "%b %d %Y")))
    api.update_playlist_description(description)


@cli.command()
def get_token():
    click.echo("Running code authorization flow")
    codeflow()


if __name__ == "__main__":
    cli()
