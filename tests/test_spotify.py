import requests
import os
import datetime
from metafy.spotify import Auth, Spotify, SpotifyTrack, SpotifyAlbum


def test_auth_acquires_values_from_environment(AuthEnv):
    assert AuthEnv.client_id == "TEST_CLIENT_ID"
    assert AuthEnv.client_secret == "TEST_CLIENT_SECRET"
    assert AuthEnv.ref_tk == "TEST_REF_TK"


def test_token_expiration():
    now = datetime.datetime.now()
    ahead_15s = now + datetime.timedelta(seconds=15)
    behind_10s = now - datetime.timedelta(seconds=10)
    ahead_20s = now + datetime.timedelta(seconds=20)

    auth = Auth()

    auth.token_expires = now
    assert auth.token_expired()
    auth.token_expires = behind_10s
    assert auth.token_expired()
    auth.token_expires = ahead_15s
    assert not auth.token_expired()
    auth.token_expires = ahead_20s
    assert not auth.token_expired()


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


def test_fake_auth_fixture(FakeAuth):
    FakeAuth.get_token_as_header()
