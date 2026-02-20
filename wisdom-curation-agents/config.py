import os

# Groq API 설정
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
DEFAULT_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
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
    os.path.dirname(__file__), "guidelines", "wisdom_curation_v2.1.md"
)
