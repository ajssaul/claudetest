"""
YouTube URL 검증 유틸리티.

1단계: HTTP 요청으로 URL 접근 가능 여부 확인
2단계: youtube-transcript-api로 트랜스크립트를 가져와 명언 키워드 존재 여부 확인
"""

import asyncio
import logging
import re
from typing import Optional

import httpx

logger = logging.getLogger("quote-agents.url_validator")

# YouTube URL에서 video ID를 추출하는 패턴들
_YT_PATTERNS = [
    re.compile(r"(?:youtube\.com/watch\?.*v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/)([A-Za-z0-9_-]{11})"),
]


def extract_youtube_video_id(url: str) -> Optional[str]:
    """YouTube URL에서 video ID(11자)를 추출한다. 실패 시 None."""
    if not url:
        return None
    for pattern in _YT_PATTERNS:
        m = pattern.search(url)
        if m:
            return m.group(1)
    return None


def is_youtube_url(url: str) -> bool:
    """URL이 YouTube 링크인지 판별한다."""
    if not url:
        return False
    return "youtube.com" in url or "youtu.be" in url


async def verify_url_accessible(url: str, timeout: float = 10.0) -> dict:
    """
    URL이 접근 가능한지 HTTP HEAD/GET으로 확인한다.

    Returns:
        {
            "url": str,
            "accessible": bool,
            "status_code": int | None,
            "error": str | None,
        }
    """
    if not url or not url.startswith("http"):
        return {"url": url, "accessible": False, "status_code": None, "error": "유효하지 않은 URL"}

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
            # HEAD 먼저 시도, 실패 시 GET
            try:
                resp = await client.head(url)
            except Exception:
                resp = await client.get(url)

            # YouTube는 삭제된 영상도 200을 반환할 수 있으므로 본문 확인 필요
            if is_youtube_url(url) and resp.status_code == 200:
                # GET으로 본문을 가져와서 "이용할 수 없는 동영상" 패턴 확인
                if resp.request.method == "HEAD":
                    resp = await client.get(url)

                body = resp.text
                unavailable_patterns = [
                    "이 동영상은 더 이상 사용할 수 없습니다",
                    "Video unavailable",
                    "This video isn't available anymore",
                    "This video is unavailable",
                    "This video has been removed",
                    "This video is private",
                    "This video is no longer available",
                    "Sign in to confirm your age",
                ]
                for pattern in unavailable_patterns:
                    if pattern in body:
                        return {
                            "url": url,
                            "accessible": False,
                            "status_code": resp.status_code,
                            "error": f"YouTube 영상 이용 불가: {pattern}",
                        }

            accessible = resp.status_code < 400
            return {
                "url": url,
                "accessible": accessible,
                "status_code": resp.status_code,
                "error": None if accessible else f"HTTP {resp.status_code}",
            }

    except httpx.TimeoutException:
        return {"url": url, "accessible": False, "status_code": None, "error": "타임아웃"}
    except Exception as e:
        return {"url": url, "accessible": False, "status_code": None, "error": str(e)}


def check_transcript_for_keywords(video_id: str, keywords: list[str], lang_codes: list[str] | None = None) -> dict:
    """
    YouTube 트랜스크립트에서 명언의 핵심 키워드가 존재하는지 확인한다.

    Args:
        video_id: YouTube 영상 ID (11자)
        keywords: 명언에서 추출한 핵심 단어 리스트
        lang_codes: 트랜스크립트 언어 우선순위 (기본: 영어 → 한국어)

    Returns:
        {
            "has_transcript": bool,
            "keyword_match_ratio": float (0.0~1.0),
            "matched_keywords": list[str],
            "error": str | None,
        }
    """
    if lang_codes is None:
        lang_codes = ["en", "ko"]

    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # 수동 자막 우선, 없으면 자동 생성 자막
        transcript = None
        for lang in lang_codes:
            try:
                transcript = transcript_list.find_transcript([lang])
                break
            except Exception:
                continue

        if transcript is None:
            # 자동 생성 자막이라도 시도
            try:
                transcript = transcript_list.find_generated_transcript(lang_codes)
            except Exception:
                pass

        if transcript is None:
            return {
                "has_transcript": False,
                "keyword_match_ratio": 0.0,
                "matched_keywords": [],
                "error": "트랜스크립트 없음",
            }

        # 트랜스크립트 전체 텍스트 결합
        entries = transcript.fetch()
        full_text = " ".join(entry["text"].lower() for entry in entries)

        # 키워드 매칭
        matched = []
        for kw in keywords:
            if kw.lower() in full_text:
                matched.append(kw)

        ratio = len(matched) / len(keywords) if keywords else 0.0

        return {
            "has_transcript": True,
            "keyword_match_ratio": ratio,
            "matched_keywords": matched,
            "error": None,
        }

    except Exception as e:
        return {
            "has_transcript": False,
            "keyword_match_ratio": 0.0,
            "matched_keywords": [],
            "error": str(e),
        }


