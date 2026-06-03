from __future__ import annotations

import html
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from pagewatch_ping.checker import check_once, start_background_checker
from pagewatch_ping.storage import ALLOWED_CHECK_INTERVAL_MINUTES, DEFAULT_CHECK_INTERVAL_MINUTES, UrlStore


DATA_DIR = Path.home() / ".pagewatch-ping"
DB_PATH = DATA_DIR / "pagewatch_ping.db"
INTERVAL_OPTIONS = [
    (60, "1시간"),
    (360, "6시간"),
    (1440, "1일"),
    (4320, "3일"),
    (10080, "7일"),
]


class PagewatchPingHandler(BaseHTTPRequestHandler):
    store: UrlStore

    def do_GET(self) -> None:
        if self.path == "/" or self.path.startswith("/?"):
            self._send_html(render_index(self.store))
            return
        self.send_error(404)

    def do_POST(self) -> None:
        body = self.rfile.read(int(self.headers.get("Content-Length", "0"))).decode("utf-8")
        form = urllib.parse.parse_qs(body)
        path = urllib.parse.urlparse(self.path).path

        if path == "/urls":
            self.store.create_url(
                name=_field(form, "name"),
                url=_field(form, "url"),
                check_interval_minutes=_interval_field(form),
            )
            self._redirect("/")
            return

        if path.startswith("/urls/"):
            parts = path.strip("/").split("/")
            url_id = int(parts[1])
            action = parts[2] if len(parts) > 2 else ""
            if action == "update":
                self.store.update_url(
                    url_id,
                    name=_field(form, "name"),
                    url=_field(form, "url"),
                    check_interval_minutes=_interval_field(form),
                    enabled=_field(form, "enabled", "0") == "1",
                )
            elif action == "delete":
                self.store.delete_url(url_id)
            elif action == "check":
                record = self.store.get_url(url_id)
                if record:
                    check_once(self.store, record)
            self._redirect("/")
            return

        self.send_error(404)

    def log_message(self, format: str, *args) -> None:
        return

    def _send_html(self, content: str) -> None:
        encoded = content.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _redirect(self, location: str) -> None:
        self.send_response(303)
        self.send_header("Location", location)
        self.end_headers()


def render_index(store: UrlStore) -> str:
    rows = "\n".join(render_url_row(record) for record in store.list_urls())
    if not rows:
        rows = '<tr><td colspan="7" class="empty">등록된 URL이 없습니다.</td></tr>'
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PagewatchPing</title>
  <style>{STYLE}</style>
</head>
<body>
  <main class="shell">
    <header class="top">
      <div>
        <p class="eyebrow">Local URL Change Monitor</p>
        <h1>PagewatchPing</h1>
      </div>
      <p class="status">Telegram token은 환경 변수로 설정합니다.</p>
    </header>

    <section class="panel add-panel">
      <form method="post" action="/urls" class="add-form">
        <input name="name" placeholder="이름" required>
        <input name="url" placeholder="https://example.com/notice" type="url" required>
        {render_interval_select(DEFAULT_CHECK_INTERVAL_MINUTES)}
        <button type="submit">추가</button>
      </form>
    </section>

    <section class="panel table-panel">
      <table>
        <thead>
          <tr>
            <th>이름</th>
            <th>URL</th>
            <th>주기</th>
            <th>활성</th>
            <th>상태</th>
            <th>마지막 확인</th>
            <th></th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </section>
  </main>
</body>
</html>"""


def render_url_row(record) -> str:
    checked = record.last_checked_at or "-"
    enabled_checked = "checked" if record.enabled else ""
    return f"""
<tr>
  <td>
    <form id="update-{record.id}" method="post" action="/urls/{record.id}/update" class="row-form">
      <input name="name" value="{_escape(record.name)}" required>
    </form>
  </td>
  <td><input form="update-{record.id}" name="url" value="{_escape(record.url)}" type="url" required></td>
  <td>{render_interval_select(record.check_interval_minutes, form_id=f"update-{record.id}")}</td>
  <td class="center">
    <input form="update-{record.id}" name="enabled" value="1" type="checkbox" {enabled_checked}>
  </td>
  <td><span class="badge">{_escape(record.last_status)}</span></td>
  <td>{_escape(checked)}</td>
  <td class="actions">
    <button form="update-{record.id}" type="submit">저장</button>
    <form method="post" action="/urls/{record.id}/check"><button type="submit">확인</button></form>
    <form method="post" action="/urls/{record.id}/delete"><button class="danger" type="submit">삭제</button></form>
  </td>
