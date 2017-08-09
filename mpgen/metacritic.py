import requests
from datetime import datetime
from bs4 import BeautifulSoup as Soup


class Scraper:
    """
    Scrapes the most recent Metacritic New Album Realeses page
    """
    def __init__(self):
        self.url = ("http://www.metacritic.com/browse/"
                    "albums/release-date/new-releases/date")

    def scrape_html(self):
        """
        Make a request for the most recent Metacritic New Album Releases page

        Return the html text or raise and Exception if the request failed
        """
        resp = requests.get(self.url,
                            headers={"User-Agent": "MPGEN-Scraper"})

        if resp.status_code != 200:
            raise Exception("Unable to scrape {url}".format(url=self.url))

        html = resp.text

        # Take html from metacritic and return a list of parsed albums from it
        soup = Soup(html, "html.parser")
        soup.find("ol", {"class": "list_products"})

        return [Album.from_list_item(list_item)
                for list_item
                in soup.findAll("li", {"class": "product"})]


class Album:
    """
    Represents an album parsed from Metacritic's site.  Each album
    has a date, artist, title, and rating associated with it

    If an album is not yet rated (usually for upcoming albums) the rating is
    assumed to be 0 (harsh)
    """
    def __init__(self, date, rating, title, artist):
        self.date = date
        self.artist = artist
        self.rating = rating
        self.title = title

    def __repr__(self):
        return ("Album(date='{date}', artist='{artist}', "
                "title='{title}', rating='{rating}')").format(
                    date=self.date,
                    artist=self.artist,
                    title=self.title,
                    rating=self.rating)

    @classmethod
    def from_list_item(cls, li):
        """
        Parse date, rating, title, and artist of from an <li> tag soup object

        ex:
        <li>
          <div class="product_score">100</div>
          <div class="product_title">Some Title</div>
          <li class="release_date"><span class="data">Jan 12</span></li>
          <li class="product_artist"><span class="data">Some Artist</span></li>
        </li>

        would parse to:
            Jan 12 (current or previous four-digit year)
            Some Title
            Some Artist
            100
        """
        rating_text = li.find("div", {"class": "product_score"}).text.strip()
        title_text = li.find("div", {"class": "product_title"}).text.strip()
        date_text = li.find("li",
                            {"class": "release_date"}
                            ).find("span",
                                   {"class": "data"}).text.strip()
        artist_text = li.find("li",
                              {"class": "product_artist"}
                              ).find("span", {"class": "data"}).text.strip()

        title = MetaTitle(title_text)
        artist = MetaArtist(artist_text)

        # convert rating in string form to int. 'tbd' is converted to 0
        try:
            rt = int(rating_text)
        except ValueError:
            rt = 0
        finally:
            rating = MetaRating(rt)

        date = MetaDate.strptime(date_text, "%b %d")
        # assume the the year is the current year
        date = date.replace(year=datetime.now().year)

        # metacritic doesn't report albums 3 months ahead of their release
        if date.month >= datetime.now().month + 3:
            # this album must be from last year
            # ie. it's Jan and this album was release in Dec
            date = date.replace(year=date.year-1)

        return cls(date=date, rating=rating, title=title, artist=artist)


class MetaDate(datetime):
    pass


class MetaRating(int):
    pass


class MetaTitle(str):
    pass


class MetaArtist(str):
    pass


if __name__ == "__main__":
    scraper = Scraper()
    albums = scraper.scrape_html()
    print(albums[0])
    print(albums[-1])
