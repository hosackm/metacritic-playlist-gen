import os
import webbrowser
import requests
from urllib.parse import urlparse
from base64 import b64encode as b64e
from pprint import pprint


def codeflow():
    clientid = os.environ["SPOTIFY_CLIENT_ID"]
    clientsecret = os.environ["SPOTIFY_CLIENT_SECRET"]

    # build URL as per Spotify's web API guidelines
    url = "https://accounts.spotify.com/en/authorize"
    url += "?client_id=1d250b7639af49efadbe82b1b675f189"
    url += "&response_type=code"
    url += "&redirect_uri=http:%2F%2Fexample.com"
    url += "%20".join(["&scope=playlist-read-private",
                       "playlist-modify-public",
                       "playlist-modify-private"])

    # visit the Spotify authorization website
    webbrowser.open(url)

    # get URL from browser so we can extract the code query param
    redirect = input("Enter the redirected URL: ")
    code = urlparse(redirect).query.split("code=")[-1]

    token_url = "https://accounts.spotify.com/api/token"
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "http://example.com"
    }
    token_header = {
        "Authorization": "Basic {}".format(
            b64e("{}:{}".format(clientid, clientsecret).encode(
                "utf8")).decode(
                    "utf8"))
    }

    resp = requests.post(token_url, headers=token_header, data=token_data)
    print()
    pprint(resp.json())
