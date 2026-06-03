from __future__ import annotations

import os
import threading
import time
import urllib.request
from datetime import datetime

from pagewatch_ping.detector import detect_change, fingerprint
from pagewatch_ping.storage import UrlRecord, UrlStore
from pagewatch_ping.telegram import build_alert_message, send_telegram_message


APP_NAME = "PagewatchPing"


def fetch_url(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "PagewatchPing/1.0 (+local URL change monitor)",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def check_once(store: UrlStore, record: UrlRecord) -> None:
    checked_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        current_html = fetch_url(record.url)
        current_hash = fingerprint(current_html)
        result = detect_change(record.last_content, current_html)
        if result.changed and record.last_hash and current_hash != record.last_hash:
            _notify(record, result, checked_at)
        status = result.change_type if result.changed else "정상"
        store.mark_checked(
            record.id,
            last_hash=current_hash,
            last_content=current_html,
            last_status=status,
            last_checked_at=checked_at,
        )
    except Exception as exc:
        store.mark_checked(
            record.id,
            last_hash=record.last_hash,
            last_content=record.last_content,
            last_status=f"오류: {exc}",
            last_checked_at=checked_at,
        )


def run_due_checks(store: UrlStore) -> None:
    now = datetime.now()
    for record in store.list_urls():
        if not record.enabled:
            continue
        if record.last_checked_at:
            last_checked = datetime.strptime(record.last_checked_at, "%Y-%m-%d %H:%M:%S")
            elapsed_minutes = (now - last_checked).total_seconds() / 60
            if elapsed_minutes < record.check_interval_minutes:
                continue
        check_once(store, record)


def start_background_checker(store: UrlStore, poll_seconds: int = 30) -> threading.Thread:
    thread = threading.Thread(target=_loop, args=(store, poll_seconds), daemon=True)
    thread.start()
    return thread


def _loop(store: UrlStore, poll_seconds: int) -> None:
    while True:
        run_due_checks(store)
        time.sleep(poll_seconds)


def _notify(record: UrlRecord, result, checked_at: str) -> None:
    bot_token = os.environ.get("PAGEWATCHPING_TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("PAGEWATCHPING_TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        return
    message = build_alert_message(
        app_name=APP_NAME,
        name=record.name,
        url=record.url,
        result=result,
        checked_at=checked_at,
    )
    send_telegram_message(bot_token, chat_id, message)
