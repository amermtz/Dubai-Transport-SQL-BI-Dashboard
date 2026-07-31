"""Test configuration.

`scripts/` is a plain directory, not an installed package, so it goes on sys.path
the same way running `python scripts/load_gtfs.py` would put it there.
"""

import sys
import zipfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

FIXTURE_DIR = PROJECT_ROOT / "tests" / "fixtures" / "mini_gtfs"


@pytest.fixture
def feed_dir():
    """The fixture feed as an extracted directory."""
    from load_gtfs import Feed

    return Feed(FIXTURE_DIR, is_zip=False)


@pytest.fixture
def feed_zip(tmp_path):
    """The same feed zipped, nested under a top-level folder.

    Feeds are commonly distributed with the .txt files inside a folder rather
    than at the archive root, so the member lookup has to match on basename.
    """
    from load_gtfs import Feed

    archive_path = tmp_path / "mini-gtfs.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        for txt in sorted(FIXTURE_DIR.glob("*.txt")):
            archive.write(txt, f"dubai_rta/{txt.name}")
    return Feed(archive_path, is_zip=True)
