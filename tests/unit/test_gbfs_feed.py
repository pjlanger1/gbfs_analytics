# test_gbfs_feed.py

# local modules
from src.gbfs_analytics.gbfsfeed import GbfsFeed


def test_gbfs_feed_init():
    gbfs_feed = GbfsFeed(city="", baseurl="")
    assert gbfs_feed is not None
