from datetime import datetime, timedelta


def test_mocked_scraper_returns_albums(scraper):
    albums = scraper.scrape_html()
    assert len(albums) > 0


def test_correct_number_of_albums_parsed(albums):
    assert len(albums) == 200


def test_first_and_last_albums_have_correct_data(albums):
    first, last = albums[0].date, albums[-1].date
    assert first.day == 23 and first.month == 6
    assert last.day == 28 and last.month == 4


def test_filtering_by_dates_is_possible(albums):
    most_recent_date = datetime.strptime("Jun 21 2017", "%b %d %Y")
    date_one_month_ago = most_recent_date - timedelta(weeks=4)

    one_month_old_albums = list(filter(
        lambda a: date_one_month_ago <= a.date <= most_recent_date,
        albums))

    assert len(one_month_old_albums) < len(albums)


def test_year_is_decremented_if_release_month_is_in_the_past(MakeAlbum):
    now = datetime.now()
    more_than_three_months_ahead = now + timedelta(weeks=16)
    album = MakeAlbum(93, "test title",
                      more_than_three_months_ahead.strftime("%b %d"),
                      "test artist")

    assert album.date.year + 1 == now.year


def test_tbd_date_parses_to_zero(MakeAlbum):
    album = MakeAlbum("tbd", "fake title", "Dec 24", "fake artist")
    assert album.rating == 0
