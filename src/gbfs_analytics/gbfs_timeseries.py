# gbfs_manager.py

# standard library
import json
from datetime import datetime


class GBFSTimeSeries:
    def __init__(self, feed_name, metadata_fields):
        """Initialize with feed_name and a metadata dictionary for field tagging."""
        self.feed_name = feed_name
        self.metadata_fields = metadata_fields  # List of full paths to metadata fields
        self.data = (
            {}
        )  # Store station/bike data, including metadata history and time series

    def get_nested_field(self, data_dict, field_path):
        """Retrieve the value from a nested dictionary using the full field path."""
        keys = field_path.split(".")  # Split the path by '.'
        for key in keys:
            if isinstance(data_dict, dict):
                data_dict = data_dict.get(key)
            else:
                return None  # Return None if any part of the path is missing
        return data_dict

    def is_metadata_field(self, field_name):
        """Determine if a field is a metadata field based on the feed_name."""
        return field_name in self.metadata_fields

    def extract_metadata(self, data_item):
        """Extract metadata from a given data item based on the metadata fields."""
        metadata = {}
        for field_path in self.metadata_fields:
            value = self.get_nested_field(data_item, field_path)
            if value is not None:
                metadata[field_path] = value
            else:
                print(
                    f"Warning: Field {field_path} not found in the data item."
                )  # Add logging to help identify missing fields
        return metadata

    def init_snapshot(self, feed_data):
        """Initialize snapshot for the relevant feed (station_status or free_bike_status)."""
        if self.feed_name == "station_status":
            self.restructure_station_status(feed_data)
        elif self.feed_name == "free_bike_status":
            self.restructure_free_bike_status(feed_data)

    def restructure_station_status(self, station_status):
        """Restructure station status and log dynamic changes."""
        for station in station_status.get("data", {}).get("stations", []):
            station_id = self.get_nested_field(station, "station_id")
            last_reported = (
                self.get_nested_field(station, "last_reported")
                or datetime.utcnow().timestamp()
            )

            if station_id not in self.data:
                self.data[station_id] = {"metadata_history": [], "time_series": []}

            # Extract metadata based on the predefined metadata fields
            metadata = self.extract_metadata(station)
            if not metadata:
                print(f"Warning: Metadata is empty for station_id {station_id}")

            dynamic_data = {
                key: value for key, value in station.items() if key not in metadata
            }

            # Check and update metadata if needed
            latest_metadata = (
                self.data[station_id]["metadata_history"][-1]["metadata"]
                if self.data[station_id]["metadata_history"]
                else None
            )
            if latest_metadata != metadata:
                new_version = len(self.data[station_id]["metadata_history"]) + 1
                self.data[station_id]["metadata_history"].append(
                    {
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "version": new_version,
                        "metadata": metadata,
                    }
                )
            else:
                new_version = len(self.data[station_id]["metadata_history"])

            # Log dynamic (time-series) data with 'last_reported' as the timestamp
            self.data[station_id]["time_series"].append(
                {
                    "timestamp": datetime.utcfromtimestamp(last_reported).isoformat()
                    + "Z",
                    "metadata_version": new_version,
                    "data": dynamic_data,
                }
            )

    def restructure_free_bike_status(self, free_bike_status):
        """Restructure free bike status and log metadata changes if necessary."""
        # Use the top-level last_updated field for the timestamp
        last_updated = free_bike_status.get(
            "last_updated", datetime.utcnow().timestamp()
        )

        for bike in free_bike_status.get("data", {}).get("bikes", []):
            bike_id = self.get_nested_field(bike, "bike_id")
            if bike_id not in self.data:
                self.data[bike_id] = {"metadata_history": [], "time_series": []}

            # Extract metadata based on the predefined metadata fields
            metadata = self.extract_metadata(bike)
            if not metadata:
                print(f"Warning: Metadata is empty for bike_id {bike_id}")

            dynamic_data = {
                key: value for key, value in bike.items() if key not in metadata
            }

            # Check and update metadata if necessary
            latest_metadata = (
                self.data[bike_id]["metadata_history"][-1]["metadata"]
                if self.data[bike_id]["metadata_history"]
                else None
            )
            if latest_metadata != metadata:
                new_version = len(self.data[bike_id]["metadata_history"]) + 1
                self.data[bike_id]["metadata_history"].append(
                    {
                        "timestamp": last_updated,
                        "version": new_version,
                        "metadata": metadata,
                    }
                )
            else:
                new_version = len(self.data[bike_id]["metadata_history"])

            # Log dynamic (time-series) data with 'last_updated' from feed level
            self.data[bike_id]["time_series"].append(
                {
                    "timestamp": last_updated,
                    "metadata_version": new_version,
                    "data": dynamic_data,
                }
            )

    def init_delta(self, old_data, new_data):
        """
        Calculate and store the delta between two data points for station_status or
        free_bike_status.
        """
        delta_data = self.calculate_delta(old_data, new_data)
        current_time = datetime.utcnow().isoformat() + "Z"

        # Add delta to the time series
        for station_or_bike_id, changes in delta_data.items():
            self.data.setdefault(
                station_or_bike_id, {"metadata_history": [], "time_series": []}
            )
            self.data[station_or_bike_id]["time_series"].append(
                {"timestamp": current_time, "data": changes}
            )

    def calculate_delta(self, old_data, new_data):
        """Calculate delta between two data points."""
        delta = {}
        for station_or_bike in new_data.get("data", {}).get(
            "stations", []
        ) or new_data.get("data", {}).get("bikes", []):
            item_id = self.get_nested_field(
                station_or_bike, "station_id"
            ) or self.get_nested_field(station_or_bike, "bike_id")
            old_station_or_bike = next(
                (
                    x
                    for x in (
                        old_data.get("data", {}).get("stations", [])
                        or old_data.get("data", {}).get("bikes", [])
                    )
                    if self.get_nested_field(x, "station_id") == item_id
                    or self.get_nested_field(x, "bike_id") == item_id
                ),
                None,
            )
            if old_station_or_bike:
                delta[item_id] = {
                    key: station_or_bike[key]
                    for key in station_or_bike
                    if key not in old_station_or_bike
                    or station_or_bike[key] != old_station_or_bike[key]
                }
            else:
                delta[item_id] = station_or_bike  # New station or bike
        return delta

    def display(self):
        """Utility to display the current state of time series data."""
        print(json.dumps(self.data, indent=4))
