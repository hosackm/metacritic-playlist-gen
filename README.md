# Metafy
Metafy a program that will create a [Spotify playlist](https://open.spotify.com/playlist/65RYrUbKJgX0eJHBIZ14Fe?si=-TBJlxIFQtGiU0dT45Mxqw) of albums that were highly rated on Metacritic.  It runs weekly on Monday mornings and generates a playlist based on the previous weeks best rated albums.

## Install
To install the package run:

    python3 -m virtualenv venv
    . venv/bin/activate
    pip install .

To check that everything installed correctly you can run the unit tests:

    python setup.py pytest
