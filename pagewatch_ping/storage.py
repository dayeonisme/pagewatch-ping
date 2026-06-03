from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


DEFAULT_CHECK_INTERVAL_MINUTES = 1440
ALLOWED_CHECK_INTERVAL_MINUTES = (60, 360, 1440, 4320, 10080)


@dataclass(frozen=True)
class UrlRecord:
    id: int
    name: str
    url: str
    enabled: bool
    check_interval_minutes: int
    last_hash: str | None
    last_content: str | None
    last_status: str
    last_checked_at: str | None
    created_at: str
    updated_at: str


class UrlStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS urls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    url TEXT NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    check_interval_minutes INTEGER NOT NULL DEFAULT 1440,
                    last_hash TEXT,
                    last_content TEXT,
                    last_status TEXT NOT NULL DEFAULT '대기',
                    last_checked_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            placeholders = ",".join("?" for _value in ALLOWED_CHECK_INTERVAL_MINUTES)
            connection.execute(
                f"""
                UPDATE urls
                SET check_interval_minutes = ?
                WHERE check_interval_minutes NOT IN ({placeholders})
                """,
                (DEFAULT_CHECK_INTERVAL_MINUTES, *ALLOWED_CHECK_INTERVAL_MINUTES),
            )

    def list_urls(self) -> list[UrlRecord]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM urls ORDER BY id DESC").fetchall()
        return [self._record(row) for row in rows]

    def get_url(self, url_id: int) -> UrlRecord | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM urls WHERE id = ?", (url_id,)).fetchone()
        return self._record(row) if row else None

    def create_url(
        self,
        name: str,
        url: str,
        check_interval_minutes: int = DEFAULT_CHECK_INTERVAL_MINUTES,
    ) -> UrlRecord:
        now = _now()
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO urls
                    (name, url, enabled, check_interval_minutes, created_at, updated_at)
                VALUES (?, ?, 1, ?, ?, ?)
                """,
                (name.strip(), url.strip(), check_interval_minutes, now, now),
            )
            url_id = int(cursor.lastrowid)
        record = self.get_url(url_id)
        if record is None:
            raise RuntimeError("created URL could not be loaded")
        return record

    def update_url(
        self,
        url_id: int,
        name: str,
        url: str,
        check_interval_minutes: int,
        enabled: bool,
    ) -> UrlRecord:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE urls
                SET name = ?, url = ?, check_interval_minutes = ?, enabled = ?, updated_at = ?
                WHERE id = ?
                """,
                (name.strip(), url.strip(), check_interval_minutes, int(enabled), _now(), url_id),
            )
        record = self.get_url(url_id)
        if record is None:
            raise KeyError(f"URL not found: {url_id}")
        return record

    def delete_url(self, url_id: int) -> bool:
        with self._connect() as connection:
            cursor = connection.execute("DELETE FROM urls WHERE id = ?", (url_id,))
        return cursor.rowcount > 0

    def mark_checked(
        self,
        url_id: int,
        *,
        last_hash: str | None,
        last_content: str | None,
        last_status: str,
        last_checked_at: str,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE urls
                SET last_hash = ?, last_content = ?, last_status = ?, last_checked_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (last_hash, last_content, last_status, last_checked_at, _now(), url_id),
            )

    def _record(self, row: sqlite3.Row) -> UrlRecord:
        return UrlRecord(
            id=int(row["id"]),
            name=str(row["name"]),
            url=str(row["url"]),
            enabled=bool(row["enabled"]),
            check_interval_minutes=int(row["check_interval_minutes"]),
            last_hash=row["last_hash"],
            last_content=row["last_content"],
            last_status=str(row["last_status"]),
            last_checked_at=row["last_checked_at"],
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
