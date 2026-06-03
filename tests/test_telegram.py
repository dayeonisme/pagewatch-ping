import unittest

from pagewatch_ping.detector import ChangeResult
from pagewatch_ping.telegram import build_alert_message


class TelegramMessageTests(unittest.TestCase):
    def test_alert_message_contains_change_type_and_summary(self):
        message = build_alert_message(
            app_name="PagewatchPing",
            name="공지사항",
            url="https://example.com/notice",
            result=ChangeResult(
                changed=True,
                change_type="신규 게시글 등록",
                summary="추가: 신규 이벤트 안내",
            ),
            checked_at="2026-06-03 21:30",
        )

        self.assertIn("[PagewatchPing] 변경 감지", message)
        self.assertIn("유형: 신규 게시글 등록", message)
        self.assertIn("요약: 추가: 신규 이벤트 안내", message)
        self.assertIn("https://example.com/notice", message)


if __name__ == "__main__":
    unittest.main()
