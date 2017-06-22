import os
import unittest
import mpgen.spotify as sptfy
from base64 import b64encode as b64enc


class TestAuth(unittest.TestCase):
    def test_acquires_environment_variables(self):
        """
        Tests that Auth is able to take environment variables when no
        initializing parameters are passed at creation time
        """
        os.environ["MPGEN_CLIENT_ID"] = "client_id"
        os.environ["MPGEN_CLIENT_SECRET"] = "client_secret"
        os.environ["MPGEN_AUTH_TK"] = "auth_tk"
        os.environ["MPGEN_REF_TK"] = "ref_tk"

        auth = sptfy.Auth()

        self.assertEqual(auth.client_id, "client_id")
        self.assertEqual(auth.client_secret, "client_secret")
        self.assertEqual(auth.auth_tk, "auth_tk")
        self.assertEqual(auth.ref_tk, "ref_tk")

    def test_b64_encoding(self):
        """
        Tests that the auth object is able to produce the correct base64
        encoded string to use for authorization
        """
        cid = "abcdefg"
        csec = "hijklmn"

        auth = sptfy.Auth(
            client_id=cid,
            client_secret=csec,
            redirect_uri="xxx",
            auth_tk="xxx",
            ref_tk="xxx"
            )
        tmpl = "{}:{}"
        expected = b64enc(tmpl.format(cid, csec).encode("utf8")).decode("utf8")

        self.assertTrue(auth._get_b64_encoded_string(), expected)


class TestSpotifyTrack(unittest.TestCase):
    def test_each_track_parses_correctly(self):
        track = sptfy.SpotifyTrack.from_track_json(fake_track_response)
        self.assertEqual(track.artist, "Beyoncé")
        self.assertEqual(track.track_id, "4JehYebiI9JE8sR8MisGVb")
        self.assertEqual(track.title, "Halo")


fake_track_response = {
  "artists": [{
    "name": "Beyoncé"
  }],
  "id": "4JehYebiI9JE8sR8MisGVb",
  "name": "Halo"
}

if __name__ == "__main__":
    unittest.main()
