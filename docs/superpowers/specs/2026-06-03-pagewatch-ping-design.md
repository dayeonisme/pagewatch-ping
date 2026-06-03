# PagewatchPing Design

## Name

Recommended app name: PagewatchPing.

Recommended GitHub repository name: `pagewatch-ping`.

The app, repository, package, data directory, and environment variable names use the PagewatchPing naming family.

## Goal

PagewatchPing is a local PC application that watches registered URLs and sends a Telegram alert when a page changes.

## Scope

The application supports only the required management actions: view registered URLs, add a URL, edit a URL, and delete a URL. Each URL can also be enabled or disabled and checked manually from the list screen.

The application includes macOS LaunchAgent scripts so the user can configure PagewatchPing once and have it start automatically after login, including after a PC restart.

Each URL has a configurable check interval. The default is 1 day. The UI allows only these intervals: 1 hour, 6 hours, 1 day, 3 days, and 7 days.

## Architecture

The application uses Python standard-library components only:

- `http.server` for the local web UI.
- `sqlite3` for persistent URL storage.
- `threading` for the background checker loop.
- `urllib` for URL fetching and Telegram Bot API calls.
- `html.parser` for extracting normalized page text.
- `launchd` via `~/Library/LaunchAgents/com.pagewatchping.app.plist` for macOS autostart.

This keeps the first version easy to run on a local PC without package installation.

## Change Detection

For each URL, PagewatchPing stores the previous normalized page text and hash. On each check it fetches the current HTML, extracts visible text while ignoring script and style content, normalizes whitespace, and compares the current blocks against the previous blocks.

The background checker wakes every 30 seconds, reads enabled URLs from SQLite, and checks only URLs whose saved `last_checked_at` is older than their configured interval. This means the 30-second loop is only a scheduler tick; it does not fetch every URL every 30 seconds.

The Telegram alert includes:

- URL name.
- Change type.
- Short change summary.
- URL.
- Checked time.

Supported change classifications:

- `신규 게시글 등록`: the page has new text blocks, typically a new notice or post title.
- `페이지 내 구성 요소 변경`: existing text changed, disappeared, moved, or the page structure changed.

The first successful check stores a baseline and does not send an alert.
