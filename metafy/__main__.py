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

from . import version
from .code import codeflow
from .__lambdas__ import metacritic_lambda, spotify_lambda


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
@click.option("--output", default="metafy.zip", help="filename of zip package")
def build_pkg(output):
    """
    Package mpgen and dependent Python packages into zip for uploading to
    AWS Lambda instance.  Everything is flattened into the same zip folder.
    """
    click.echo("Building AWS Lambda package ({})".format(output))

    # make temporary working dir
    with tempfile.TemporaryDirectory(prefix="metafy") as tmpdir:
        package_path = os.path.join(tmpdir, "metafy")
        os.makedirs(package_path)

        # copy src files
        for f in glob.glob("metafy/*.py"):
            copy_file_or_dir(f, package_path)

        # copy packages
        if "Windows" in platform.platform():
            packages_glob = "venvdocker/Lib/site-packages/*"
        else:
            packages_glob = "venvdocker/lib*/python3.7/site-packages/*"

        for f in glob.glob(packages_glob):
            if "metafy" in f:
                # avoid recursive addition of this package
                continue
            copy_file_or_dir(f, tmpdir)

        # zip everything up and remove tmp folder
        base, _ = os.path.splitext(output)
        shutil.make_archive(base, "zip", tmpdir)


@cli.command()
@click.option("--s3-upload/--no-s3-upload", default=False)
def scrape(s3_upload):
    # only add s3-upload key if it's true
    ev = {"s3-upload": s3_upload} if s3_upload else {}
    metacritic_lambda(ev, None)


@cli.command()
def update_playlist():
    spotify_lambda(None, {})


@cli.command()
def get_token():
    click.echo("Running code authorization flow")
    codeflow()


if __name__ == "__main__":
    cli()
