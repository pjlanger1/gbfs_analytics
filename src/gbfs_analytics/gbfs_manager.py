# gbfs_manager.py

# local modules
from .gbfsfeed import GbfsFeed


class GBFSManager:
    def __init__(self):
        # available systems and their base URLs
        self.systems = {
            "dc": "https://gbfs.capitalbikeshare.com/gbfs/2.3/gbfs.json",
            "nyc": "https://gbfs.lyft.com/gbfs/2.3/bkn/gbfs.json",
            "boston": "https://gbfs.bluebikes.com/gbfs/gbfs.json",
            "chicago": "https://gbfs.divvybikes.com/gbfs/2.3/gbfs.json",
            "sf": "https://gbfs.baywheels.com/gbfs/2.3/gbfs.json",
            "portland": "https://gbfs.biketownpdx.com/gbfs/2.3/gbfs.json",
            "denver": "https://gbfs.lyft.com/gbfs/2.3/den/gbfs.json",
            "columbus": "https://gbfs.lyft.com/gbfs/2.3/cmh/gbfs.json",
            "la": "https://gbfs.bcycle.com/bcycle_lametro/gbfs.json",
            "phila": "https://gbfs.bcycle.com/bcycle_indego/gbfs.json",
            "toronto": "https://tor.publicbikesystem.net/customer/gbfs/v2/gbfs.json",
            "cdmx":"https://gbfs.mex.lyftbikes.com/gbfs/gbfs.json"
        }

    def get_feed(self, city: str) -> GbfsFeed:
        """
        Return a gbfs_feed instance for the given city if available.

        Args:
            city:

        Returns:

        """
        if city not in self.systems:
            raise ValueError(f"City {city} is not available in the systems list.")
        return GbfsFeed(city=city, baseurl=self.systems[city])

    def list_available_systems(self) -> list:
        """
        Return a list of available systems.

        Returns:

        """
        return list(self.systems.keys())
