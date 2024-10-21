# gbfs_feed.py

# standard library
from datetime import datetime, timezone
from json import dump, JSONDecodeError
from logging import Logger
from time import sleep, time, ctime
from typing import Type

# third-party packages
import requests
from schedule import clear, every, run_pending, CancelJob
from pydantic import TypeAdapter

# local modules
from .config import METADATA_FIELDS
from .data_structures import Station
from .gbfs_timeseries import GBFSTimeSeries
from .utils import get_logger


class GbfsFeed:
    def __init__(
        self, city: str, baseurl: str, logger: Logger | None = None
    ) -> None:
        if logger is None:
            self.logger = get_logger()
        self.baseurl = baseurl
        self.city = city
        self.cache = {}
        self.ttls = {}
        self.scheduled_tasks = {}
        self.timeseries_store = {}
        self.stop_time = None
        type_adapter = TypeAdapter(Station)
        stations = {
            city: type_adapter.validate_python(metadata).model_dump()
            for city, metadata in METADATA_FIELDS.items()
        }
        self.metadata_fields = stations.get(city)

        try:
            self.ttl, self.vers, self.urls = self.get_feed_info()
        except Exception as e:
            self.logger.error(f"Failed to initialize GBFS feed for {city}: {e}")
            self.ttl, self.vers, self.urls = None, None, {}

    def get_feed_info(self) -> tuple[int, str, dict]:
        """
        Fetch the feed information from the base URL.

        Returns:

        """
        response = self.safe_request_handler(url=self.baseurl, use_cache=False)
        if response is None:
            raise Exception(f"Unable to fetch feed info from {self.baseurl}")

        ttl = response.get("ttl", 0)
        version = response.get("version", "unknown")
        feeds = {
            feed["name"]: feed["url"]
            for feed in response.get("data", {}).get("en", {}).get("feeds", [])
        }
        return ttl, version, feeds

    def get_metadata_fields(self, feed: str) -> list[str]:
        """
        Retrieve metadata fields based on city and feed.

        Args:
            feed:

        Returns:

        """
        return self.metadata_fields.get(feed, [])

    def safe_request_handler(
        self, url: str, expect_json: bool = True, use_cache: bool = True
    ) -> dict | None:
        """
        TODO - add description

        Args:
            url:
            expect_json:
            use_cache:

        Returns:

        """
        headers = {}
        if use_cache and url in self.cache:
            etag = self.cache[url].get("etag")
            if etag:
                headers["If-None-Match"] = etag

        try:
            response = requests.get(url=url, headers=headers)
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
        except JSONDecodeError as e:
            self.logger.error(f"Error decoding JSON: {e}")
        return None

    def perform_snapshot(
        self, feed: str, interval: int, iterations: int, save_mode: bool = False
    ) -> None:
        """
        Create a new timeseries instance and perform periodic snapshots.

        Args:
            feed:
            interval:
            iterations:
            save_mode:

        Returns:

        """
        # Create new timeseries instance
        timeseries = GBFSTimeSeries(
            feed_name=feed, metadata_fields=self.get_metadata_fields(feed)
        )
        # Store instance in dictionary
        self.timeseries_store[feed] = timeseries
        task_counter = 0

        def task() -> type[CancelJob] | None:
            # Set variables as non-local
            nonlocal task_counter

            # Log the start of the task
            self.logger.info(
                f"Task started for {feed}: Iteration {task_counter + 1}/{iterations}"
            )
            current_data = self.safe_request_handler(url=self.urls[feed])
            if current_data:
                # Update timeseries with new data
                timeseries.init_snapshot(feed_data=current_data)

                # Save the snapshot if save_mode is enabled
                if save_mode:
                    last_reported = current_data.get("last_updated", time())
                    last_reported = (
                        datetime.fromtimestamp(
                            last_reported, tz=timezone.utc
                        ).isoformat()
                        + "Z"
                    )
                    with open(
                        f"{feed}_snapshot_{task_counter}_{last_reported}.json", "w"
                    ) as f:
                        dump(obj=current_data, fp=f, indent=4)
                    # Log snapshot timing
                    self.logger.info(f"Snapshot for {feed} saved at {ctime()}")

            # Increment the counter after each iteration
            task_counter += 1
            if task_counter >= iterations:
                # Log when task is stopping
                self.logger.info(
                    f"Maximum iterations reached for {feed}. Stopping scheduler."
                )
                # Cancel the task after reaching the limit
                return CancelJob

        # Trigger the first task immediately
        task()
        # Schedule the periodic task to continue every 'interval' seconds
        every(interval=interval).seconds.do(job_func=task)
        # Log that scheduling was successful
        self.logger.info(f"Task for {feed} scheduled to run every {interval} seconds.")

        # Graceful shutdown handling with try-except-finally
        try:
            # Start a loop to keep the scheduler running
            while task_counter < iterations:
                # Run the scheduled jobs
                run_pending()
                # Sleep for a short duration to prevent high CPU usage
                sleep(1)
        except KeyboardInterrupt:
            self.logger.error("Process interrupted! Cleaning up scheduled tasks...")
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")
        finally:
            # Clear all scheduled jobs
            clear()
            self.logger.info("Scheduler tasks cleared. Exiting gracefully.")

    def perform_delta(
        self, feed: str, interval: int, iterations: int, save_mode: bool = False
    ) -> None:
        """
        Create a new timeseries instance and calculate deltas between periodic pulls.

        Args:
            feed:
            interval:
            iterations:
            save_mode:

        Returns:

        """
        # Initialize with metadata fields
        timeseries = GBFSTimeSeries(
            feed_name=feed, metadata_fields=self.get_metadata_fields(feed=feed)
        )
        # Store instance in dictionary
        self.timeseries_store[feed] = timeseries
        task_counter = 0
        old_data = {}

        def task() -> Type[CancelJob]:
            # Set variables as non-local
            nonlocal task_counter, old_data

            # Ends the job after the specified number of iterations
            if task_counter >= iterations:
                return CancelJob

            current_data = self.safe_request_handler(url=self.urls[feed])
            if current_data:
                if old_data:
                    # store delta in the timeseries object
                    timeseries.init_delta(old_data=old_data, new_data=current_data)
                    # only save the delta if save_mode is True
                    delta = timeseries.calculate_delta(
                        old_data=old_data, new_data=current_data
                    )

                    if save_mode:
                        last_reported = (
                            datetime.fromtimestamp(
                                current_data["last_updated"], tz=timezone.utc
                            ).isoformat()
                            + "Z"
                        )
                        with open(
                            f"{feed}_delta_{task_counter}_{last_reported}.json", "w"
                        ) as f:
                            dump(obj=delta, fp=f, indent=4)
                        # example logging
                        self.logger.info(f"Delta for {feed} saved at {ctime()}")
                # update old_data to the current pull
                old_data = current_data
            task_counter += 1

        # trigger the first task immediately
        task()

        # schedule the periodic task
        every(interval=interval).seconds.do(job_func=task)

        try:
            # Start a loop to keep the scheduler running
            while task_counter < iterations:
                # Run the scheduled jobs
                run_pending()
                # Sleep for a short duration to prevent high CPU usage
                sleep(1)
        except KeyboardInterrupt:
            self.logger.error("Process interrupted! Cleaning up scheduled tasks...")
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")
        finally:
            # Clear all scheduled jobs
            clear()
            self.logger.info("Scheduler tasks cleared. Exiting gracefully.")
