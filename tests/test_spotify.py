import requests
import os
import datetime
from metafy.spotify import SpotifyAuth, Spotify, SpotifyTrack, SpotifyAlbum


def test_spotify_get_tracks_playlist(MockedSpotifyAPI):
    spotify = MockedSpotifyAPI
    tracks = spotify.get_tracks_from_playlist()

    assert len(tracks) == 3
    assert tracks == [
        SpotifyTrack("Randy Newman", "The Great Debate", "5hbttdGGhvN9PUZDwgCk67"),
        SpotifyTrack("Randy Newman", "Brothers", "7uc4eht56O5P1Yu45708cU"),
        SpotifyTrack("Randy Newman", "Putin", "5GGYsohgEd9xnTaLE9ChZA")
    ]


def test_spotify_search_returns_correct_albums(MockedSpotifyAPI):
    spotify = MockedSpotifyAPI
    album = spotify.search_for_album("rick astley whenever")
    expected = SpotifyAlbum("Rick Astley", "Whenever You Need Somebody", "6XhjNHCyCDyyGJRM5mg40G")

    assert album == expected
