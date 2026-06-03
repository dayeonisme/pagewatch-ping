import unittest

from pagewatch_ping.detector import detect_change, fingerprint, text_blocks


class DetectorTests(unittest.TestCase):
    def test_fingerprint_ignores_scripts_styles_and_whitespace(self):
        html = """
        <html>
          <head><style>.x { color: red; }</style><script>now()</script></head>
          <body><h1> Notice </h1><p> New   item </p></body>
        </html>
        """

        self.assertEqual(text_blocks(html), ["Notice", "New item"])
        self.assertEqual(fingerprint(html), fingerprint("<h1>Notice</h1><p>New item</p>"))

    def test_detects_new_post_when_new_heading_like_text_is_added(self):
        before = "<main><h1>공지사항</h1><a>기존 게시글</a></main>"
        after = "<main><h1>공지사항</h1><a>신규 이벤트 안내</a><a>기존 게시글</a></main>"

        result = detect_change(before, after)

        self.assertTrue(result.changed)
        self.assertEqual(result.change_type, "신규 게시글 등록")
        self.assertIn("신규 이벤트 안내", result.summary)

    def test_detects_page_structure_change_when_text_changes_without_new_items(self):
        before = "<main><h1>소개</h1><p>운영 시간: 09:00</p></main>"
        after = "<main><h1>소개</h1><p>운영 시간: 10:00</p></main>"

        result = detect_change(before, after)

        self.assertTrue(result.changed)
        self.assertEqual(result.change_type, "페이지 내 구성 요소 변경")
        self.assertIn("운영 시간: 10:00", result.summary)

    def test_reports_no_change_for_equivalent_html(self):
        result = detect_change("<p>same text</p>", "<div><p>same   text</p></div>")

        self.assertFalse(result.changed)
        self.assertEqual(result.change_type, "변경 없음")


if __name__ == "__main__":
    unittest.main()
