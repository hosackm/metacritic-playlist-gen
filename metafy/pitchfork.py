import requests
from typing import List, Dict
from datetime import datetime as dt
from urllib.parse import unquote
from metafy.albums import AlbumSource, Album

from bs4 import BeautifulSoup


class PitchforkSource(AlbumSource):
    URL = "https://pitchfork.com/best"

    def __init__(self):
        super().__init__()
        self.name = "Pitchfork Source"

    def get_html(self) -> bytes:
        resp = requests.get(self.URL)
        return resp.content

    def parse(self, content: bytes) -> List[Dict]:
        soup = BeautifulSoup(content, "html.parser")
        section = soup.select("#best-new-albums")[0]
        albums_html = section.select("ul li div a")

        albums = []
        for a in albums_html:
            artist = a.select("li")
            if not artist:
                continue
            artist = artist[0].text
            title = a.find("h2").text
            img = unquote(a.find("img")["src"])
            albums.append({"img": img,
                           "artist": artist,
                           "title": title,
                           "date": dt.now(),  # date information isn't available on this page
                           "rating": 100})  # rating isn't available but we know it's recommended by Pitchfork
        return albums

    def gen_albums(self):
        for a in self.parse(self.get_html()):
            yield Album(title=a["title"], artist=a["artist"], source=self.name,
                        img=a["img"], rating=100, date=a["date"])
