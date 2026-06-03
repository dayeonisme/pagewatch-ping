from __future__ import annotations

import urllib.parse
import urllib.request

from pagewatch_ping.detector import ChangeResult


def build_alert_message(
    *,
    app_name: str,
    name: str,
    url: str,
    result: ChangeResult,
    checked_at: str,
) -> str:
    return "\n".join(
        [
            f"[{app_name}] 변경 감지",
            f"이름: {name}",
            f"유형: {result.change_type}",
            f"요약: {result.summary}",
            f"URL: {url}",
            f"확인 시간: {checked_at}",
        ]
    )


def send_telegram_message(bot_token: str, chat_id: str, text: str) -> None:
    endpoint = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode("utf-8")
    request = urllib.request.Request(endpoint, data=payload, method="POST")
    with urllib.request.urlopen(request, timeout=15) as response:
        if response.status >= 400:
            raise RuntimeError(f"Telegram API returned HTTP {response.status}")
