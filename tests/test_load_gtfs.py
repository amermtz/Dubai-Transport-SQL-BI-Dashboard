"""Regression tests for the GTFS loader.

These run without a database. Everything covered here is a transformation that
happens before MySQL is involved -- which is exactly where GTFS data gets
silently corrupted, because none of these failures raise. Leading zeros vanish,
midnight wraps, dates become large integers: the load "succeeds" and the numbers
on the dashboard are simply wrong.

Run:  python -m pytest tests -q
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from gtfs_spec import BY_FILENAME, GTFS_FILES, files_in_load_order
from load_gtfs import (
    coerce_frame,
    fmt_secs,
    gtfs_date_to_date,
    gtfs_time_to_seconds,
    read_kwargs,
    sort_stops_parents_first,
)

# ---------------------------------------------------------------- times


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("00:00:00", 0),
        ("05:30:00", 19_800),
        ("23:59:59", 86_399),
        ("24:00:00", 86_400),      # midnight, still the same service day
        ("25:05:00", 90_300),      # 01:05 the following morning
        ("5:30:00", 19_800),       # single-digit hour is legal GTFS
        ("", None),
        ("   ", None),
        (None, None),
        (float("nan"), None),
    ],
)
def test_gtfs_time_to_seconds(raw, expected):
    assert gtfs_time_to_seconds(raw) == expected


@pytest.mark.parametrize("bad", ["12:30", "not a time", "12:30:00:00"])
def test_gtfs_time_rejects_malformed(bad):
    with pytest.raises(ValueError):
        gtfs_time_to_seconds(bad)


def test_past_midnight_does_not_wrap():
    """The failure this whole design exists to prevent.

    A trip departing 23:50 and arriving 24:20 lasts 30 minutes. Parsed as clock
    times, 24:20 becomes 00:20 and the duration comes out as minus 23.5 hours.
    """
    departure = gtfs_time_to_seconds("23:50:00")
    arrival = gtfs_time_to_seconds("24:20:00")
    assert arrival - departure == 30 * 60
    assert arrival > departure


def test_hour_of_day_derivation():
    """(secs // 3600) % 24 recovers the clock hour, including past midnight."""
    assert (gtfs_time_to_seconds("23:50:00") // 3600) % 24 == 23
    assert (gtfs_time_to_seconds("24:20:00") // 3600) % 24 == 0
    assert (gtfs_time_to_seconds("25:05:00") // 3600) % 24 == 1


def test_fmt_secs_shows_hours_beyond_24():
    assert fmt_secs(90_300) == "25:05:00"


# ---------------------------------------------------------------- dates


def test_gtfs_date_to_date():
    assert gtfs_date_to_date("20260731") == date(2026, 7, 31)


@pytest.mark.parametrize("blank", ["", "   ", None, float("nan")])
def test_gtfs_date_blank_is_none(blank):
    assert gtfs_date_to_date(blank) is None


@pytest.mark.parametrize("bad", ["2026-07-31", "202607", "abcdefgh"])
def test_gtfs_date_rejects_malformed(bad):
    with pytest.raises(ValueError):
        gtfs_date_to_date(bad)


# ---------------------------------------------------------------- coercion


def test_ids_keep_leading_zeros(feed_dir):
    """route_id '007' must not become the integer 7."""
    spec = BY_FILENAME["routes.txt"]
    with feed_dir.open("routes.txt") as handle:
        df = coerce_frame(pd.read_csv(handle, **read_kwargs(spec)), spec)

    assert df["route_id"].tolist() == ["007", "10"]


def test_coerce_frame_types(feed_dir):
    spec = BY_FILENAME["stop_times.txt"]
    with feed_dir.open("stop_times.txt") as handle:
        df = coerce_frame(pd.read_csv(handle, **read_kwargs(spec)), spec)

    # times became seconds, past-midnight preserved
    assert df["departure_time"].tolist()[-1] == 90_300
    assert str(df["departure_time"].dtype) == "Int64"

    # a blank optional int stays NA rather than becoming 0 or a float
    timepoints = df["timepoint"].tolist()
    assert pd.isna(timepoints[3])
    assert str(df["timepoint"].dtype) == "Int64"


def test_blank_optional_field_becomes_null(feed_dir):
    """An empty route_color must be NULL, never the empty string."""
    spec = BY_FILENAME["routes.txt"]
    with feed_dir.open("routes.txt") as handle:
        df = coerce_frame(pd.read_csv(handle, **read_kwargs(spec)), spec)

    assert pd.isna(df.loc[1, "route_color"])
    assert "" not in df["route_color"].dropna().tolist()


def test_dates_converted(feed_dir):
    spec = BY_FILENAME["calendar.txt"]
    with feed_dir.open("calendar.txt") as handle:
        df = coerce_frame(pd.read_csv(handle, **read_kwargs(spec)), spec)

    assert df.loc[0, "start_date"] == date(2026, 1, 1)
    assert df.loc[0, "end_date"] == date(2026, 12, 31)


def test_coerce_handles_all_blank_time_column():
    """A file where no times are given at all must not blow up on astype."""
    spec = BY_FILENAME["stop_times.txt"]
    df = pd.DataFrame({"trip_id": ["T1"], "arrival_time": [None], "departure_time": [None]})
    out = coerce_frame(df, spec)

    assert str(out["arrival_time"].dtype) == "Int64"
    assert pd.isna(out["arrival_time"].iloc[0])


# ---------------------------------------------------------------- stops ordering


def test_parent_stations_sorted_first(feed_dir):
    """The fixture lists a platform before its parent station, on purpose."""
    spec = BY_FILENAME["stops.txt"]
    with feed_dir.open("stops.txt") as handle:
        df = coerce_frame(pd.read_csv(handle, **read_kwargs(spec)), spec)

    assert df["stop_id"].tolist()[0] == "0012"       # platform first in the file
    ordered = sort_stops_parents_first(df)
    assert ordered["stop_id"].tolist()[0] == "STN1"  # station first on insert

    # every parent_station now appears at or before the row referencing it
    positions = {sid: i for i, sid in enumerate(ordered["stop_id"])}
    for i, parent in enumerate(ordered["parent_station"]):
        if not pd.isna(parent):
            assert positions[parent] < i


def test_sort_stops_without_location_type_is_a_passthrough():
    df = pd.DataFrame({"stop_id": ["a", "b"]})
    assert sort_stops_parents_first(df)["stop_id"].tolist() == ["a", "b"]


# ---------------------------------------------------------------- feed access


def test_zip_and_directory_feeds_agree(feed_dir, feed_zip):
    """A zipped feed (nested in a folder) reads identically to an extracted one."""
    assert feed_dir.member_names() == feed_zip.member_names()

    spec = BY_FILENAME["stop_times.txt"]
    frames = []
    for feed in (feed_dir, feed_zip):
        with feed.open("stop_times.txt") as handle:
            frames.append(pd.read_csv(handle, **read_kwargs(spec)))
    pd.testing.assert_frame_equal(*frames)


def test_feed_reports_missing_member(feed_zip):
    with pytest.raises(FileNotFoundError):
        with feed_zip.open("does_not_exist.txt"):
            pass


def test_bom_does_not_corrupt_first_column(tmp_path):
    """A BOM'd feed still yields a usable first column name.

    This asserts the invariant, not the mechanism: pandas' C parser strips the
    BOM on its own, so this test passes with or without the utf-8-sig setting in
    read_kwargs. Kept because the invariant is what actually matters, but it is
    not a guard on that setting -- don't read a pass here as proof of one.
    """
    from load_gtfs import Feed

    (tmp_path / "agency.txt").write_bytes(
        b"\xef\xbb\xbfagency_id,agency_name\nRTA,Test\n"
    )
    feed = Feed(tmp_path, is_zip=False)
    spec = BY_FILENAME["agency.txt"]
    with feed.open("agency.txt") as handle:
        df = pd.read_csv(handle, **read_kwargs(spec))

    assert list(df.columns)[0] == "agency_id"


# ---------------------------------------------------------------- spec integrity


def test_spec_load_order_is_unambiguous():
    orders = [f.load_order for f in GTFS_FILES]
    assert len(set(orders)) == len(orders)


def test_spec_table_and_filenames_unique():
    assert len({f.table for f in GTFS_FILES}) == len(GTFS_FILES)
    assert len({f.filename for f in GTFS_FILES}) == len(GTFS_FILES)


@pytest.mark.parametrize("spec", GTFS_FILES, ids=lambda s: s.filename)
def test_typed_columns_are_declared_columns(spec):
    """Guards against a typo in the spec silently disabling a coercion."""
    typed = (
        set(spec.id_columns)
        | set(spec.time_columns)
        | set(spec.date_columns)
        | set(spec.int_columns)
        | set(spec.float_columns)
    )
    assert typed <= set(spec.columns), f"not declared in columns: {typed - set(spec.columns)}"


@pytest.mark.parametrize("spec", GTFS_FILES, ids=lambda s: s.filename)
def test_a_column_has_one_type(spec):
    groups = [
        spec.id_columns, spec.time_columns, spec.date_columns,
        spec.int_columns, spec.float_columns,
    ]
    seen: set[str] = set()
    for group in groups:
        overlap = seen & set(group)
        assert not overlap, f"{spec.filename}: {overlap} typed twice"
        seen |= set(group)


def test_children_load_after_parents():
    """trips depends on routes and calendar; stop_times depends on trips and stops."""
    order = {f.table: i for i, f in enumerate(files_in_load_order())}
    assert order["routes"] < order["trips"] < order["stop_times"]
    assert order["agency"] < order["routes"]
    assert order["calendar"] < order["trips"]
    assert order["stops"] < order["stop_times"]
