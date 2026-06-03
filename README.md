# PagewatchPing

Local URL change monitor that sends Telegram alerts when registered pages change.

## Repository Name

Recommended GitHub repository name: `pagewatch-ping`

The app, repository, package, data directory, and environment variable names use the PagewatchPing naming family.

## Run

```bash
export PAGEWATCHPING_TELEGRAM_BOT_TOKEN="your-bot-token"
export PAGEWATCHPING_TELEGRAM_CHAT_ID="your-chat-id"
bash run.sh
```

Open `http://127.0.0.1:8765`.

## macOS Autostart

Register PagewatchPing as a macOS LaunchAgent so it starts automatically after login, including after a PC restart:

```bash
bash install_autostart.sh
```

The installer asks once for Telegram Bot Token and Chat ID, writes `~/Library/LaunchAgents/com.pagewatchping.app.plist`, and starts the app immediately.

Remove autostart:

```bash
bash uninstall_autostart.sh
```

## Features

- Add, edit, delete, and list watched URLs.
- Store watched URLs in `~/.pagewatch-ping/pagewatch_ping.db`.
- Register a macOS LaunchAgent for restart-safe autostart.
- Check pages on each URL's interval.
- Use a default check interval of 1 day.
- Change each URL's interval from a dropdown: 1 hour, 6 hours, 1 day, 3 days, or 7 days.
- Send Telegram alerts only after the first baseline check.
- Include a brief change type and summary, such as `신규 게시글 등록` or `페이지 내 구성 요소 변경`.

## Test

```bash
python3 -m unittest discover -s tests
```
