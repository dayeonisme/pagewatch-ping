# PagewatchPing

등록한 URL의 변경사항을 주기적으로 확인하고, 변경이 감지되면 Telegram으로 알림을 보내는 로컬 PC 애플리케이션입니다.

## 주요 기능

- 감시할 URL 추가, 수정, 삭제, 목록 확인
- URL별 확인 주기 설정
  - 1시간
  - 6시간
  - 1일
  - 3일
  - 7일
- 기본 확인 주기: 1일
- 첫 확인 시에는 기준값만 저장하고 알림은 보내지 않음
- 이후 변경이 감지되면 Telegram 알림 전송
- 알림에 변경 유형과 간단한 요약 포함
  - `신규 게시글 등록`
  - `페이지 내 구성 요소 변경`
- macOS 재시작 후 로그인 시 자동 실행

## 실행 방법

```bash
cd pagewatch-ping
export PAGEWATCHPING_TELEGRAM_BOT_TOKEN="your-bot-token"
export PAGEWATCHPING_TELEGRAM_CHAT_ID="your-chat-id"
bash run.sh
```

실행 후 브라우저에서 아래 주소로 접속합니다.

```text
http://127.0.0.1:8765
```

## Telegram 설정

### Bot Token 만들기

1. Telegram에서 `@BotFather`를 엽니다.
2. `/newbot`을 입력합니다.
3. 봇 이름과 username을 입력합니다.
4. BotFather가 발급한 Bot Token을 복사합니다.

### Chat ID 확인

1. 만든 봇에게 `/start` 또는 아무 메시지를 보냅니다.
2. 브라우저에서 아래 주소를 엽니다.

```text
https://api.telegram.org/botBOT_TOKEN/getUpdates
```

3. 응답 JSON의 `message.chat.id` 값을 사용합니다.

## macOS 자동 실행 설정

한 번 설정하면 Mac 재시작 후 로그인 시 PagewatchPing이 자동으로 실행됩니다.

```bash
cd pagewatch-ping
bash install_autostart.sh
```

설치 스크립트는 Telegram Bot Token과 Chat ID를 한 번 입력받고, 아래 LaunchAgent 파일을 생성합니다.

```text
~/Library/LaunchAgents/com.pagewatchping.app.plist
```

자동 실행 제거:

```bash
cd pagewatch-ping
bash uninstall_autostart.sh
```

## 동작 방식

PagewatchPing은 외부 스케줄러 없이 앱 내부 백그라운드 checker로 동작합니다.

1. 앱 실행 시 SQLite DB를 엽니다.
2. 백그라운드 thread가 시작됩니다.
3. thread는 30초마다 등록된 URL 목록을 확인합니다.
4. 비활성 URL은 건너뜁니다.
5. 마지막 확인 시각으로부터 URL별 설정 주기가 지나지 않았으면 건너뜁니다.
6. 확인 시간이 된 URL만 실제로 요청합니다.
7. HTML에서 보이는 텍스트를 추출하고 정규화합니다.
8. 이전 기준값과 비교합니다.
9. 변경이 있으면 Telegram 알림을 보냅니다.
10. 새 기준값과 마지막 확인 상태를 DB에 저장합니다.

30초마다 모든 URL을 요청하는 구조가 아니라, 30초마다 “확인할 URL이 있는지”만 판단합니다.

## 저장 위치

등록 URL과 마지막 확인 상태는 아래 SQLite DB에 저장됩니다.

```text
~/.pagewatch-ping/pagewatch_ping.db
```

로그는 macOS 자동 실행 설정을 사용한 경우 아래 경로에 저장됩니다.

```text
~/Library/Logs/PagewatchPing/
```

## 테스트

```bash
cd pagewatch-ping
python3 -m unittest discover -s tests
```

## 주의사항

- 실제 Telegram Bot Token과 Chat ID는 GitHub에 커밋하지 마세요.
- 너무 짧은 주기로 같은 사이트를 반복 확인하면 사이트에서 자동 요청으로 판단할 수 있습니다.
- 기본값인 1일 주기를 권장합니다.
