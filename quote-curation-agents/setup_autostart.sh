#!/bin/bash
# 명언 큐레이션 웹 UI — macOS 자동 시작 설정 스크립트
#
# 이 스크립트를 한 번만 실행하면:
# - 맥 로그인 시 웹 서버가 자동으로 백그라운드 실행
# - 브라우저에서 http://localhost:8080 접속만 하면 바로 사용 가능
# - 터미널 열 필요 없음
#
# 사용법:
#   chmod +x setup_autostart.sh
#   ./setup_autostart.sh

set -e

# 현재 스크립트 위치 기준으로 프로젝트 경로 결정
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_PATH="$(which python3)"
PLIST_NAME="com.quote-curation.web"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"
LOG_DIR="$PROJECT_DIR/logs"

echo ""
echo "=================================================="
echo "  명언 큐레이션 — 자동 시작 설정"
echo "=================================================="
echo ""

# Python 경로 확인
if [ -z "$PYTHON_PATH" ]; then
    echo "오류: python3을 찾을 수 없습니다."
    exit 1
fi
echo "Python: $PYTHON_PATH"
echo "프로젝트: $PROJECT_DIR"

# ANTHROPIC_API_KEY 확인
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo ""
    echo "ANTHROPIC_API_KEY가 설정되지 않았습니다."
    read -p "API 키를 입력하세요: " API_KEY
    if [ -z "$API_KEY" ]; then
        echo "API 키가 필요합니다."
        exit 1
    fi
else
    API_KEY="$ANTHROPIC_API_KEY"
    echo "API 키: 설정됨"
fi

# 로그 디렉토리 생성
mkdir -p "$LOG_DIR"

# 기존 서비스 중지
if launchctl list | grep -q "$PLIST_NAME" 2>/dev/null; then
    echo "기존 서비스 중지 중..."
    launchctl unload "$PLIST_PATH" 2>/dev/null || true
fi

# LaunchAgent plist 생성
cat > "$PLIST_PATH" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_NAME}</string>

    <key>ProgramArguments</key>
    <array>
        <string>${PYTHON_PATH}</string>
        <string>${PROJECT_DIR}/web_app.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>${PROJECT_DIR}</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>ANTHROPIC_API_KEY</key>
        <string>${API_KEY}</string>
    </dict>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>${LOG_DIR}/web_app.log</string>

    <key>StandardErrorPath</key>
    <string>${LOG_DIR}/web_app_error.log</string>
</dict>
</plist>
PLIST

# 서비스 등록 및 시작
launchctl load "$PLIST_PATH"

echo ""
echo "=================================================="
echo "  설정 완료!"
echo "=================================================="
echo ""
echo "  브라우저에서 접속: http://localhost:8080"
echo ""
echo "  관리 명령어:"
echo "    중지:  launchctl unload $PLIST_PATH"
echo "    시작:  launchctl load $PLIST_PATH"
echo "    제거:  ./setup_autostart.sh --uninstall"
echo "    로그:  tail -f $LOG_DIR/web_app.log"
echo ""

# 브라우저 자동 열기
sleep 2
open "http://localhost:8080"
