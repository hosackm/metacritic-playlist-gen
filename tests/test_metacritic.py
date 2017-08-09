import os
import unittest
from unittest.mock import patch
import mpgen.metacritic as metacritic
from datetime import datetime, timedelta
from bs4 import BeautifulSoup as Soup

FILEPATH = os.path.join(os.path.dirname(__file__),
                        "resources", "metacritic_sample.html")


class TestMetacriticParse(unittest.TestCase):
    """
    Test the Album class by parsing static html and making sure the values
    are what we expect
    """
    def setUp(self):
        """
        Setup mock for HTTP request method and do scraping
        """
        self.patcher = patch("mpgen.metacritic.requests.get")
        self.mockobj = self.patcher.start()

        self.mockobj.return_value.status_code = 200
        with open(FILEPATH, encoding="utf8") as f:
            self.mockobj.return_value.text = f.read()

        self.scraper = metacritic.Scraper()
        self.albums = self.scraper.scrape_html()

    def tearDown(self):
        "Teardown mock"
        self.patcher.stop()

    def test_first_and_last_parsed_correctly(self):
        """
        Test the date was parsed from the first and last albums correctly
        """
        first_album, last_album = self.albums[0], self.albums[-1]

        self.assertEqual(first_album.date,
                         datetime.strptime("Jun 23 2017", "%b %d %Y"))
        self.assertEqual(first_album.artist, "Jeff Tweedy")
        self.assertEqual(first_album.rating, 77)
        self.assertEqual(first_album.title, "Together At Last")

        self.assertEqual(last_album.date,
                         datetime.strptime("Apr 28 2017", "%b %d %Y"))
        self.assertEqual(last_album.artist, "Los Angeles Police Department")
        self.assertEqual(last_album.rating, 80)
        self.assertEqual(last_album.title, "Los Angeles Police Department")

    def test_all_albums_have_valid_data(self):
        """
        Make sure data has been parsed correctly
        """
        for album in self.albums:
            assert album.artist != ""
            assert album.title != ""
            assert album.date is not None
            assert 0 <= album.rating <= 100

    def test_correct_number_albums_parsed(self):
        assert len(self.albums) == 200

    def test_january_december_year_calculation(self):
        """
        Metacritic does not display dates so the MetaDate must infer the date
        if the current month is January and the album was released in December
        we must make sure the year of the album is one less than the current
        year
        """
        now = datetime.now()
        more_than_three_months_ahead = now + timedelta(weeks=16)
        three_months_html = """
            <li>
            <div class="product_score">{0}</div>
            <div class="product_title">{1}</div>
            <li class="release_date"><span class="data">{2}</span></li>
            <li class="product_artist"><span class="data">{3}</span></li>
            </li>
            """.format(93, "",
                       more_than_three_months_ahead.strftime("%b %d"), "")
        li_soup = Soup(three_months_html, "html.parser")

        album = metacritic.Album.from_list_item(li_soup)

        self.assertEqual(album.date.year + 1, now.year)

    def test_tbd_rating_parses_to_zero(self):
        no_rating_html = """
            <li>
            <div class="product_score">{0}</div>
            <div class="product_title">{1}</div>
            <li class="release_date"><span class="data">{2}</span></li>
            <li class="product_artist"><span class="data">{3}</span></li>
            </li>
            """.format("tdb", "", "Dec 24", "")
        nr_soup = Soup(no_rating_html, "html.parser")
        album = metacritic.Album.from_list_item(nr_soup)

        self.assertEqual(album.rating, 0)

    def test_can_filter_by_date(self):
        most_recent_date = datetime.strptime("Jun 21 2017", "%b %d %Y")
        date_one_month_ago = most_recent_date - timedelta(weeks=4)

        one_month_old_albums = list(filter(
            lambda a: date_one_month_ago <= a.date <= most_recent_date,
            self.albums))

        self.assertTrue(len(one_month_old_albums) < len(self.albums))

    def test_scraper_returns_200_albums(self):
        self.assertEqual(len(self.albums), 200)

if __name__ == "__main__":
    unittest.main()
