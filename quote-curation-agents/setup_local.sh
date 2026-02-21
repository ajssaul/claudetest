#!/bin/bash
# ============================================================
# 명언 큐레이션 시스템 — 맥북 로컬 설치 스크립트
# ============================================================

set -e

echo "============================================"
echo "  명언 큐레이션 시스템 로컬 설치"
echo "============================================"
echo

# 1. Python 버전 확인
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Python이 설치되어 있지 않습니다."
    echo "   brew install python3"
    exit 1
fi

PY_VERSION=$($PYTHON_CMD --version 2>&1)
echo "✅ $PY_VERSION"

# 2. 가상환경 생성
if [ ! -d "venv" ]; then
    echo "📦 가상환경 생성 중..."
    $PYTHON_CMD -m venv venv
    echo "✅ 가상환경 생성 완료"
else
    echo "✅ 가상환경 이미 존재"
fi

# 3. 가상환경 활성화
source venv/bin/activate
echo "✅ 가상환경 활성화"

# 4. 의존성 설치
echo "📦 패키지 설치 중..."
pip install -r requirements.txt --quiet
echo "✅ 패키지 설치 완료"

# 5. .env 파일 설정
if [ ! -f ".env" ]; then
    echo
    echo "⚠️  .env 파일이 없습니다. 생성합니다."
    echo

    # Anthropic API 키
    read -p "Anthropic API 키 입력: " ANTHROPIC_KEY
    if [ -z "$ANTHROPIC_KEY" ]; then
        echo "❌ API 키가 필요합니다."
        exit 1
    fi

    # YouTube API 키
    read -p "YouTube Data API 키 입력 (없으면 Enter): " YOUTUBE_KEY

    # .env 작성
    echo "ANTHROPIC_API_KEY=$ANTHROPIC_KEY" > .env
    if [ -n "$YOUTUBE_KEY" ]; then
        echo "YOUTUBE_API_KEY=$YOUTUBE_KEY" >> .env
    fi

    echo "✅ .env 파일 생성 완료"
else
    echo "✅ .env 파일 이미 존재"

    # YouTube API 키가 없으면 추가 안내
    if ! grep -q "YOUTUBE_API_KEY" .env; then
        echo
        read -p "YouTube Data API 키를 추가하시겠습니까? (y/N): " ADD_YT
        if [ "$ADD_YT" = "y" ] || [ "$ADD_YT" = "Y" ]; then
            read -p "YouTube Data API 키 입력: " YOUTUBE_KEY
            if [ -n "$YOUTUBE_KEY" ]; then
                echo "YOUTUBE_API_KEY=$YOUTUBE_KEY" >> .env
                echo "✅ YouTube API 키 추가 완료"
            fi
        fi
    fi
fi

# 6. output 디렉토리 생성
mkdir -p output

# 7. 완료
echo
echo "============================================"
echo "  ✅ 설치 완료!"
echo "============================================"
echo
echo "사용법:"
echo "  cd $(pwd)"
echo "  source venv/bin/activate"
echo
echo "  # 대화형 모드"
echo "  python main.py"
echo
echo "  # CLI 모드"
echo '  python main.py --topic "비즈니스" --count 10'
echo '  python main.py --topic "리더십" --leaders "일론 머스크,스티브 잡스" --count 5'
echo
echo "  # 결과 파일 저장"
echo '  python main.py --topic "비즈니스" --count 10 --output output/business_10.tsv'
echo
