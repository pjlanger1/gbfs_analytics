# gbfs_feed.py

# standard library
import json
import logging
import time
from datetime import datetime

# third-party packages
import requests
import schedule

# local modules
from .gbfs_timeseries import GBFSTimeSeries

METADATA_FIELDS = {
    "dc": {
        "station_status": [
            "is_installed",
            "station_id",
            "is_returning",
            "is_renting",
        ],
        "free_bike_status": [
            "vehicle_type_id",
            "rental_uris",
            "bike_id",
            "is_reserved",
            "is_disabled",
        ],
    },
    "nyc": {
        "station_status": ["is_returning", "station_id", "is_renting", "is_installed"],
        "free_bike_status": [None],
    },
    "boston": {
        "station_status": [
            "eightd_has_available_keys",
            "legacy_id",
            "is_renting",
            "is_returning",
            "is_installed",
            "station_id",
        ],
        "free_bike_status": [None],
    },
    "chicago": {
        "station_status": ["station_id", "is_returning", "is_installed", "is_renting"],
        "free_bike_status": [
            "is_disabled",
            "rental_uris",
            "is_reserved",
            "bike_id",
            "vehicle_type_id",
        ],
    },
    "sf": {
        "station_status": ["is_renting", "is_returning", "is_installed", "station_id"],
        "free_bike_status": [
            "bike_id",
            "is_reserved",
            "vehicle_type_id",
            "rental_uris",
            "is_disabled",
        ],
    },
    "portland": {
        "station_status": ["is_returning", "station_id", "is_installed", "s_renting"],
        "free_bike_status": [
            "is_disabled",
            "rental_uris",
            "vehicle_type_id",
            "bike_id",
            "is_reserved",
        ],
    },
    "denver": {
        "station_status": ["is_installed", "station_id", "is_returning", "is_renting"],
        "free_bike_status": [
            "is_reserved",
            "bike_id",
            "vehicle_type_id",
            "is_disabled",
        ],
    },
    "columbus": {
        "station_status": ["is_renting", "is_returning", "station_id", "is_installed"],
        "free_bike_status": [
            "is_reserved",
            "is_disabled",
            "rental_uris",
            "vehicle_type_id",
            "bike_id",
        ],
    },
    "la": {
        "station_status": ["is_returning", "is_renting", "is_installed", "station_id"],
        "free_bike_status": [None],
    },
    "phila": {
        "station_status": ["is_returning", "is_renting", "is_installed", "station_id"],
        "free_bike_status": [None],
    },
    "toronto": {
        "station_status": [
            "station_id",
            "is_charging_station",
            "status",
            "is_installed",
            "is_renting",
            "is_returning",
        ],
        "free_bike_status": [None],
    },
}


# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class gbfs_feed:
    def __init__(self, sysinit, baseurl):
        self.logger = logging.getLogger(__name__)
        self.system = sysinit
        self.baseurl = baseurl
        self.city = sysinit
        self.cache = {}
        self.ttls = {}
        self.scheduled_tasks = {}
        self.timeseries_store = {}
        self.stop_time = None

        try:
            self.ttl, self.vers, self.urls = self.get_feed_info()
        except Exception as e:
            self.logger.error(f"Failed to initialize GBFS feed for {sysinit}: {e}")
            self.ttl, self.vers, self.urls = None, None, {}

    def get_feed_info(self):
        """Fetch the feed information from the base URL."""
        response = self.safe_request_handler(self.baseurl, use_cache=False)
        if response is None:
            raise Exception(f"Unable to fetch feed info from {self.baseurl}")

        ttl = response.get("ttl", 0)
        version = response.get("version", "unknown")
        feeds = {
            feed["name"]: feed["url"]
            for feed in response.get("data", {}).get("en", {}).get("feeds", [])
        }
        return ttl, version, feeds

    def get_metadata_fields(self, feed):
        """Retrieve metadata fields based on city and feed."""
        return METADATA_FIELDS.get(self.city, {}).get(feed, [])

    def safe_request_handler(self, url, expect_json=True, use_cache=True):
        headers = {}
        if use_cache and url in self.cache:
            etag = self.cache[url].get("etag")
            if etag:
                headers["If-None-Match"] = etag

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            if response.status_code == 304 and use_cache:
                self.logger.info(f"Using cached data for {url}")
                return self.cache[url]["data"]

            data = response.json() if expect_json else response.content

            if use_cache:
                self.cache[url] = {"etag": response.headers.get("ETag"), "data": data}
            return data
        except requests.RequestException as e:
            self.logger.error(f"HTTP request failed: {e}")
        except json.JSONDecodeError as e:
            self.logger.error(f"Error decoding JSON: {e}")
        return None

    def perform_snapshot(self, feed, interval, iterations, save_mode=False):
        """Create a new timeseries instance and perform periodic snapshots."""
        timeseries = GBFSTimeSeries(
            feed, self.get_metadata_fields(feed)
        )  # Create new timeseries instance
        self.timeseries_store[feed] = timeseries  # Store instance in dictionary
        task_counter = [0]  # Mutable counter to track iterations

        def task():
            print(
                f"Task started for {feed}: Iteration {task_counter[0] + 1}/{iterations}"
            )  # Log the start of the task
            current_data = self.safe_request_handler(self.urls[feed])
            if current_data:
                timeseries.init_snapshot(
                    current_data
                )  # Update timeseries with new data

                # Save the snapshot if save_mode is enabled
                if save_mode:
                    last_reported = current_data.get("last_updated", time.time())
                    timestamp = (
                        datetime.utcfromtimestamp(last_reported).isoformat() + "Z"
                    )
                    with open(
                        f"{feed}_snapshot_{task_counter[0]}_{timestamp}.json", "w"
                    ) as f:
                        json.dump(current_data, f, indent=4)
                    print(
                        f"Snapshot for {feed} saved at {time.ctime()}"
                    )  # Log snapshot timing

            task_counter[0] += 1  # Increment the counter after each iteration
            if task_counter[0] >= iterations:
                print(
                    f"Maximum iterations reached for {feed}. Stopping scheduler."
                )  # Log when task is stopping
                return schedule.CancelJob  # Cancel the task after reaching the limit

        # Trigger the first task immediately
        task()
        # Schedule the periodic task to continue every 'interval' seconds
        schedule.every(interval).seconds.do(task)
        print(
            f"Task for {feed} scheduled to run every {interval} seconds."
        )  # Log that scheduling was successful

        # Graceful shutdown handling with try-except-finally
        try:
            # Start a loop to keep the scheduler running
            while task_counter[0] < iterations:
                schedule.run_pending()  # Run the scheduled jobs
                time.sleep(1)  # Sleep for a short duration to prevent high CPU usage
        except KeyboardInterrupt:
            print("Process interrupted! Cleaning up scheduled tasks...")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            schedule.clear()  # Clear all scheduled jobs
            print("Scheduler tasks cleared. Exiting gracefully.")

    def perform_delta(self, feed, interval, iterations, save_mode=False):
        """Create a new timeseries instance and calculate deltas between periodic pulls."""
        timeseries = GBFSTimeSeries(
            feed, self.get_metadata_fields(feed)
        )  # Initialize with metadata fields
        self.timeseries_store[feed] = timeseries  # Store instance in dictionary
        task_counter = [0]  # Using a list to make it mutable inside the inner function
        old_data = [
            None
        ]  # Use a list to hold old_data to avoid nonlocal declaration issues

        def task():
            if task_counter[0] >= iterations:
                return (
                    schedule.CancelJob
                )  # ends the job after the specified number of iterations
            current_data = self.safe_request_handler(self.urls[feed])
            if current_data:
                if old_data[0] is not None:
                    timeseries.init_delta(
                        old_data[0], current_data
                    )  # store delta in the timeseries object
                    delta = timeseries.calculate_delta(old_data[0], current_data)
                    # only save the delta if save_mode is True
                    if save_mode:
                        last_reported = (
                            datetime.utcfromtimestamp(
                                current_data["last_updated"]
                            ).isoformat()
                            + "Z"
                        )
                        with open(
                            f"{feed}_delta_{task_counter[0]}_{last_reported}.json", "w"
                        ) as f:
                            json.dump(delta, f, indent=4)
                        print(
                            f"Delta for {feed} saved at {time.ctime()}"
                        )  # example logging
                old_data[0] = current_data  # update old_data to the current pull
            task_counter[0] += 1

        # trigger the first task immediately
        task()

        # schedule the periodic task
        schedule.every(interval).seconds.do(task)

        try:
            # Start a loop to keep the scheduler running
            while task_counter[0] < iterations:
                schedule.run_pending()  # Run the scheduled jobs
                time.sleep(1)  # Sleep for a short duration to prevent high CPU usage
        except KeyboardInterrupt:
            print("Process interrupted! Cleaning up scheduled tasks...")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            schedule.clear()  # Clear all scheduled jobs
            print("Scheduler tasks cleared. Exiting gracefully.")
