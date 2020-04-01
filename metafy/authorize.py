import webbrowser
import requests
from pprint import pprint
from base64 import b64encode
from urllib.parse import quote, urlparse


def main():
    # build correct URL to visit for User's authorization
    base = "https://accounts.spotify.com/authorize?response_type=code"
    client_id = input("Enter Spotify Client ID: ")
    client_secret = input("Enter Spotify Client Secret: ")
    redirect_uri = input("Enter Spotify Redirect URI: ")
    scopes = ["playlist-read-collaborative",
              "playlist-modify-public",
              "playlist-read-private",
              "playlist-modify-private"]
    url = (f"{base}&client_id={client_id}&client_secret={client_secret}"
           f"&redirect_uri={quote(redirect_uri)}&scope={'%20'.join(scopes)}")

    # Open browser to allow Spotify Login
    webbrowser.open(url)

    # Ask for the redirected URL that contains the code as a URL query param
    codeurl = input("Copy/paste URL you were directed to just now: ")
    code = urlparse(codeurl).query.split("=")[-1]

    # POST code and auth values to the Spotify token URL
    data = {"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri}
    encoded_secret = b64encode(f"{client_id}:{client_secret}".encode("utf8")).decode("utf8")
    headers = {"Authorization": f"Basic {encoded_secret}"}

    # read the response that contains the token
    resp = requests.post("https://accounts.spotify.com/api/token", data=data, headers=headers)
    if resp.status_code != 200:
        print("Error POST-ing data for a token")
    pprint(resp.json())


if __name__ == "__main__":
    main()