def extract_keywords_from_quote(wisdom_original: str, min_length: int = 4, max_keywords: int = 8) -> list[str]:
    """명언 원문에서 검증용 핵심 키워드를 추출한다."""
    # 불용어 제거
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "need", "dare", "ought",
        "this", "that", "these", "those", "what", "which", "who", "whom",
        "and", "but", "or", "nor", "not", "for", "with", "about", "from",
        "into", "through", "during", "before", "after", "above", "below",
        "between", "out", "off", "over", "under", "again", "further",
        "then", "once", "here", "there", "when", "where", "why", "how",
        "all", "both", "each", "few", "more", "most", "other", "some",
        "such", "than", "too", "very", "just", "because", "also", "your",
        "you", "they", "them", "their", "its", "our", "his", "her", "she",
        "him", "it", "we", "me", "my", "if", "so", "to", "of", "in", "on",
        "at", "by", "up", "as", "no", "yes",
    }

    # 단어 추출 (알파벳+숫자만)
    words = re.findall(r"[a-zA-Z0-9]+", wisdom_original.lower())
    # 불용어 제거 + 최소 길이 필터
    keywords = [w for w in words if w not in stopwords and len(w) >= min_length]
    # 빈도 기반 정렬 (더 희소한 단어가 더 식별력 높음)
    # 단순히 앞에서부터 고유 키워드 추출
    seen = set()
    unique = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            unique.append(kw)

    return unique[:max_keywords]


async def verify_youtube_source(
    url: str,
    wisdom_original: str,
    keyword_match_threshold: float = 0.3,
) -> dict:
    """
    YouTube 출처를 종합 검증한다.

    1단계: URL 접근 가능 여부
    2단계: 트랜스크립트에서 명언 키워드 매칭

    Returns:
        {
            "url": str,
            "video_id": str | None,
            "url_accessible": bool,
            "transcript_verified": bool | None,  # None이면 트랜스크립트 확인 불가
            "keyword_match_ratio": float,
            "overall_valid": bool,
            "rejection_reason": str | None,
        }
    """
    result = {
        "url": url,
        "video_id": None,
        "url_accessible": False,
        "transcript_verified": None,
        "keyword_match_ratio": 0.0,
        "overall_valid": False,
        "rejection_reason": None,
    }

    # Video ID 추출
    video_id = extract_youtube_video_id(url)
    result["video_id"] = video_id

    if not video_id:
        result["rejection_reason"] = "유효하지 않은 YouTube URL 형식"
        return result

    # 1단계: URL 접근 가능 여부
    access_check = await verify_url_accessible(url)
    result["url_accessible"] = access_check["accessible"]

    if not access_check["accessible"]:
        result["rejection_reason"] = f"YouTube 영상 접근 불가: {access_check['error']}"
        return result

    # 2단계: 트랜스크립트 키워드 매칭
    keywords = extract_keywords_from_quote(wisdom_original)
    if keywords:
        # 동기 함수를 비동기로 실행
        transcript_check = await asyncio.to_thread(
            check_transcript_for_keywords, video_id, keywords
        )

        result["keyword_match_ratio"] = transcript_check["keyword_match_ratio"]

        if transcript_check["has_transcript"]:
            if transcript_check["keyword_match_ratio"] >= keyword_match_threshold:
                result["transcript_verified"] = True
                result["overall_valid"] = True
            else:
                result["transcript_verified"] = False
                result["rejection_reason"] = (
                    f"트랜스크립트에서 명언 내용 불일치 "
                    f"(키워드 매칭률: {transcript_check['keyword_match_ratio']:.0%}, "
                    f"기준: {keyword_match_threshold:.0%})"
                )
        else:
            # 트랜스크립트 없지만 URL은 접근 가능 → 불확실
            result["transcript_verified"] = None
            result["overall_valid"] = True  # URL은 살아있으므로 일단 통과, 검수자가 판단
            result["rejection_reason"] = None
    else:
        # 키워드 추출 실패 → URL 접근만으로 판단
        result["overall_valid"] = True

    return result


async def batch_verify_youtube_sources(wisdoms: list[dict]) -> list[dict]:
    """
    명언 리스트에서 YouTube 출처를 가진 항목들을 일괄 검증한다.

    각 명언 dict에 '_yt_verification' 키를 추가한다.

    Returns:
        검증 결과가 추가된 명언 리스트 (원본 수정)
    """
    tasks = []
    yt_indices = []

    for i, w in enumerate(wisdoms):
        url = w.get("source_url", "")
        if is_youtube_url(url):
            yt_indices.append(i)
            tasks.append(
                verify_youtube_source(url, w.get("wisdom_original", ""))
            )

    if not tasks:
        return wisdoms

    logger.info(f"YouTube URL 검증 시작: {len(tasks)}개")
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for idx, result in zip(yt_indices, results):
        if isinstance(result, Exception):
            wisdoms[idx]["_yt_verification"] = {
                "overall_valid": False,
                "rejection_reason": f"검증 오류: {result}",
            }
        else:
            wisdoms[idx]["_yt_verification"] = result

    valid_count = sum(
        1 for i in yt_indices
        if wisdoms[i].get("_yt_verification", {}).get("overall_valid", False)
    )
    logger.info(f"YouTube URL 검증 완료: {valid_count}/{len(tasks)}개 유효")

    return wisdoms
