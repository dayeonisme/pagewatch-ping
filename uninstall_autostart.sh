#!/bin/bash
set -euo pipefail

PLIST_NAME="com.pagewatchping.app"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"
USER_ID="$(id -u)"

launchctl bootout "gui/${USER_ID}" "$PLIST_PATH" 2>/dev/null || true
rm -f "$PLIST_PATH"

echo "PagewatchPing 자동 시작 등록을 제거했습니다."
