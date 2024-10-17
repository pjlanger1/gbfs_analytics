# data_structures.py

# standard library
from enum import Enum

# third-party packages
from pydantic import BaseModel


class StationStatus(str, Enum):
    IS_INSTALLED = "is_installed"
    STATION_ID = "station_id"
    IS_RETURNING = "is_returning"
    IS_RENTING = "is_renting"
    EIGHTD_HAS_AVAILABLE_KEYS = "eightd_has_available_keys"
    LEGACY_ID = "legacy_id"
    IS_CHARGING_STATION = "is_charging_station"
    STATUS = "status"


class FreeBikeStatus(str, Enum):
    VEHICLE_TYPE_ID = "vehicle_type_id"
    RENTAL_URIS = "rental_uris"
    BIKE_ID = "bike_id"
    IS_RESERVED = "is_reserved"
    IS_DISABLED = "is_disabled"


class Station(BaseModel):
    station_status: list[StationStatus | None]
    free_bike_status: list[FreeBikeStatus | None]
