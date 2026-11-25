"""Helper script to create the target PostgreSQL database if it does not exist."""

import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url

from app.core.config import get_settings


def ensure_database_exists() -> None:
    """Connect to the maintenance database and create the configured target DB if missing."""
    settings = get_settings()
    url = make_url(settings.DATABASE_URL)
    if not url.drivername.startswith("postgresql"):
        print(f"Skipping PostgreSQL DB creation for driver: {url.drivername}")
        return

    target_db = url.database
    admin_url = url.set(drivername="postgresql", database="postgres").render_as_string(hide_password=False)

    with psycopg.connect(admin_url, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (target_db,))
            if cur.fetchone():
                print(f"Database '{target_db}' already exists.")
            else:
                cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(target_db)))
                print(f"Database '{target_db}' created successfully.")


if __name__ == "__main__":
    ensure_database_exists()
