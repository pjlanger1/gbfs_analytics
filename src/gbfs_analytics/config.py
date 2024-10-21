# config.py

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
        "station_status": ["is_returning", "station_id", "is_installed", "is_renting"],
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
