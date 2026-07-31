"""Shared MySQL connection helper.

Reads credentials from .env (never hard-coded, never committed) and hands back a
SQLAlchemy engine.

Note the quote_plus() calls: MySQL passwords commonly contain characters such as
'@', ':' or '/' which are URL delimiters. Dropped into a connection string raw,
they silently corrupt it -- an '@' in the password splits the URL early and you
get a misleading "Can't connect to server on '@localhost'" error rather than an
authentication failure. Percent-encoding the credentials avoids this.
"""

import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

load_dotenv()


def get_engine(database: str | None = None) -> Engine:
    """Build an engine from .env. Pass database=None to connect without one selected."""
    user = os.getenv("MYSQL_USER", "root")
    password = os.getenv("MYSQL_PASSWORD", "")
    host = os.getenv("MYSQL_HOST", "localhost")
    port = os.getenv("MYSQL_PORT", "3306")
    db = database if database is not None else os.getenv("MYSQL_DATABASE", "")

    if not password:
        raise RuntimeError(
            "MYSQL_PASSWORD is empty. Copy .env.example to .env and fill it in "
            "(see docs/SETUP.md)."
        )

    url = f"mysql+pymysql://{quote_plus(user)}:{quote_plus(password)}@{host}:{port}/{db}"
    return create_engine(url, pool_pre_ping=True)


if __name__ == "__main__":
    with get_engine().connect() as conn:
        print("server   :", conn.execute(text("SELECT VERSION()")).scalar())
        print("database :", conn.execute(text("SELECT DATABASE()")).scalar())
        print("charset  :", conn.execute(text("SELECT @@character_set_database")).scalar())
    print("CONNECTION OK")
