# gbfs_manager.py

# standard library
from datetime import datetime, timezone
from json import dumps
from logging import Logger

# local modules
from .utils import get_logger


class GBFSTimeSeries:
    def __init__(
        self, feed_name: str, metadata_fields: list, logger: Logger | None = None
    ) -> None:
        """
        Initialize with feed_name and a metadata dictionary for field tagging.

        Args:
            feed_name:
            metadata_fields:
        """
        if logger is None:
            self.logger = get_logger()
        self.feed_name = feed_name
        self.metadata_fields = metadata_fields  # List of full paths to metadata fields
        self.data = {}  # Station/bike data, with metadata history and time series

    @staticmethod
    def get_nested_field(data_dict: dict, field_path: str):
        """
        Retrieve the value from a nested dictionary using the full field path.

        Args:
            data_dict:
            field_path:

        Returns:

        """
        # Split the path by '.'
        keys = field_path.split(".")
        for key in keys:
            if isinstance(data_dict, dict):
                data_dict = data_dict.get(key)
            else:
                # Return None if any part of the path is missing
                return None
        return data_dict

    def is_metadata_field(self, field_name: str) -> bool:
        """
        Determine if a field is a metadata field based on the feed_name.

        Args:
            field_name:

        Returns:

        """
        return field_name in self.metadata_fields

    def extract_metadata(self, data_item: dict) -> dict:
        """
        Extract metadata from a given data item based on the metadata fields.

        Args:
            data_item:

        Returns:

        """
        metadata = {}
        for field_path in self.metadata_fields:
            value = self.get_nested_field(data_dict=data_item, field_path=field_path)
            if value is not None:
                metadata[field_path] = value
            else:
                # Add logging to help identify missing fields
                self.logger.warning(
                    f"Warning: Field {field_path} not found in the data item."
                )
        return metadata

    def init_snapshot(self, feed_data: dict) -> None:
        """
        Initialize snapshot for the relevant feed (station_status or free_bike_status).

        Args:
            feed_data:

        Returns:

        """
        if self.feed_name == "station_status":
            self.restructure_station_status(station_status=feed_data)
        elif self.feed_name == "free_bike_status":
            self.restructure_free_bike_status(free_bike_status=feed_data)

    def restructure_station_status(self, station_status: dict) -> None:
        """
        Restructure station status and log dynamic changes.

        Args:
            station_status:

        Returns:

        """
        for station in station_status.get("data", {}).get("stations", []):
            station_id = self.get_nested_field(
                data_dict=station, field_path="station_id"
            )
            last_reported = (
                self.get_nested_field(data_dict=station, field_path="last_reported")
                or datetime.now(timezone.utc).timestamp()
            )

            if station_id not in self.data:
                self.data[station_id] = {"metadata_history": [], "time_series": []}

            # Extract metadata based on the predefined metadata fields
            metadata = self.extract_metadata(data_item=station)
            if not metadata:
                self.logger.warning(
                    f"Warning: Metadata is empty for station_id {station_id}"
                )

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
                        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                        "version": new_version,
                        "metadata": metadata,
                    }
                )
            else:
                new_version = len(self.data[station_id]["metadata_history"])

            # Log dynamic (time-series) data with 'last_reported' as the timestamp
            self.data[station_id]["time_series"].append(
                {
                    "timestamp": datetime.fromtimestamp(
                        last_reported, tz=timezone.utc
                    ).isoformat()
                    + "Z",
                    "metadata_version": new_version,
                    "data": dynamic_data,
                }
            )

    def restructure_free_bike_status(self, free_bike_status: dict) -> None:
        """
        Restructure free bike status and log metadata changes if necessary.

        Args:
            free_bike_status:

        Returns:

        """
        # Use the top-level last_updated field for the timestamp
        last_updated = free_bike_status.get(
            "last_updated", datetime.now(timezone.utc).timestamp()
        )

        for bike in free_bike_status.get("data", {}).get("bikes", []):
            bike_id = self.get_nested_field(data_dict=bike, field_path="bike_id")
            if bike_id not in self.data:
                self.data[bike_id] = {"metadata_history": [], "time_series": []}

            # Extract metadata based on the predefined metadata fields
            metadata = self.extract_metadata(data_item=bike)
            if not metadata:
                self.logger.warning(f"Warning: Metadata is empty for bike_id {bike_id}")

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

    def init_delta(self, old_data: dict, new_data: dict) -> None:
        """
        Calculate and store the delta between two data points for station_status or
        free_bike_status.

        Args:
            old_data:
            new_data:

        Returns:

        """
        delta_data = self.calculate_delta(old_data=old_data, new_data=new_data)
        current_time = datetime.now(timezone.utc).isoformat() + "Z"

        # Add delta to the time series
        for station_or_bike_id, changes in delta_data.items():
            self.data.setdefault(
                station_or_bike_id, {"metadata_history": [], "time_series": []}
            )
            self.data[station_or_bike_id]["time_series"].append(
                {"timestamp": current_time, "data": changes}
            )

    def calculate_delta(self, old_data: dict, new_data: dict) -> dict:
        """
        Calculate delta between two data points.

        Args:
            old_data:
            new_data:

        Returns:

        """
        delta = {}
        for station_or_bike in new_data.get("data", {}).get(
            "stations", []
        ) or new_data.get("data", {}).get("bikes", []):
            item_id = self.get_nested_field(
                data_dict=station_or_bike, field_path="station_id"
            ) or self.get_nested_field(data_dict=station_or_bike, field_path="bike_id")
            old_station_or_bike = next(
                (
                    x
                    for x in (
                        old_data.get("data", {}).get("stations", [])
                        or old_data.get("data", {}).get("bikes", [])
                    )
                    if self.get_nested_field(data_dict=x, field_path="station_id")
                    == item_id
                    or self.get_nested_field(data_dict=x, field_path="bike_id")
                    == item_id
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
                # New station or bike
                delta[item_id] = station_or_bike
        return delta

    def display(self) -> None:
        """
        Utility to display the current state of time series data.

        Returns:

        """
        self.logger.info(dumps(obj=self.data, indent=4))
