"""GTFS feed -> MySQL loader.

Two modes:

    python scripts/load_gtfs.py --inspect
        Reads the feed and reports what is actually in it: which spec files are
        present, row counts, which spec columns the feed omits, which columns it
        adds beyond the spec, the service date range, and whether stop_times
        contains past-midnight times. Touches the database not at all.

    python scripts/load_gtfs.py --load
        Loads into the tables defined by sql/schema.sql, parents first.

Run --inspect FIRST. sql/schema.sql is written against its output, not against
the standard in the abstract: GTFS defines many optional columns and a given
feed ships some arbitrary subset. Building the schema off the real column list
is the difference between a model of this feed and a model of the spec.

The loader will not create tables. Letting pandas' to_sql infer them produces
all-TEXT columns with no keys, no constraints and no indexes -- which would
quietly discard the normalisation and ER modelling this project exists to
demonstrate. If a table is missing it says so and stops.

Usage:
    python scripts/load_gtfs.py --inspect
    python scripts/load_gtfs.py --inspect --feed data/raw/dubai-rta-gtfs.zip
    python scripts/load_gtfs.py --load --truncate
    python scripts/load_gtfs.py --load --only stops,routes,trips
    python scripts/load_gtfs.py --load --skip shapes
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import IO, Iterator

import pandas as pd
from sqlalchemy import inspect as sa_inspect, text
from sqlalchemy.engine import Engine

# scripts/ is not a package; running this file puts its directory on sys.path,
# but adding it explicitly keeps `python -m scripts.load_gtfs` working too.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from db import get_engine  # noqa: E402
from gtfs_spec import (  # noqa: E402
    BY_FILENAME,
    IGNORED_FILES,
    GtfsFile,
    files_in_load_order,
    required_filenames,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"

#: Rows per INSERT batch. Kept modest deliberately: to_sql(method="multi")
#: builds one multi-row INSERT per chunk, and a large chunk can exceed MySQL's
#: max_allowed_packet (4 MB by default on 8.0) -- which surfaces as an opaque
#: "Lost connection to MySQL server during query" rather than a size error.
DEFAULT_CHUNKSIZE = 5_000

#: Rows per read from the CSV. Independent of the insert batch size; this one
#: bounds memory, since stop_times.txt does not comfortably fit for large feeds.
READ_CHUNKSIZE = 200_000


# --------------------------------------------------------------------------
# Value coercions
# --------------------------------------------------------------------------

def gtfs_time_to_seconds(value: object) -> int | None:
    """'25:30:00' -> 91800. Seconds after midnight of the *service* day.

    GTFS times are not clock times. A trip departing 23:50 and arriving 00:20
    the next morning is written 23:50:00 -> 24:20:00, staying on one service
    day rather than wrapping to a smaller number. Anything that parses these as
    time-of-day either errors on hour 24+ or wraps them, and wrapping silently
    turns a 30-minute trip into a negative duration.

    Storing seconds keeps the arithmetic honest and makes the derivations the
    dashboard needs trivial:
        hour of day    = (secs // 3600) % 24
        trip duration  = arrival_secs - departure_secs   (never negative)

    Returns None for blank values, which are legal: stop_times may omit times
    at non-timepoint stops.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    raw = str(value).strip()
    if not raw:
        return None

    parts = raw.split(":")
    if len(parts) != 3:
        raise ValueError(f"Malformed GTFS time {raw!r} (expected H:MM:SS)")
    hours, minutes, seconds = (int(p) for p in parts)  # H may be 1 or 2 digits
    return hours * 3600 + minutes * 60 + seconds


def gtfs_date_to_date(value: object) -> date | None:
    """'20260731' -> date(2026, 7, 31)."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    raw = str(value).strip()
    if not raw:
        return None
    if len(raw) != 8 or not raw.isdigit():
        raise ValueError(f"Malformed GTFS date {raw!r} (expected YYYYMMDD)")
    return date(int(raw[:4]), int(raw[4:6]), int(raw[6:8]))


def coerce_frame(df: pd.DataFrame, spec: GtfsFile) -> pd.DataFrame:
    """Apply the spec's type rules to a chunk, in place of pandas' inference."""
    for column in spec.time_columns:
        if column in df.columns:
            df[column] = df[column].map(gtfs_time_to_seconds).astype("Int64")

    for column in spec.date_columns:
        if column in df.columns:
            df[column] = df[column].map(gtfs_date_to_date)

    for column in spec.int_columns:
        if column in df.columns:
            # Int64 (capital I) is pandas' nullable integer. Plain int64 cannot
            # hold NA, so a single blank optional field would coerce the whole
            # column to float and write 1.0 into an enum column.
            df[column] = pd.to_numeric(df[column], errors="coerce").astype("Int64")

    for column in spec.float_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

    # Empty strings in text columns are not the same as NULL to MySQL, and GTFS
    # uses blank to mean absent throughout. read_kwargs already maps "" to NA on
    # read; this is the backstop for any column that arrives some other way.
    #
    # The dtype test must not be `== object`: pandas 3.0 made `str` the default
    # dtype for text, so an object-only check silently stops matching anything.
    for column in df.columns:
        if df[column].dtype == object or pd.api.types.is_string_dtype(df[column]):
            df[column] = df[column].replace("", None)

    return df


def read_kwargs(spec: GtfsFile) -> dict:
    """pandas.read_csv arguments that stop it from corrupting the feed."""
    return {
        # Feeds produced on Windows often carry a UTF-8 BOM. pandas' C parser
        # happens to strip it even under plain "utf-8", so this is explicit
        # insurance rather than the only thing standing between us and a first
        # column named "﻿stop_id" -- it still matters for the python engine,
        # and for anything else that later reads these files directly.
        "encoding": "utf-8-sig",
        # Every id stays text. See gtfs_spec for why.
        "dtype": {column: "string" for column in spec.id_columns},
        # Times and dates are parsed by coerce_frame, not by pandas.
        "keep_default_na": True,
        "na_values": [""],
        "skipinitialspace": True,
    }


# --------------------------------------------------------------------------
# Feed access -- a feed is either a .zip or an already-extracted directory
# --------------------------------------------------------------------------

@dataclass
class Feed:
    """A GTFS feed, zipped or extracted, with uniform access to its members."""

    path: Path
    is_zip: bool

    @property
    def label(self) -> str:
        return f"{self.path.name}{' (zip)' if self.is_zip else '/'}"

    def member_names(self) -> list[str]:
        """Every .txt file in the feed, without directory prefixes."""
        if self.is_zip:
            with zipfile.ZipFile(self.path) as archive:
                return sorted(
                    Path(name).name
                    for name in archive.namelist()
                    if name.lower().endswith(".txt") and not name.endswith("/")
                )
        return sorted(p.name for p in self.path.glob("*.txt"))

    def has(self, filename: str) -> bool:
        return filename in self.member_names()

    @contextmanager
    def open(self, filename: str) -> Iterator[IO[bytes]]:
        """Binary handle to one member. Handles feeds zipped with a top folder."""
        if self.is_zip:
            with zipfile.ZipFile(self.path) as archive:
                match = next(
                    (n for n in archive.namelist() if Path(n).name == filename),
                    None,
                )
                if match is None:
                    raise FileNotFoundError(f"{filename} not in {self.path}")
                with archive.open(match) as handle:
                    yield handle
        else:
            with open(self.path / filename, "rb") as handle:
                yield handle


def resolve_feed(explicit: str | None) -> Feed:
    """Find the feed: an explicit path, else the one thing in data/raw that looks like one."""
    if explicit:
        path = Path(explicit)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        if not path.exists():
            raise SystemExit(f"No such feed: {path}")
        return Feed(path, is_zip=path.suffix.lower() == ".zip")

    candidates: list[Feed] = []
    for zip_path in sorted(RAW_DIR.glob("*.zip")):
        with zipfile.ZipFile(zip_path) as archive:
            names = {Path(n).name for n in archive.namelist()}
        if "agency.txt" in names:
            candidates.append(Feed(zip_path, is_zip=True))
    for directory in sorted(p for p in RAW_DIR.iterdir() if p.is_dir()):
        if (directory / "agency.txt").exists():
            candidates.append(Feed(directory, is_zip=False))

    if not candidates:
        raise SystemExit(
            f"No GTFS feed found in {RAW_DIR}.\n"
            "Expected a .zip or a folder containing agency.txt. "
            "See docs/DATA-SOURCING.md for where to get the Dubai RTA feed."
        )
    if len(candidates) > 1:
        listing = "\n  ".join(c.label for c in candidates)
        raise SystemExit(
            f"Several feeds found in {RAW_DIR}:\n  {listing}\n"
            "Pick one with --feed."
        )
    return candidates[0]


# --------------------------------------------------------------------------
# --inspect
# --------------------------------------------------------------------------

def inspect_feed(feed: Feed) -> None:
    """Report what the feed actually contains. Writes nothing, reads nothing from MySQL."""
    present = set(feed.member_names())

    print(f"Feed: {feed.path}")
    print(f"Files in feed: {len(present)}\n")

    missing_required = [f for f in required_filenames() if f not in present]
    if missing_required:
        print("MISSING REQUIRED FILES: " + ", ".join(missing_required))
        print("This is not a usable GTFS feed.\n")

    if "calendar.txt" not in present and "calendar_dates.txt" not in present:
        print("WARNING: neither calendar.txt nor calendar_dates.txt present -- "
              "the feed defines no service days at all.\n")

    print(f"{'file':<22} {'rows':>10}  columns")
    print("-" * 78)

    for spec in files_in_load_order():
        if spec.filename not in present:
            marker = "REQUIRED" if spec.required else "absent (optional)"
            print(f"{spec.filename:<22} {'-':>10}  {marker}")
            continue

        with feed.open(spec.filename) as handle:
            header = pd.read_csv(handle, nrows=0, encoding="utf-8-sig")
        actual = list(header.columns)

        rows = count_rows(feed, spec)
        print(f"{spec.filename:<22} {rows:>10,}  {len(actual)} columns")

        extra = [c for c in actual if c not in spec.columns]
        absent = [c for c in spec.columns if c not in actual]
        if extra:
            print(f"{'':<22} {'':>10}  + beyond spec: {', '.join(extra)}")
        if absent:
            print(f"{'':<22} {'':>10}  - spec cols absent: {', '.join(absent)}")

    unexpected = present - set(BY_FILENAME) - IGNORED_FILES
    known_unmodelled = present & IGNORED_FILES
    if known_unmodelled:
        print(f"\nPresent but not modelled: {', '.join(sorted(known_unmodelled))}")
    if unexpected:
        print(f"Not in the GTFS standard:  {', '.join(sorted(unexpected))}")

    print()
    report_service_span(feed, present)
    report_time_range(feed, present)

    print("\nNext: write sql/schema.sql against the column lists above, "
          "then re-run with --load.")


def count_rows(feed: Feed, spec: GtfsFile) -> int:
    """Row count without holding the file in memory."""
    total = 0
    with feed.open(spec.filename) as handle:
        for chunk in pd.read_csv(
            handle, usecols=[0], chunksize=READ_CHUNKSIZE, encoding="utf-8-sig"
        ):
            total += len(chunk)
    return total


def report_service_span(feed: Feed, present: set[str]) -> None:
    """The date window the feed covers -- i.e. what the dashboard can honestly claim."""
    starts: list[date] = []
    ends: list[date] = []

    if "calendar.txt" in present:
        with feed.open("calendar.txt") as handle:
            cal = pd.read_csv(handle, encoding="utf-8-sig", dtype="string")
        starts += [d for d in cal["start_date"].map(gtfs_date_to_date) if d]
        ends += [d for d in cal["end_date"].map(gtfs_date_to_date) if d]

    if "calendar_dates.txt" in present:
        with feed.open("calendar_dates.txt") as handle:
            cd = pd.read_csv(handle, encoding="utf-8-sig", dtype="string")
        dates = [d for d in cd["date"].map(gtfs_date_to_date) if d]
        starts += dates
        ends += dates

    if starts and ends:
        print(f"Service span: {min(starts)} -> {max(ends)}")
    else:
        print("Service span: could not be determined")


def report_time_range(feed: Feed, present: set[str]) -> None:
    """Flag past-midnight times, and show the real operating window."""
    if "stop_times.txt" not in present:
        return

    lowest: int | None = None
    highest: int | None = None
    past_midnight = 0

    with feed.open("stop_times.txt") as handle:
        for chunk in pd.read_csv(
            handle,
            usecols=["departure_time"],
            chunksize=READ_CHUNKSIZE,
            encoding="utf-8-sig",
            dtype="string",
        ):
            secs = chunk["departure_time"].map(gtfs_time_to_seconds).dropna()
            if secs.empty:
                continue
            lowest = min(x for x in (lowest, int(secs.min())) if x is not None)
            highest = max(x for x in (highest, int(secs.max())) if x is not None)
            past_midnight += int((secs >= 24 * 3600).sum())

    if lowest is None or highest is None:
        print("Operating window: no departure times present")
        return

    print(f"Operating window: {fmt_secs(lowest)} -> {fmt_secs(highest)}")
    if past_midnight:
        print(f"  {past_midnight:,} departures are past 24:00:00 "
              "(service running into the following morning).")
        print("  Confirms times must be stored as seconds, not TIME-of-day.")


def fmt_secs(seconds: int) -> str:
    return f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"


# --------------------------------------------------------------------------
# --load
# --------------------------------------------------------------------------

def load_feed(
    feed: Feed,
    engine: Engine,
    only: set[str] | None,
    skip: set[str],
    truncate: bool,
    chunksize: int,
) -> None:
    """Load the feed into existing tables, parents before children."""
    present = set(feed.member_names())
    existing_tables = set(sa_inspect(engine).get_table_names())

    plan = [
        spec for spec in files_in_load_order()
        if spec.filename in present
        and spec.table not in skip
        and (only is None or spec.table in only)
    ]

    if not plan:
        raise SystemExit("Nothing to load -- check --only / --skip against the feed.")

    missing_tables = [s.table for s in plan if s.table not in existing_tables]
    if missing_tables:
        raise SystemExit(
            "These tables do not exist yet: " + ", ".join(missing_tables) + "\n"
            "Create them first:\n"
            "  mysql -u root -p dubai_transport < sql/schema.sql\n"
            "This loader will not auto-create tables -- pandas would infer an "
            "all-TEXT schema with no keys or constraints."
        )

    if truncate:
        truncate_tables([s.table for s in reversed(plan)], engine)

    print(f"Loading {feed.label} -> {engine.url.database}\n")
    for spec in plan:
        rows = load_file(feed, spec, engine, chunksize)
        print(f"  {spec.table:<18} {rows:>10,} rows")

    print("\nLoad complete.")


def truncate_tables(tables: list[str], engine: Engine) -> None:
    """Empty tables child-first so a re-run is idempotent.

    FK checks are disabled for the duration: even in the correct order, a
    self-referencing table (stops.parent_station) cannot be truncated with
    constraints active. The setting is session-scoped, so it cannot leak into
    other connections, and it is restored before the transaction closes.
    """
    print(f"Truncating: {', '.join(tables)}")
    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        try:
            for table in tables:
                conn.execute(text(f"TRUNCATE TABLE `{table}`"))
        finally:
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))


def load_file(feed: Feed, spec: GtfsFile, engine: Engine, chunksize: int) -> int:
    """Stream one GTFS file into its table. Returns rows written."""
    # Only load columns the destination table actually has. A feed may carry
    # spec columns the schema chose not to model, plus vendor extensions.
    table_columns = {c["name"] for c in sa_inspect(engine).get_columns(spec.table)}

    written = 0
    with feed.open(spec.filename) as handle:
        reader = pd.read_csv(handle, chunksize=READ_CHUNKSIZE, **read_kwargs(spec))
        for chunk in reader:
            chunk = coerce_frame(chunk, spec)
            chunk = chunk[[c for c in chunk.columns if c in table_columns]]

            if spec.table == "stops":
                chunk = sort_stops_parents_first(chunk)

            chunk.to_sql(
                spec.table,
                con=engine,
                if_exists="append",
                index=False,
                chunksize=chunksize,
                method="multi",
            )
            written += len(chunk)
    return written


def sort_stops_parents_first(df: pd.DataFrame) -> pd.DataFrame:
    """Order stops so parent stations precede the platforms that reference them.

    stops.parent_station points at another row in the same file, and feeds do
    not guarantee parents come first. With the self-FK enforced, a platform
    inserted ahead of its station fails on a constraint that is not actually
    violated by the finished table -- only by the insert order.

    location_type: 1 = station (the parent), 0/blank = stop or platform.
    """
    if "location_type" not in df.columns:
        return df
    is_station = (df["location_type"] == 1).fillna(False)
    return pd.concat([df[is_station], df[~is_station]], ignore_index=True)


# --------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect or load a GTFS static feed into MySQL.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--inspect", action="store_true",
                      help="report the feed's real contents; no database access")
    mode.add_argument("--load", action="store_true",
                      help="load into the tables created by sql/schema.sql")

    parser.add_argument("--feed", help="path to a GTFS .zip or extracted folder "
                                       "(default: autodetect in data/raw/)")
    parser.add_argument("--only", help="comma-separated tables to load")
    parser.add_argument("--skip", default="", help="comma-separated tables to skip")
    parser.add_argument("--truncate", action="store_true",
                        help="empty the target tables first (makes re-runs idempotent)")
    parser.add_argument("--chunksize", type=int, default=DEFAULT_CHUNKSIZE,
                        help=f"rows per INSERT batch (default {DEFAULT_CHUNKSIZE})")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    feed = resolve_feed(args.feed)

    if args.inspect:
        inspect_feed(feed)
        return

    load_feed(
        feed=feed,
        engine=get_engine(),
        only={t.strip() for t in args.only.split(",")} if args.only else None,
        skip={t.strip() for t in args.skip.split(",") if t.strip()},
        truncate=args.truncate,
        chunksize=args.chunksize,
    )


if __name__ == "__main__":
    main()
