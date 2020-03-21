import os
import unittest
from unittest import mock
import datetime
import mpgen.spotify


def mocked_requests_factory(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    # Spotify.get_tracks_from_playlist, Spotify.get_tracks_from_album
    if "/tracks" in args[0]:
        return MockResponse(tracks_json, 200)
    # Spotify.search_for_album
    elif "/search" in args[0]:
        return MockResponse(search_json, 200)

    return MockResponse(None, 404)


class TestAuth(unittest.TestCase):
    def setUp(self):
        self.auth = mpgen.spotify.Auth("id", "secret", "reftoken")

    def test_acquires_environment_variables(self):
        """
        Tests that Auth is able to take environment variables when no
        initializing parameters are passed at creation time
        """
        os.environ["MPGEN_CLIENT_ID"] = "client_id"
        os.environ["MPGEN_CLIENT_SECRET"] = "client_secret"
        os.environ["MPGEN_REF_TK"] = "ref_tk"

        auth = mpgen.spotify.Auth()

        self.assertEqual(auth.client_id, "client_id")
        self.assertEqual(auth.client_secret, "client_secret")
        self.assertEqual(auth.ref_tk, "ref_tk")

    @mock.patch("mpgen.spotify.Auth.get_token")
    def test_get_auth_header(self, mocktoken):
        """
        Tests that the auth object is able to produce the correct base64
        encoded string to use for authorization
        """
        faketoken = "ABCD1234"
        fakeheader = {"Authorization": "Bearer {}".format(faketoken)}
        mocktoken.return_value = fakeheader

        self.assertTrue(self.auth.get_token_as_header(), fakeheader)

    def test_token_expired(self):
        now = datetime.datetime.now()
        ahead_15s = now + datetime.timedelta(seconds=15)
        behind_10s = now - datetime.timedelta(seconds=10)
        ahead_20s = now + datetime.timedelta(seconds=20)

        self.auth.token_expires = now
        self.assertTrue(self.auth.token_expired())

        self.auth.token_expires = behind_10s
        self.assertTrue(self.auth.token_expired())

        self.auth.token_expires = ahead_15s
        self.assertFalse(self.auth.token_expired())

        self.auth.token_expires = ahead_20s
        self.assertFalse(self.auth.token_expired())


class TestSpotify(unittest.TestCase):
    def setUp(self):
        os.environ["MPGEN_CLIENT_ID"] = "client_id"
        os.environ["MPGEN_CLIENT_SECRET"] = "client_secret"
        os.environ["MPGEN_REF_TK"] = "ref_tk"

    @mock.patch("mpgen.spotify.requests.get", side_effect=mocked_requests_factory)
    @mock.patch("mpgen.spotify.Auth.get_token")
    def test_get_tracks_from_playlist(self, mock_get, mock_token):
        spotify = mpgen.spotify.Spotify()
        tracks = spotify.get_tracks_from_playlist()
        expected = [
            mpgen.spotify.SpotifyTrack("Randy Newman", "The Great Debate", "5hbttdGGhvN9PUZDwgCk67"),
            mpgen.spotify.SpotifyTrack("Randy Newman", "Brothers", "7uc4eht56O5P1Yu45708cU"),
            mpgen.spotify.SpotifyTrack("Randy Newman", "Putin", "5GGYsohgEd9xnTaLE9ChZA")
        ]

        self.assertEqual(tracks, expected)

    @mock.patch("mpgen.spotify.requests.get", side_effect=mocked_requests_factory)
    @mock.patch("mpgen.spotify.Auth.get_token")
    @mock.patch("mpgen.spotify.Spotify.get_tracks_from_album", return_value=[1, 2, 3, 4])
    def test_search_for_album(self, mock_get, mock_token, mock_tracks):
        spotify = mpgen.spotify.Spotify()
        expected = mpgen.spotify.SpotifyAlbum("Rick Astley", "Whenever You Need Somebody", "6XhjNHCyCDyyGJRM5mg40G")
        album = spotify.search_for_album("rick astley whenever")

        self.assertEqual(album, expected)

# JSON results copied from the Spotify API console
tracks_json = {
  "href": "https://api.spotify.com/v1/users/hosackm/playlists/65RYrUbKJgX0eJHBIZ14Fe/tracks?offset=0&limit=3",
  "items": [{
    "added_at": "2017-08-07T08:00:51Z",
    "added_by": {
      "external_urls": {
        "spotify": "http://open.spotify.com/user/hosackm"
      },
      "href": "https://api.spotify.com/v1/users/hosackm",
      "id": "hosackm",
      "type": "user",
      "uri": "spotify:user:hosackm"
    },
    "is_local": False,
    "track": {
      "album": {
        "album_type": "album",
        "artists": [{
          "external_urls": {
            "spotify": "https://open.spotify.com/artist/3HQyFCFFfJO3KKBlUfZsyW"
          },
          "href": "https://api.spotify.com/v1/artists/3HQyFCFFfJO3KKBlUfZsyW",
          "id": "3HQyFCFFfJO3KKBlUfZsyW",
          "name": "Randy Newman",
          "type": "artist",
          "uri": "spotify:artist:3HQyFCFFfJO3KKBlUfZsyW"
        }],
        "available_markets": ["AD", "AR", "AT", "AU", "BE", "BG", "BO", "BR",
                              "CA", "CH", "CL", "CO", "CR", "CY", "CZ", "DE",
                              "DK", "DO", "EC", "EE", "ES", "FI", "FR", "GB",
                              "GR", "GT", "HK", "HN", "HU", "ID", "IE", "IS",
                              "IT", "JP", "LI", "LT", "LU", "LV", "MC", "MT",
                              "MX", "MY", "NI", "NL", "NO", "NZ", "PA", "PE",
                              "PH", "PL", "PT", "PY", "SE", "SG", "SK", "SV",
                              "TR", "TW", "US", "UY"],
        "external_urls": {
          "spotify": "https://open.spotify.com/album/6Yu3m6c7tXFBQMeD42ccvu"
        },
        "href": "https://api.spotify.com/v1/albums/6Yu3m6c7tXFBQMeD42ccvu",
        "id": "6Yu3m6c7tXFBQMeD42ccvu",
        "images": [{
          "height": 640,
          "url": "https://i.scdn.co/image/5e0307d23f6c28e8f7cab5c1029ff5eb6afdd5ad",
          "width": 640
        }, {
          "height": 300,
          "url": "https://i.scdn.co/image/8506a18282c0e908493fe9a67cac20f0929f5a07",
          "width": 300
        }, {
          "height": 64,
          "url": "https://i.scdn.co/image/52fd86d51db95caaae71b4a0e176a52003d6c710",
          "width": 64
        }],
        "name": "Dark Matter",
        "type": "album",
        "uri": "spotify:album:6Yu3m6c7tXFBQMeD42ccvu"
      },
      "artists": [{
        "external_urls": {
          "spotify": "https://open.spotify.com/artist/3HQyFCFFfJO3KKBlUfZsyW"
        },
        "href": "https://api.spotify.com/v1/artists/3HQyFCFFfJO3KKBlUfZsyW",
        "id": "3HQyFCFFfJO3KKBlUfZsyW",
        "name": "Randy Newman",
        "type": "artist",
        "uri": "spotify:artist:3HQyFCFFfJO3KKBlUfZsyW"
      }],
      "available_markets": ["AD", "AR", "AT", "AU", "BE", "BG", "BO", "BR", "CA",
                            "CH", "CL", "CO", "CR", "CY", "CZ", "DE", "DK", "DO",
                            "EC", "EE", "ES", "FI", "FR", "GB", "GR", "GT", "HK",
                            "HN", "HU", "ID", "IE", "IS", "IT", "JP", "LI", "LT",
                            "LU", "LV", "MC", "MT", "MX", "MY", "NI", "NL", "NO",
                            "NZ", "PA", "PE", "PH", "PL", "PT", "PY", "SE", "SG",
                            "SK", "SV", "TR", "TW", "US", "UY"],
      "disc_number": 1,
      "duration_ms": 489053,
      "explicit": False,
      "external_ids": {
        "isrc": "USNO11600845"
      },
      "external_urls": {
        "spotify": "https://open.spotify.com/track/5hbttdGGhvN9PUZDwgCk67"
      },
      "href": "https://api.spotify.com/v1/tracks/5hbttdGGhvN9PUZDwgCk67",
      "id": "5hbttdGGhvN9PUZDwgCk67",
      "name": "The Great Debate",
      "popularity": 37,
      "track_number": 1,
      "type": "track",
      "uri": "spotify:track:5hbttdGGhvN9PUZDwgCk67"
    }
  }, {
    "added_at": "2017-08-07T08:00:51Z",
    "added_by": {
      "external_urls": {
        "spotify": "http://open.spotify.com/user/hosackm"
      },
      "href": "https://api.spotify.com/v1/users/hosackm",
      "id": "hosackm",
      "type": "user",
      "uri": "spotify:user:hosackm"
    },
    "is_local": False,
    "track": {
      "album": {
        "album_type": "album",
        "artists": [{
          "external_urls": {
            "spotify": "https://open.spotify.com/artist/3HQyFCFFfJO3KKBlUfZsyW"
          },
          "href": "https://api.spotify.com/v1/artists/3HQyFCFFfJO3KKBlUfZsyW",
          "id": "3HQyFCFFfJO3KKBlUfZsyW",
          "name": "Randy Newman",
          "type": "artist",
          "uri": "spotify:artist:3HQyFCFFfJO3KKBlUfZsyW"
        }],
        "available_markets": ["AD", "AR", "AT", "AU", "BE", "BG", "BO", "BR",
                              "CA", "CH", "CL", "CO", "CR", "CY", "CZ", "DE",
                              "DK", "DO", "EC", "EE", "ES", "FI", "FR", "GB",
                              "GR", "GT", "HK", "HN", "HU", "ID", "IE", "IS",
                              "IT", "JP", "LI", "LT", "LU", "LV", "MC", "MT",
                              "MX", "MY", "NI", "NL", "NO", "NZ", "PA", "PE",
                              "PH", "PL", "PT", "PY", "SE", "SG", "SK", "SV",
                              "TR", "TW", "US", "UY"],
        "external_urls": {
          "spotify": "https://open.spotify.com/album/6Yu3m6c7tXFBQMeD42ccvu"
        },
        "href": "https://api.spotify.com/v1/albums/6Yu3m6c7tXFBQMeD42ccvu",
        "id": "6Yu3m6c7tXFBQMeD42ccvu",
        "images": [{
          "height": 640,
          "url": "https://i.scdn.co/image/5e0307d23f6c28e8f7cab5c1029ff5eb6afdd5ad",
          "width": 640
        }, {
          "height": 300,
          "url": "https://i.scdn.co/image/8506a18282c0e908493fe9a67cac20f0929f5a07",
          "width": 300
        }, {
          "height": 64,
          "url": "https://i.scdn.co/image/52fd86d51db95caaae71b4a0e176a52003d6c710",
          "width": 64
        }],
        "name": "Dark Matter",
        "type": "album",
        "uri": "spotify:album:6Yu3m6c7tXFBQMeD42ccvu"
      },
      "artists": [{
        "external_urls": {
          "spotify": "https://open.spotify.com/artist/3HQyFCFFfJO3KKBlUfZsyW"
        },
        "href": "https://api.spotify.com/v1/artists/3HQyFCFFfJO3KKBlUfZsyW",
        "id": "3HQyFCFFfJO3KKBlUfZsyW",
        "name": "Randy Newman",
        "type": "artist",
        "uri": "spotify:artist:3HQyFCFFfJO3KKBlUfZsyW"
      }],
      "available_markets": ["AD", "AR", "AT", "AU", "BE", "BG", "BO", "BR",
                            "CA", "CH", "CL", "CO", "CR", "CY", "CZ", "DE",
                            "DK", "DO", "EC", "EE", "ES", "FI", "FR", "GB",
                            "GR", "GT", "HK", "HN", "HU", "ID", "IE", "IS",
                            "IT", "JP", "LI", "LT", "LU", "LV", "MC", "MT",
                            "MX", "MY", "NI", "NL", "NO", "NZ", "PA", "PE",
                            "PH", "PL", "PT", "PY", "SE", "SG", "SK", "SV",
                            "TR", "TW", "US", "UY"],
      "disc_number": 1,
      "duration_ms": 294213,
      "explicit": False,
      "external_ids": {
        "isrc": "USNO11600846"
      },
      "external_urls": {
        "spotify": "https://open.spotify.com/track/7uc4eht56O5P1Yu45708cU"
      },
      "href": "https://api.spotify.com/v1/tracks/7uc4eht56O5P1Yu45708cU",
      "id": "7uc4eht56O5P1Yu45708cU",
      "name": "Brothers",
      "popularity": 34,
      "track_number": 2,
      "type": "track",
      "uri": "spotify:track:7uc4eht56O5P1Yu45708cU"
    }
  }, {
    "added_at": "2017-08-07T08:00:51Z",
    "added_by": {
      "external_urls": {
        "spotify": "http://open.spotify.com/user/hosackm"
      },
      "href": "https://api.spotify.com/v1/users/hosackm",
      "id": "hosackm",
      "type": "user",
      "uri": "spotify:user:hosackm"
    },
    "is_local": False,
    "track": {
      "album": {
        "album_type": "album",
        "artists": [{
          "external_urls": {
            "spotify": "https://open.spotify.com/artist/3HQyFCFFfJO3KKBlUfZsyW"
          },
          "href": "https://api.spotify.com/v1/artists/3HQyFCFFfJO3KKBlUfZsyW",
          "id": "3HQyFCFFfJO3KKBlUfZsyW",
          "name": "Randy Newman",
          "type": "artist",
          "uri": "spotify:artist:3HQyFCFFfJO3KKBlUfZsyW"
        }],
        "available_markets": ["AD", "AR", "AT", "AU", "BE", "BG", "BO", "BR",
                              "CA", "CH", "CL", "CO", "CR", "CY", "CZ", "DE",
                              "DK", "DO", "EC", "EE", "ES", "FI", "FR", "GB",
                              "GR", "GT", "HK", "HN", "HU", "ID", "IE", "IS",
                              "IT", "JP", "LI", "LT", "LU", "LV", "MC", "MT",
                              "MX", "MY", "NI", "NL", "NO", "NZ", "PA", "PE",
                              "PH", "PL", "PT", "PY", "SE", "SG", "SK", "SV",
                              "TR", "TW", "US", "UY"],
        "external_urls": {
          "spotify": "https://open.spotify.com/album/6Yu3m6c7tXFBQMeD42ccvu"
        },
        "href": "https://api.spotify.com/v1/albums/6Yu3m6c7tXFBQMeD42ccvu",
        "id": "6Yu3m6c7tXFBQMeD42ccvu",
        "images": [{
          "height": 640,
          "url": "https://i.scdn.co/image/5e0307d23f6c28e8f7cab5c1029ff5eb6afdd5ad",
          "width": 640
        }, {
          "height": 300,
          "url": "https://i.scdn.co/image/8506a18282c0e908493fe9a67cac20f0929f5a07",
          "width": 300
        }, {
          "height": 64,
          "url": "https://i.scdn.co/image/52fd86d51db95caaae71b4a0e176a52003d6c710",
          "width": 64
        }],
        "name": "Dark Matter",
        "type": "album",
        "uri": "spotify:album:6Yu3m6c7tXFBQMeD42ccvu"
      },
      "artists": [{
        "external_urls": {
          "spotify": "https://open.spotify.com/artist/3HQyFCFFfJO3KKBlUfZsyW"
        },
        "href": "https://api.spotify.com/v1/artists/3HQyFCFFfJO3KKBlUfZsyW",
        "id": "3HQyFCFFfJO3KKBlUfZsyW",
        "name": "Randy Newman",
        "type": "artist",
        "uri": "spotify:artist:3HQyFCFFfJO3KKBlUfZsyW"
      }],
      "available_markets": ["AD", "AR", "AT", "AU", "BE", "BG", "BO", "BR",
                            "CA", "CH", "CL", "CO", "CR", "CY", "CZ", "DE",
                            "DK", "DO", "EC", "EE", "ES", "FI", "FR", "GB",
                            "GR", "GT", "HK", "HN", "HU", "ID", "IE", "IS",
                            "IT", "JP", "LI", "LT", "LU", "LV", "MC", "MT",
                            "MX", "MY", "NI", "NL", "NO", "NZ", "PA", "PE",
                            "PH", "PL", "PT", "PY", "SE", "SG", "SK", "SV",
                            "TR", "TW", "US", "UY"],
      "disc_number": 1,
      "duration_ms": 224160,
      "explicit": False,
      "external_ids": {
        "isrc": "USNO11600662"
      },
      "external_urls": {
        "spotify": "https://open.spotify.com/track/5GGYsohgEd9xnTaLE9ChZA"
      },
      "href": "https://api.spotify.com/v1/tracks/5GGYsohgEd9xnTaLE9ChZA",
      "id": "5GGYsohgEd9xnTaLE9ChZA",
      "name": "Putin",
      "popularity": 34,
      "track_number": 3,
      "type": "track",
      "uri": "spotify:track:5GGYsohgEd9xnTaLE9ChZA"
    }
  }],
  "limit": 3,
  "next": "https://api.spotify.com/v1/users/hosackm/playlists/65RYrUbKJgX0eJHBIZ14Fe/tracks?offset=3&limit=3",
  "offset": 0,
  "previous": "null",
  "total": 19
}

search_json = {
  "albums": {
    "href": "https://api.spotify.com/v1/search?query=rick+astley&type=album&market=US&offset=0&limit=2",
    "items": [{
      "album_type": "album",
      "artists": [{
        "external_urls": {
          "spotify": "https://open.spotify.com/artist/0gxyHStUsqpMadRV0Di1Qt"
        },
        "href": "https://api.spotify.com/v1/artists/0gxyHStUsqpMadRV0Di1Qt",
        "id": "0gxyHStUsqpMadRV0Di1Qt",
        "name": "Rick Astley",
        "type": "artist",
        "uri": "spotify:artist:0gxyHStUsqpMadRV0Di1Qt"
      }],
      "available_markets": ["AR", "BO", "BR", "CA", "CH", "CL", "CO", "CR",
                            "DO", "EC", "GT", "HK", "HN", "ID", "JP", "LI",
                            "MX", "MY", "NI", "PA", "PE", "PH", "PY", "SG",
                            "SV", "TW", "US", "UY"],
      "external_urls": {
        "spotify": "https://open.spotify.com/album/6XhjNHCyCDyyGJRM5mg40G"
      },
      "href": "https://api.spotify.com/v1/albums/6XhjNHCyCDyyGJRM5mg40G",
      "id": "6XhjNHCyCDyyGJRM5mg40G",
      "images": [{
        "height": 640,
        "url": "https://i.scdn.co/image/15ac2c9091d9b74e841b281ceb23ca8208321444",
        "width": 640
      }, {
        "height": 300,
        "url": "https://i.scdn.co/image/90ed6823864381221c03dc3c9fc62d094e81dfb2",
        "width": 300
      }, {
        "height": 64,
        "url": "https://i.scdn.co/image/568017ab80000e71ca299909806898f75a948456",
        "width": 64
      }],
      "name": "Whenever You Need Somebody",
      "type": "album",
      "uri": "spotify:album:6XhjNHCyCDyyGJRM5mg40G"
    }, {
      "album_type": "compilation",
      "artists": [{
        "external_urls": {
          "spotify": "https://open.spotify.com/artist/0gxyHStUsqpMadRV0Di1Qt"
        },
        "href": "https://api.spotify.com/v1/artists/0gxyHStUsqpMadRV0Di1Qt",
        "id": "0gxyHStUsqpMadRV0Di1Qt",
        "name": "Rick Astley",
        "type": "artist",
        "uri": "spotify:artist:0gxyHStUsqpMadRV0Di1Qt"
      }],
      "available_markets": ["US"],
      "external_urls": {
        "spotify": "https://open.spotify.com/album/3vGtqTr5he9uQfusQWJ0oC"
      },
      "href": "https://api.spotify.com/v1/albums/3vGtqTr5he9uQfusQWJ0oC",
      "id": "3vGtqTr5he9uQfusQWJ0oC",
      "images": [{
        "height": 634,
        "url": "https://i.scdn.co/image/d0c3c73e7dc4c3ccf921e2f3c86969aa7181bcab",
        "width": 640
      }, {
        "height": 297,
        "url": "https://i.scdn.co/image/463e545ef86af314c4b7c79ff17892531a80770e",
        "width": 300
      }, {
        "height": 63,
        "url": "https://i.scdn.co/image/f0123bce1178d3c4fa991c55d88fea951fdff4e8",
        "width": 64
      }],
      "name": "Platinum & Gold Collection",
      "type": "album",
      "uri": "spotify:album:3vGtqTr5he9uQfusQWJ0oC"
    }],
    "limit": 2,
    "next": "https://api.spotify.com/v1/search?query=rick+astley&type=album&market=US&offset=2&limit=2",
    "offset": 0,
    "previous": "null",
    "total": 70
  }
}

albums_json = {
  "href": "https://api.spotify.com/v1/albums/6XhjNHCyCDyyGJRM5mg40G/tracks?offset=0&limit=2",
  "items": [{
    "artists": [{
      "external_urls": {
        "spotify": "https://open.spotify.com/artist/0gxyHStUsqpMadRV0Di1Qt"
      },
      "href": "https://api.spotify.com/v1/artists/0gxyHStUsqpMadRV0Di1Qt",
      "id": "0gxyHStUsqpMadRV0Di1Qt",
      "name": "Rick Astley",
      "type": "artist",
      "uri": "spotify:artist:0gxyHStUsqpMadRV0Di1Qt"
    }],
    "available_markets": ["AR", "BO", "BR", "CA", "CH", "CL", "CO", "CR", "DO",
                          "EC", "GT", "HK", "HN", "ID", "JP", "LI", "MX", "MY",
                          "NI", "PA", "PE", "PH", "PY", "SG", "SV", "TW", "US",
                          "UY"],
    "disc_number": 1,
    "duration_ms": 212826,
    "explicit": False,
    "external_urls": {
      "spotify": "https://open.spotify.com/track/7GhIk7Il098yCjg4BQjzvb"
    },
    "href": "https://api.spotify.com/v1/tracks/7GhIk7Il098yCjg4BQjzvb",
    "id": "7GhIk7Il098yCjg4BQjzvb",
    "name": "Never Gonna Give You Up",
    "track_number": 1,
    "type": "track",
    "uri": "spotify:track:7GhIk7Il098yCjg4BQjzvb"
  }, {
    "artists": [{
      "external_urls": {
        "spotify": "https://open.spotify.com/artist/0gxyHStUsqpMadRV0Di1Qt"
      },
      "href": "https://api.spotify.com/v1/artists/0gxyHStUsqpMadRV0Di1Qt",
      "id": "0gxyHStUsqpMadRV0Di1Qt",
      "name": "Rick Astley",
      "type": "artist",
      "uri": "spotify:artist:0gxyHStUsqpMadRV0Di1Qt"
    }],
    "available_markets": ["AR", "BO", "BR", "CA", "CH", "CL", "CO", "CR", "DO",
                          "EC", "GT", "HK", "HN", "ID", "JP", "LI", "MX", "MY",
                          "NI", "PA", "PE", "PH", "PY", "SG", "SV", "TW", "US",
                          "UY"],
    "disc_number": 1,
    "duration_ms": 232960,
    "explicit": False,
    "external_urls": {
      "spotify": "https://open.spotify.com/track/5qUAdDl59w0Vbu4Gi6ecSX"
    },
    "href": "https://api.spotify.com/v1/tracks/5qUAdDl59w0Vbu4Gi6ecSX",
    "id": "5qUAdDl59w0Vbu4Gi6ecSX",
    "name": "Whenever You Need Somebody",
    "track_number": 2,
    "type": "track",
    "uri": "spotify:track:5qUAdDl59w0Vbu4Gi6ecSX"
  }],
  "limit": 2,
  "next": "https://api.spotify.com/v1/albums/6XhjNHCyCDyyGJRM5mg40G/tracks?offset=2&limit=2",
  "offset": 0,
  "previous": "null",
  "total": 10
}

if __name__ == "__main__":
    unittest.main()
