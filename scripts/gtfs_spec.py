"""GTFS static specification -- the file/column map the loader is driven by.

Why this exists as data rather than being hard-coded in the loader: GTFS is a
published standard, so the *names* here are not guesses. But real feeds vary in
which optional files and columns they actually ship. Keeping the spec separate
lets the loader intersect "what the standard allows" with "what this feed has",
and lets `sql/schema.sql` be written against the intersection rather than
against the whole standard.

Reference: https://gtfs.org/documentation/schedule/reference/

Column type hints below drive the coercions in load_gtfs.py. The three that
matter most, and the reason a naive pandas read of a GTFS feed is wrong:

  id_columns    Must stay TEXT. Feeds use ids like "01", "007", "1" -- pandas
                infers int64 and silently strips the leading zeros, after which
                the joins to stop_times/trips no longer match.

  time_columns  GTFS times may exceed 24:00:00 ("25:30:00" = 01:30 the next
                morning, still part of the previous service day). They are NOT
                clock times and no datetime parser will accept them. Stored as
                seconds-after-midnight ints.

  date_columns  YYYYMMDD integers, e.g. 20260731. Read as text then converted;
                read as int they are merely large numbers.

Deliberately not modelled: pathways.txt and levels.txt (station-interior
routing -- no BI value here) and translations.txt. If the RTA feed ships them
they are reported by --inspect and skipped by --load.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class GtfsFile:
    """One GTFS file and how to get it into MySQL correctly."""

    filename: str            # name inside the feed, e.g. "stop_times.txt"
    table: str               # destination MySQL table
    required: bool           # required by the spec (see note on calendar below)
    load_order: int          # ascending; parents before children for FK safety
    columns: tuple[str, ...] = ()        # every column the standard defines
    id_columns: tuple[str, ...] = ()     # force to str -- never let pandas infer
    time_columns: tuple[str, ...] = ()   # HH:MM:SS, may exceed 24h
    date_columns: tuple[str, ...] = ()   # YYYYMMDD
    int_columns: tuple[str, ...] = ()    # nullable ints (enums, sequences, flags)
    float_columns: tuple[str, ...] = ()  # coordinates, distances, prices
    notes: str = ""


GTFS_FILES: tuple[GtfsFile, ...] = (
    GtfsFile(
        filename="agency.txt",
        table="agency",
        required=True,
        load_order=10,
        columns=(
            "agency_id", "agency_name", "agency_url", "agency_timezone",
            "agency_lang", "agency_phone", "agency_fare_url", "agency_email",
        ),
        id_columns=("agency_id",),
        notes="agency_id is optional when a feed has exactly one agency.",
    ),
    GtfsFile(
        filename="calendar.txt",
        table="calendar",
        required=False,
        load_order=20,
        columns=(
            "service_id", "monday", "tuesday", "wednesday", "thursday",
            "friday", "saturday", "sunday", "start_date", "end_date",
        ),
        id_columns=("service_id",),
        date_columns=("start_date", "end_date"),
        int_columns=(
            "monday", "tuesday", "wednesday", "thursday",
            "friday", "saturday", "sunday",
        ),
        notes=(
            "Conditionally required: a feed must have calendar.txt or "
            "calendar_dates.txt, and may have both. Some feeds express all "
            "service through calendar_dates.txt alone."
        ),
    ),
    GtfsFile(
        filename="calendar_dates.txt",
        table="calendar_dates",
        required=False,
        load_order=30,
        columns=("service_id", "date", "exception_type"),
        id_columns=("service_id",),
        date_columns=("date",),
        int_columns=("exception_type",),
        notes="exception_type 1 = service added, 2 = service removed.",
    ),
    GtfsFile(
        filename="stops.txt",
        table="stops",
        required=True,
        load_order=40,
        columns=(
            "stop_id", "stop_code", "stop_name", "tts_stop_name", "stop_desc",
            "stop_lat", "stop_lon", "zone_id", "stop_url", "location_type",
            "parent_station", "stop_timezone", "wheelchair_boarding",
            "level_id", "platform_code",
        ),
        id_columns=("stop_id", "zone_id", "parent_station", "level_id"),
        int_columns=("location_type", "wheelchair_boarding"),
        float_columns=("stop_lat", "stop_lon"),
        notes=(
            "parent_station is a self-referencing FK: a platform points at its "
            "parent station, and both live in this one file. The loader sorts "
            "stations (location_type=1) ahead of platforms so the parent row "
            "always exists first."
        ),
    ),
    GtfsFile(
        filename="routes.txt",
        table="routes",
        required=True,
        load_order=50,
        columns=(
            "route_id", "agency_id", "route_short_name", "route_long_name",
            "route_desc", "route_type", "route_url", "route_color",
            "route_text_color", "route_sort_order", "continuous_pickup",
            "continuous_drop_off", "network_id",
        ),
        id_columns=("route_id", "agency_id", "network_id"),
        int_columns=(
            "route_type", "route_sort_order",
            "continuous_pickup", "continuous_drop_off",
        ),
        notes=(
            "route_type is the mode enum -- 0 tram, 1 metro/subway, 2 rail, "
            "3 bus, 4 ferry. This is the column the whole 'compare modes' "
            "half of the dashboard hangs off."
        ),
    ),
    GtfsFile(
        filename="shapes.txt",
        table="shapes",
        required=False,
        load_order=60,
        columns=(
            "shape_id", "shape_pt_lat", "shape_pt_lon",
            "shape_pt_sequence", "shape_dist_traveled",
        ),
        id_columns=("shape_id",),
        int_columns=("shape_pt_sequence",),
        float_columns=("shape_pt_lat", "shape_pt_lon", "shape_dist_traveled"),
        notes=(
            "Route geometry for map visuals. Large and optional -- skip with "
            "--skip shapes if it slows iteration."
        ),
    ),
    GtfsFile(
        filename="trips.txt",
        table="trips",
        required=True,
        load_order=70,
        columns=(
            "route_id", "service_id", "trip_id", "trip_headsign",
            "trip_short_name", "direction_id", "block_id", "shape_id",
            "wheelchair_accessible", "bikes_allowed",
        ),
        id_columns=(
            "route_id", "service_id", "trip_id", "block_id", "shape_id",
        ),
        int_columns=("direction_id", "wheelchair_accessible", "bikes_allowed"),
    ),
    GtfsFile(
        filename="stop_times.txt",
        table="stop_times",
        required=True,
        load_order=80,
        columns=(
            "trip_id", "arrival_time", "departure_time", "stop_id",
            "stop_sequence", "stop_headsign", "pickup_type", "drop_off_type",
            "continuous_pickup", "continuous_drop_off", "shape_dist_traveled",
            "timepoint",
        ),
        id_columns=("trip_id", "stop_id"),
        time_columns=("arrival_time", "departure_time"),
        int_columns=(
            "stop_sequence", "pickup_type", "drop_off_type",
            "continuous_pickup", "continuous_drop_off", "timepoint",
        ),
        float_columns=("shape_dist_traveled",),
        notes=(
            "The fact table, and by far the largest -- typically hundreds of "
            "thousands to millions of rows. Always loaded in chunks."
        ),
    ),
    GtfsFile(
        filename="frequencies.txt",
        table="frequencies",
        required=False,
        load_order=90,
        columns=("trip_id", "start_time", "end_time", "headway_secs", "exact_times"),
        id_columns=("trip_id",),
        time_columns=("start_time", "end_time"),
        int_columns=("headway_secs", "exact_times"),
        notes=(
            "Headway-based service. If present it MATTERS: those trips run "
            "repeatedly across a window rather than once, so counting rows in "
            "trips.txt alone undercounts actual service frequency."
        ),
    ),
    GtfsFile(
        filename="transfers.txt",
        table="transfers",
        required=False,
        load_order=100,
        columns=(
            "from_stop_id", "to_stop_id", "from_route_id", "to_route_id",
            "from_trip_id", "to_trip_id", "transfer_type", "min_transfer_time",
        ),
        id_columns=(
            "from_stop_id", "to_stop_id", "from_route_id", "to_route_id",
            "from_trip_id", "to_trip_id",
        ),
        int_columns=("transfer_type", "min_transfer_time"),
        notes="Feeds the interchange analysis.",
    ),
    GtfsFile(
        filename="fare_attributes.txt",
        table="fare_attributes",
        required=False,
        load_order=110,
        columns=(
            "fare_id", "price", "currency_type", "payment_method",
            "transfers", "agency_id", "transfer_duration",
        ),
        id_columns=("fare_id", "agency_id"),
        int_columns=("payment_method", "transfers", "transfer_duration"),
        float_columns=("price",),
    ),
    GtfsFile(
        filename="fare_rules.txt",
        table="fare_rules",
        required=False,
        load_order=120,
        columns=("fare_id", "route_id", "origin_id", "destination_id", "contains_id"),
        id_columns=("fare_id", "route_id", "origin_id", "destination_id", "contains_id"),
    ),
    GtfsFile(
        filename="feed_info.txt",
        table="feed_info",
        required=False,
        load_order=130,
        columns=(
            "feed_publisher_name", "feed_publisher_url", "feed_lang",
            "default_lang", "feed_start_date", "feed_end_date", "feed_version",
            "feed_contact_email", "feed_contact_url",
        ),
        date_columns=("feed_start_date", "feed_end_date"),
        notes=(
            "Provenance. feed_version and the publisher go straight into the "
            "README so the dashboard states which vintage of the feed it is built on."
        ),
    ),
)

# Lookups, so callers don't re-scan the tuple.
BY_FILENAME: dict[str, GtfsFile] = {f.filename: f for f in GTFS_FILES}
BY_TABLE: dict[str, GtfsFile] = {f.table: f for f in GTFS_FILES}

#: Files the loader knows about but deliberately ignores, so --inspect can
#: distinguish "unexpected" from "expected, not modelled".
IGNORED_FILES: frozenset[str] = frozenset(
    {"pathways.txt", "levels.txt", "translations.txt", "attributions.txt"}
)


def files_in_load_order() -> list[GtfsFile]:
    """Spec files ordered so a parent table is always loaded before its children."""
    return sorted(GTFS_FILES, key=lambda f: f.load_order)


def required_filenames() -> list[str]:
    """Files without which a feed is not usable."""
    return [f.filename for f in GTFS_FILES if f.required]
