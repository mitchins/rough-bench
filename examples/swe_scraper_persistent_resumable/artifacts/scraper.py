import logging
import sqlite3
import time
from pathlib import Path


LOGGER = logging.getLogger(__name__)


class PersistentScraper:
    def __init__(self, db_path: str = "state.db", rate_limit_seconds: float = 1.0) -> None:
        self.db_path = Path(db_path)
        self.rate_limit_seconds = rate_limit_seconds
        self.connection = sqlite3.connect(self.db_path)
        self.connection.execute(
            """
            create table if not exists checkpoints (
                source text primary key,
                cursor text not null,
                updated_at text not null
            )
            """
        )
        self.connection.execute(
            """
            create table if not exists items (
                item_id text primary key,
                payload text not null,
                seen_at text not null
            )
            """
        )
        self.connection.commit()

    def fetch_page(self, cursor: str) -> str:
        LOGGER.info("fetching cursor=%s", cursor)
        time.sleep(self.rate_limit_seconds)
        return f"payload for {cursor}"

    def save_item(self, item_id: str, payload: str) -> None:
        self.connection.execute(
            """
            insert into items (item_id, payload, seen_at)
            values (?, ?, datetime('now'))
            on conflict(item_id) do update set payload = excluded.payload
            """,
            (item_id, payload),
        )

    def update_checkpoint(self, source: str, cursor: str) -> None:
        self.connection.execute(
            """
            insert into checkpoints (source, cursor, updated_at)
            values (?, ?, datetime('now'))
            on conflict(source) do update set
                cursor = excluded.cursor,
                updated_at = excluded.updated_at
            """,
            (source, cursor),
        )
        self.connection.commit()
