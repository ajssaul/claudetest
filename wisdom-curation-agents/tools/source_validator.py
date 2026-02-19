"""
출처 유효성 검증 도구.
- 퍼블릭 도메인 여부 확인 (저자 사망 연도 체크)
- URL 유효성 검증
- 출처 유형 자동 분류
"""

import logging
import re
from typing import Optional
from urllib.parse import urlparse

import httpx

from .book_search import BookSearchTool

logger = logging.getLogger("wisdom-agents.tools.source_validator")


class SourceValidator:
    """출처의 유효성을 검증한다."""

    SOURCE_TYPE_PATTERNS = {
        "도서": [
            r"gutenberg\.org",
            r"archive\.org",
            r"books\.google",
            r"goodreads\.com",
        ],
        "SNS": [
            r"twitter\.com",
            r"x\.com",
            r"linkedin\.com",
        ],
        "블로그": [
            r"medium\.com",
            r"substack\.com",
            r"blog\.",
            r"wordpress\.com",
            r"blogspot\.com",
        ],
        "연설": [
            r"commencement",
            r"speech",
            r"ted\.com",
        ],
        "팟캐스트": [
            r"podcast",
            r"spotify\.com",
            r"apple\.com/podcast",
        ],
        "인터뷰": [
            r"interview",
        ],
    }

    # 사용 불가 출처 패턴
    BLOCKED_PATTERNS = [
        r"udemy\.com",
        r"coursera\.org",
        r"skillshare\.com",
        r"masterclass\.com",
    ]

    @staticmethod
    def classify_source_type(url: str, source_name: str = "") -> str:
        """URL과 출처명으로 출처 유형을 자동 분류한다."""
        combined = f"{url} {source_name}".lower()

        for source_type, patterns in SourceValidator.SOURCE_TYPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, combined, re.IGNORECASE):
                    return source_type

        # YouTube
        if re.search(r"youtube\.com|youtu\.be", combined):
            return "연설"  # 기본적으로 연설로 분류 (추후 세분화)

        return "기타"

    @staticmethod
    def is_blocked_source(url: str) -> bool:
        """차단된 출처인지 확인한다."""
        for pattern in SourceValidator.BLOCKED_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        return False

    @staticmethod
    def is_public_domain(author_name: str, death_year: Optional[int] = None) -> bool:
        """저자가 퍼블릭 도메인인지 확인한다."""
        return BookSearchTool.is_public_domain_author(author_name, death_year)

    @staticmethod
    async def validate_url(url: str) -> bool:
        """URL이 유효한지 확인한다 (HEAD 요청)."""
        if not url or url.strip() == "":
            return False

        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False

        try:
            async with httpx.AsyncClient(
                timeout=10, follow_redirects=True
            ) as client:
                resp = await client.head(url)
                return resp.status_code < 400
        except Exception:
            # HEAD 실패 시 GET으로 재시도
            try:
                async with httpx.AsyncClient(
                    timeout=10, follow_redirects=True
                ) as client:
                    resp = await client.get(url)
                    return resp.status_code < 400
            except Exception:
                return False

    @staticmethod
    def validate_source_completeness(wisdom_data: dict) -> list[str]:
        """출처 정보의 완전성을 검증하고 문제 목록을 반환한다."""
        issues = []

        if not wisdom_data.get("source"):
            issues.append("출처명이 없습니다")
        elif wisdom_data["source"] in ["구전", "알 수 없음", "Unknown"]:
            issues.append("출처가 불명확합니다")

        if not wisdom_data.get("source_url"):
            issues.append("출처 URL이 없습니다")

        if not wisdom_data.get("source_type"):
            issues.append("출처 유형이 지정되지 않았습니다")

        if not wisdom_data.get("wisdom_original"):
            issues.append("원문이 없습니다")

        if not wisdom_data.get("leader_name") and not wisdom_data.get("leader_name_en"):
            issues.append("발언자 정보가 없습니다")

        return issues