</tr>"""


def render_interval_select(selected_minutes: int, form_id: str | None = None) -> str:
    form_attr = f' form="{_escape(form_id)}"' if form_id else ""
    selected = selected_minutes if selected_minutes in ALLOWED_CHECK_INTERVAL_MINUTES else DEFAULT_CHECK_INTERVAL_MINUTES
    options = "\n".join(
        f'<option value="{minutes}"{" selected" if minutes == selected else ""}>{label}</option>'
        for minutes, label in INTERVAL_OPTIONS
    )
    return f'<select name="check_interval_minutes"{form_attr} aria-label="확인 주기">\n{options}\n</select>'


def run(host: str = "127.0.0.1", port: int = 8765) -> None:
    store = UrlStore(DB_PATH)
    PagewatchPingHandler.store = store
    start_background_checker(store)
    server = ThreadingHTTPServer((host, port), PagewatchPingHandler)
    print(f"PagewatchPing running at http://{host}:{port}")
    server.serve_forever()


def _field(form: dict[str, list[str]], name: str, default: str = "") -> str:
    return form.get(name, [default])[0]


def _int_field(form: dict[str, list[str]], name: str, default: int) -> int:
    try:
        return max(1, int(_field(form, name, str(default))))
    except ValueError:
        return default


def _interval_field(form: dict[str, list[str]]) -> int:
    requested = _int_field(form, "check_interval_minutes", DEFAULT_CHECK_INTERVAL_MINUTES)
    return requested if requested in ALLOWED_CHECK_INTERVAL_MINUTES else DEFAULT_CHECK_INTERVAL_MINUTES


def _escape(value: str) -> str:
    return html.escape(value, quote=True)


STYLE = """
:root {
  color-scheme: light;
  --ink: #1d2521;
  --muted: #65736c;
  --line: #d6ddd8;
  --panel: #fbfcfa;
  --paper: #f2f5f1;
  --accent: #0f7b6c;
  --danger: #a53131;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  color: var(--ink);
  background:
    linear-gradient(90deg, rgba(15,123,108,.08) 1px, transparent 1px),
    linear-gradient(0deg, rgba(15,123,108,.08) 1px, transparent 1px),
    var(--paper);
  background-size: 28px 28px;
}
.shell { width: min(1180px, calc(100vw - 32px)); margin: 36px auto; }
.top { display: flex; justify-content: space-between; align-items: end; gap: 24px; margin-bottom: 18px; }
.eyebrow { margin: 0 0 8px; color: var(--accent); font-size: 12px; text-transform: uppercase; }
h1 { margin: 0; font-size: 42px; letter-spacing: 0; }
.status { margin: 0; color: var(--muted); font-size: 13px; }
.panel {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
  box-shadow: 0 12px 30px rgba(29,37,33,.08);
}
.add-panel { padding: 14px; margin-bottom: 14px; }
.add-form { display: grid; grid-template-columns: 160px minmax(260px, 1fr) 92px 78px; gap: 10px; }
input, select {
  width: 100%;
  min-height: 38px;
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 8px 10px;
  background: white;
  color: var(--ink);
}
button {
  min-height: 36px;
  border: 1px solid var(--accent);
  border-radius: 6px;
  padding: 0 12px;
  background: var(--accent);
  color: white;
  cursor: pointer;
}
button.danger { border-color: var(--danger); background: var(--danger); }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 12px; border-bottom: 1px solid var(--line); text-align: left; font-size: 13px; vertical-align: middle; }
th { color: var(--muted); font-weight: 700; }
td.center { text-align: center; }
.badge { display: inline-block; max-width: 260px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.actions { display: flex; gap: 6px; align-items: center; }
.actions form { display: inline; }
.empty { text-align: center; color: var(--muted); padding: 38px; }
@media (max-width: 820px) {
  .top, .actions { align-items: stretch; flex-direction: column; }
  .add-form { grid-template-columns: 1fr; }
  table, thead, tbody, tr, th, td { display: block; }
  thead { display: none; }
  tr { border-bottom: 1px solid var(--line); padding: 10px; }
  td { border-bottom: 0; padding: 6px; }
}
"""
