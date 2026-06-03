import tempfile
import unittest
from pathlib import Path

from pagewatch_ping.storage import UrlStore
from pagewatch_ping.web import render_index


class WebRenderTests(unittest.TestCase):
    def test_new_url_form_uses_interval_dropdown_with_one_day_selected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = UrlStore(Path(temp_dir) / "pagewatch_ping.db")

            html = render_index(store)

            self.assertIn('<select name="check_interval_minutes"', html)
            self.assertIn('<option value="60">1시간</option>', html)
            self.assertIn('<option value="360">6시간</option>', html)
            self.assertIn('<option value="1440" selected>1일</option>', html)
            self.assertIn('<option value="4320">3일</option>', html)
            self.assertIn('<option value="10080">7일</option>', html)

    def test_existing_url_row_selects_its_current_interval(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = UrlStore(Path(temp_dir) / "pagewatch_ping.db")
            store.create_url(
                name="공지",
                url="https://example.com/notice",
                check_interval_minutes=360,
            )

            html = render_index(store)

            self.assertIn('<option value="360" selected>6시간</option>', html)


if __name__ == "__main__":
    unittest.main()
