# -*- coding: utf-8 -*-
from . import sqlitepatch

import os
import json
import scrapy
from io import BytesIO
from datetime import datetime, timedelta
from typing import Dict

from boto3.session import Session
from scrapy.exceptions import DropItem
from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess
from scrapy.item import Item


class MetacriticSpider(scrapy.Spider):
    name = 'metacritic'
    allowed_domains = ['metacritic.com']
    start_urls = ['http://www.metacritic.com/browse/albums/release-date/new-releases/date']

    def parse(self, response) -> Dict:
        products = response.css("div.product_wrap")
        for product in products:
            # generate datetime from HTML parsed Month+Day string
            date = product.css("li.release_date > span.data::text").extract_first()
            date = "{} {}".format(date, datetime.now().year)

            # 'tbd' can be used for unreleased albums so catch it
            try:
                score = int(product.css("div.metascore_w::text").extract_first())
            except ValueError:
                score = 0

            # extract album names and artist names
            artist = product.css("li.product_artist > span.data::text").extract_first()
            album = product.css("div.product_title > a::text").extract_first().strip()

            yield {
                "album": album,
                "artist": artist,
                "date": date,
                "score": score
            }


def recent_and_above_80(item, date_thresh=timedelta(weeks=1), score_thresh=80) -> bool:
    """Returns True if an album scored higher than score_thresh and is more recent than date_thresh

    Arguments:
        item {dict} -- [dictionary containing date, score, album, and artist keys]

    Keyword Arguments:
        date_thresh {[timedelta]} -- [oldest date in past to consider recent] (default: {timedelta(weeks=1)})
        score_thresh {int} -- [the lowest metascore to include] (default: {80})

    Returns:
        [bool] -- [is recent and scored highly]
    """

    thedate = datetime.strptime(item["date"], "%b %d %Y")
    if not timedelta(days=0) < (datetime.today() - thedate) < date_thresh:
        return False  # older than a week or not yet released
    if item["score"] < score_thresh:
        return False

    return True


class AlbumsPipeline(object):
    def open_spider(self, spider):
        settings = get_project_settings()
        self.bucket = Session(aws_access_key_id=settings.get("AWS_ACCESS_KEY_ID"),
                              aws_secret_access_key=settings.get("AWS_SECRET_ACCESS_KEY"),
                              region_name=os.environ["S3_BUCKET_REGION"]).resource(
                                  "s3").Bucket(
                                      os.environ["S3_BUCKET_NAME"])
        self.items = []

    def close_spider(self, spider):
        self.bucket.upload_fileobj(BytesIO(json.dumps(self.items,
                                                      indent=4,
                                                      sort_keys=True).encode()),
                                   "albums.json")

    def process_item(self, item, spider) -> Item:
        if not recent_and_above_80(item):
            raise DropItem
        self.items.append(item)
        return item
