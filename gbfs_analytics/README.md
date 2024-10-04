# gbfs_analytics

**gbfs_analytics** is an open-source Python package created to improve public access to and understanding of bikeshare system data. This package allows researchers, developers, and policymakers to efficiently work with bikeshare data through the GBFS (General Bikeshare Feed Specification) framework.

this is a beta version, meaning, we're still finding bugs sometimes, so use at your own risk and please let us know if you encounter any issues or questions.

## Background and Acknowledgements

### Background

GBFS, or General Bikeshare Feed Specification, is a real-time or near real-time specification for public data, primarily intended to provide transit advice through consumer-facing applications. The specification is currently on version 3, but many systems, including Lyft's, are still using version 2.3, which is the version supported by gbfs_analytics.

For more information, see the full GBFS documentation [here](https://github.com/MobilityData/gbfs).

There have been several attempts in the past to create software to programmatically access GBFS feeds, including the now-deprecated gbfs-client package on PyPI. Writing software in this space often stems from passion, and I would like to thank those who contributed before me.

With the rise of micromobility, especially bikeshare programs, access to accurate and real-time data is essential for everyone from policymakers to urban planners and citizens. This package is designed to provide that access and help people understand bikeshare system data.

## Summary

`gbfs_analytics` provides a client framework for accessing real-time bikeshare system data efficiently using a polling mechanism. It is tailored for research use cases and allows the data to be stored and processed in a structured format.

### Core Components

The package has three core modules:

1. **`gbfs_feed` class**: 
    - The main class that interfaces with GBFS feeds and allows users to perform experiments (like polling for data or calculating deltas) using the `compose()` method.
    - It manages data retrieval and caching, and works seamlessly with time-series data.

2. **`GBFSTimeSeries` class**: 
    - This class is responsible for storing and processing time-series data. It is automatically instantiated by the `gbfs_feed` class as part of the feed’s `compose()` method.
    - It structures data into two levels: **metadata** (which changes infrequently and is stored only when necessary) and **data** (which changes frequently and is stored at every update). This structure optimizes memory usage and data retrieval.

3. **Scheduler class** (coming in version 1.0):
    - A flexible scheduler for more advanced, automated polling and scheduling features. This will allow users to configure polling jobs and run them in a non-blocking manner over long periods.

## Time-Series Data and Metadata

One of the core concepts of this package is the separation of data into **metadata** and **data**.

- **Data**: These are fast-changing values, like the number of available bikes or scooters, station occupancy, bike location (latitude and longitude), etc.
- **Metadata**: These are slow-changing fields that do not update frequently, such as whether a station is installed, the bike type, or whether a station allows rentals.

### Example: Station Status Data Structure

Here’s an example from Washington DC’s `station_status.json` for a single station:

```json
{
  "47ea64ba-00cd-4762-a90c-240244d1e4c8": {
    "1727381803.397485": {
      "num_bikes_disabled": 0,
      "num_ebikes_available": 4,
      "num_docks_disabled": 0,
      "num_scooters_unavailable": 0,
      "num_bikes_available": 6,
      "is_renting": 1,
      "is_installed": 1,
      "num_docks_available": 9,
      "num_scooters_available": 0,
      "station_id": "47ea64ba-00cd-4762-a90c-240244d1e4c8",
      "is_returning": 1,
      "vehicle_types_available": [
        {"count": 2, "vehicle_type_id": "1"},
        {"count": 4, "vehicle_type_id": "2"}
      ],
      "last_reported": 1727381748
    }
  }
}
```

In this example, the first key ("47ea64ba-00cd-4762-a90c-240244d1e4c8") is the station ID. The next key ("1727381803.397485") is a timestamp.

Data fields: num_bikes_disabled, num_bikes_available, num_ebikes_available, num_docks_disabled, num_docks_available, num_scooters_available, and vehicle_types_available.
Metadata fields: is_renting, is_installed, is_returning, and station_id.

### Example: Free Bike Status Data Structure
Here's an example from the 'free_bike_status.json' feed:

```json
{
  "1c0d9eb374a1f257b2606a60936e092e": {
    "1727381757": {
      "lon": -76.947063923,
      "lat": 38.890841484,
      "is_reserved": 0,
      "vehicle_type_id": "2",
      "current_range_meters": 12231.0144,
      "is_disabled": 0,
      "rental_uris": {
        "android": "https://dc.lft.to/lastmile_qr_scan",
        "ios": "https://dc.lft.to/lastmile_qr_scan"
      },
      "bike_id": "1c0d9eb374a1f257b2606a60936e092e"
    },
    "1727381877": {
      "lon": -76.947050571,
      "lat": 38.890845299,
      "is_reserved": 0,
      "vehicle_type_id": "2",
      "current_range_meters": 12231.0144,
      "is_disabled": 0,
      "rental_uris": {
        "android": "https://dc.lft.to/lastmile_qr_scan",
        "ios": "https://dc.lft.to/lastmile_qr_scan"
      },
      "bike_id": "1c0d9eb374a1f257b2606a60936e092e"
    }
  }
}
``` 
In this case:

The key "1c0d9eb374a1f257b2606a60936e092e" is the bike ID.
The dynamic fields (data) are lon, lat, and current_range_meters.
The static metadata would be fields like is_reserved, vehicle_type_id, rental_uris, and bike_id.

### Conceptual Difference Between Data and Metadata
The distinction between data and metadata may vary based on the feed type, city, and provider. In this first beta version, only Lyft-based GBFS systems using version 2.3 of the GBFS standard are supported. Even within the same version, field availability may vary by city.

### Installation
You can install the package using pip:

```bash
pip install gbfs_analytics
```
### Usage
Initialize the GBFS Manager

```python
from gbfs_analytics import GBFSManager

# Create a manager instance
manager = GBFSManager()

# List available systems
systems = manager.list_available_systems()
print(systems)

# Get a feed for a specific city (e.g., Washington DC)
dc_feed = manager.get_feed('dc')

# Perform a snapshot for station status data
#Perform snapshot allows you to select:
# a) an interval -> snapshot every x seconds.
# b) a # of iterations -> repeat the above y times.
# c) save_mode will save the raw snapshots of the feed to your working directory.
# d) and most importantly feed [station_status, free_bike_status]

dc_feed.perform_snapshot(feed='station_status', interval=600, iterations=6, save_mode = True)
```

## Coverage
We currently support 11 cities in North America
_______________________________________________
Washington, DC ('dc'), 
New York City ('nyc'),
Boston ('boston'),
Chicago ('chicago'),
San Francisco ('sf'),
Portland ('portland'),
Denver ('denver'),
Columbus ('columbus'),
Los Angeles ('la'),
Philadelphia ('phila')
Toronto ('tor')

DC, Chicago, SF, Portland, Denver, Columbus all offer 'free_bike_status' as well as 'station_status' feeds.
The remaining systems only offer 'station_status' feeds.

## Questions? Open a github PR or email us, we'll get back to you asap