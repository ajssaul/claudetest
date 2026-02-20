import os

# Anthropic API 설정
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
DEFAULT_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
MAX_TOKENS = 16384

# 피드백 루프 제한
MAX_SAME_ROUTE_FEEDBACK = 3
MAX_PIPELINE_RESTART = 2
MAX_TOTAL_FEEDBACK = 10

# 수집 설정
COLLECTION_MULTIPLIER = 2.0  # 요청 개수 대비 수집 배수
MIN_COLLECTION_MULTIPLIER = 1.5

# 출력 디렉토리
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

# 로깅
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# 프롬프트 디렉토리
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")

# 가이드라인 파일
GUIDELINES_PATH = os.path.join(
    os.path.dirname(__file__), "guidelines", "quote_curation_v1.0.md"
)
