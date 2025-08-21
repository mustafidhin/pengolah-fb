import os
import sqlite3
from typing import Iterable, List


class StateStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS seen_posts (
                    id TEXT PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()

    def has_seen(self, post_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("SELECT 1 FROM seen_posts WHERE id = ? LIMIT 1", (post_id,))
            return cur.fetchone() is not None

    def mark_seen(self, post_ids: Iterable[str]) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany("INSERT OR IGNORE INTO seen_posts (id) VALUES (?)", ((pid,) for pid in post_ids))
            conn.commit()