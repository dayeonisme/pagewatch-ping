#!/bin/bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLIST_NAME="com.pagewatchping.app"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"
LOG_DIR="$HOME/Library/Logs/PagewatchPing"
PYTHON="$(which python3)"
USER_ID="$(id -u)"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  PagewatchPing 자동 시작 설치"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
read -r -p "Telegram Bot Token을 입력하세요: " BOT_TOKEN
read -r -p "Telegram Chat ID를 입력하세요: " CHAT_ID

mkdir -p "$HOME/Library/LaunchAgents"
mkdir -p "$LOG_DIR"

cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${PLIST_NAME}</string>

  <key>ProgramArguments</key>
  <array>
    <string>${PYTHON}</string>
    <string>${APP_DIR}/app.py</string>
  </array>

  <key>WorkingDirectory</key>
  <string>${APP_DIR}</string>

  <key>EnvironmentVariables</key>
  <dict>
    <key>PAGEWATCHPING_TELEGRAM_BOT_TOKEN</key>
    <string>${BOT_TOKEN}</string>
    <key>PAGEWATCHPING_TELEGRAM_CHAT_ID</key>
    <string>${CHAT_ID}</string>
  </dict>

  <key>RunAtLoad</key>
  <true/>

  <key>KeepAlive</key>
  <true/>

  <key>StandardOutPath</key>
  <string>${LOG_DIR}/pagewatchping.log</string>

  <key>StandardErrorPath</key>
  <string>${LOG_DIR}/pagewatchping.err</string>
</dict>
</plist>
EOF

launchctl bootout "gui/${USER_ID}" "$PLIST_PATH" 2>/dev/null || true
launchctl bootstrap "gui/${USER_ID}" "$PLIST_PATH"
launchctl kickstart -k "gui/${USER_ID}/${PLIST_NAME}"

sleep 2

echo ""
if curl -s http://127.0.0.1:8765 >/dev/null 2>&1; then
  echo "✓ 설치 완료. PagewatchPing이 실행 중입니다."
  echo "  → http://127.0.0.1:8765"
else
  echo "설치는 완료됐지만 서버 응답 확인은 아직 되지 않았습니다."
  echo "잠시 후 http://127.0.0.1:8765 에 접속하거나 로그를 확인하세요."
fi
echo ""
echo "재시작 후에도 로그인 시 자동 실행됩니다."
echo "로그 위치: ${LOG_DIR}"
echo ""
echo "제거:"
echo "  bash uninstall_autostart.sh"
