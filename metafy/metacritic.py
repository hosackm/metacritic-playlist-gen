import time
import requests
from random import choice
from datetime import datetime as dt, timedelta as td
from typing import Optional, Type, Union, List, Generator, Dict

from bs4 import BeautifulSoup

from .albums import AlbumSource, Album


MONTH_DAY_YEAR_FMT = "%b %d %Y"


def acquire_user_agent():
    "Return a User Agent that metacritic won't expect a scraper to use"
    url = "https://www.whatismybrowser.com/guides/the-latest-user-agent/chrome"
    resp = requests.get(url)
    return choice([a.text
                   for a in BeautifulSoup(
                       resp.content, "html.parser").select("span.code")])


def gt_80_lt_1_week(album: Dict) -> bool:
    "Return True if the album was released in the past week"
    now = dt.now()
    weekago = now - td(days=7)
    date = dt.strptime(album["date"], MONTH_DAY_YEAR_FMT)

    # older than now, newer than a week ago, and gte to 80
    if date <= now and date >= weekago and album["score"] >= 80:
        return True
    return False


class MetacriticSource(AlbumSource):
    URL = "https://www.metacritic.com/browse/albums/release-date/new-releases/date"

    def __init__(self):
        super().__init__()
        self.name = "Metacritic Source"

    def get_html(self, retries: int=3) -> bytes:
        "Return the HTML content from metacritic's new releases page"
        rsp = requests.get(self.URL, headers={"User-Agent": f"{acquire_user_agent()}"})

        if rsp.status_code == 429:
            if retries > 0:
                t = int(rsp.headers.get("Retry-After", 5))
                print(f"Sleeping {t} seconds and retrying")
                time.sleep(t)
                self.get_html(retries=retries-1)
            raise Exception("Rate limitation exceeeded. Try again later.")
        elif rsp.status_code == 403:
            raise Exception("HTML resource forbidden. Try different User-Agent in request header.")
        elif rsp.status_code != 200:
            raise Exception("Unresolved HTTP error. Status code ({rsp.status_code})")

        return rsp.content

    def deduce_and_replace_year(self, month_and_day: str) -> str:
        """
        Given a month and a day this function will deduce the year and place it into the
        date formatted string.  Albums that come from a different year must be handled
        properly.
        """
        now = dt.now()
        # can't create a datetime on a leap day without the correct year specified
        # good thing I developed this on a leap year...
        if month_and_day == "Feb 29":
            d = dt(month=2, day=29, year=now.year)
        else:
            d = dt.strptime(month_and_day, "%b %d").replace(year=now.year)

        # metacritic doesn't put old or futuristic albums on the front page.
        # I use 4 months as a threshold for "old/futuristic".
        month_diff = now.month - d.month
        if month_diff > 4:
            d = d.replace(year=now.year+1)
        elif month_diff < -4:
            d = d.replace(year=now.year-1)

        return dt.strftime(d, MONTH_DAY_YEAR_FMT)

    def strip_select_as_type(self,
                             soup,
                             selector: str,
                             as_type: Optional[Type]=None) -> Union[int, dt, str]:
        """
        Given a Soup object return the first instance of CSS selector,
        strip the text, and perform an optional type casting
        """
        text = soup.select(selector)[0].text
        text = text.replace("Release Date:", "").strip()

        if as_type == int:
            try:
                return int(text)
            except ValueError:
                return 0  # "tbd" is an acceptible value for score
        elif as_type == dt:
            return self.deduce_and_replace_year(text)
        return text

    def parse(self, text: bytes) -> List[Dict]:
        "Parse out album information from the provided HTML string"
        soup = BeautifulSoup(text, "html.parser")
        return [
            {
                "date": self.strip_select_as_type(p, "li.release_date", dt),
                "score": self.strip_select_as_type(p, "div.metascore_w", int),
                "album": self.strip_select_as_type(p, "div.product_title > a"),
                "artist": self.strip_select_as_type(p, "li.product_artist > span.data")
            } for p in soup.select("div.product_wrap")
        ]

    def gen_albums(self) -> Generator[Album, None, None]:
        for a in filter(gt_80_lt_1_week, self.parse(self.get_html())):
            yield Album(title=a["album"], artist=a["artist"], source=self.name,
                        img="https://google.com/img.jpg", rating=a["score"], date=a["date"])
