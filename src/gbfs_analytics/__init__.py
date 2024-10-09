import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Package initialized!")

__version__ = "0.1.0"

from .gbfs_manager import GBFSManager
from .gbfsfeed import GbfsFeed
from .gbfs_timeseries import GBFSTimeSeries

__all__ = ["GBFSManager", "GbfsFeed", "GBFSTimeSeries"]
