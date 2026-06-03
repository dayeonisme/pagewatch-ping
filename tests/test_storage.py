import tempfile
import unittest
import sqlite3
from pathlib import Path

from pagewatch_ping.storage import UrlStore


class UrlStoreTests(unittest.TestCase):
    def test_default_check_interval_is_one_day(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = UrlStore(Path(temp_dir) / "pagewatch_ping.db")

            created = store.create_url(
                name="공지",
                url="https://example.com/notice",
            )

            self.assertEqual(created.check_interval_minutes, 1440)

    def test_existing_unsupported_interval_is_migrated_to_one_day(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "pagewatch_ping.db"
            with sqlite3.connect(db_path) as connection:
                connection.execute(
                    """
                    CREATE TABLE urls (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        url TEXT NOT NULL,
                        enabled INTEGER NOT NULL DEFAULT 1,
                        check_interval_minutes INTEGER NOT NULL DEFAULT 5,
                        last_hash TEXT,
                        last_content TEXT,
                        last_status TEXT NOT NULL DEFAULT '대기',
                        last_checked_at TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                    """
                )
                connection.execute(
                    """
                    INSERT INTO urls
                        (name, url, check_interval_minutes, created_at, updated_at)
                    VALUES ('공지', 'https://example.com/notice', 5, '2026-06-03 00:00:00', '2026-06-03 00:00:00')
                    """
                )

            store = UrlStore(db_path)

            self.assertEqual(store.list_urls()[0].check_interval_minutes, 1440)

    def test_create_list_update_and_delete_url(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = UrlStore(Path(temp_dir) / "pagewatch_ping.db")

            created = store.create_url(
                name="공지",
                url="https://example.com/notice",
                check_interval_minutes=10,
            )
            self.assertEqual(created.name, "공지")

            updated = store.update_url(
                created.id,
                name="공지사항",
                url="https://example.com/notices",
                check_interval_minutes=15,
                enabled=False,
            )
            self.assertEqual(updated.name, "공지사항")
            self.assertFalse(updated.enabled)

            urls = store.list_urls()
            self.assertEqual(len(urls), 1)
            self.assertEqual(urls[0].url, "https://example.com/notices")

            self.assertTrue(store.delete_url(created.id))
            self.assertEqual(store.list_urls(), [])


if __name__ == "__main__":
    unittest.main()
