"""
YouTube URL 웹 검색 유틸리티.

Claude API의 web_search tool을 사용하여 실제 YouTube URL을 찾는다.
서버에서 직접 YouTube/Google에 접근할 수 없으므로,
Claude가 대신 웹 검색을 수행하여 정확한 URL을 확보한다.
"""

import asyncio
import json
import logging
import re
from typing import Optional

import anthropic

import config

logger = logging.getLogger("quote-agents.youtube_search")

# web_search tool 정의
WEB_SEARCH_TOOL = {
    "type": "web_search_20250305",
    "name": "web_search",
    "max_uses": 3,
}


def _get_async_client() -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)


def _extract_youtube_urls_from_response(response) -> list[str]:
    """Claude API 응답에서 YouTube URL을 추출한다."""
    urls = set()

    for block in response.content:
        # web_search_tool_result에서 YouTube URL 추출
        if block.type == "web_search_tool_result":
            for item in getattr(block, "content", []):
                url = getattr(item, "url", "")
                if url and ("youtube.com/watch" in url or "youtu.be/" in url):
                    urls.add(url)

        # 텍스트에서 YouTube URL 추출
        if hasattr(block, "text") and block.text:
            found = re.findall(
                r'https?://(?:www\.)?(?:youtube\.com/watch\?v=[A-Za-z0-9_-]{11}|youtu\.be/[A-Za-z0-9_-]{11})',
                block.text
            )
            urls.update(found)

    return list(urls)


async def search_youtube_url(
    leader_name: str,
    source_title: str,
    wisdom_excerpt: str = "",
) -> Optional[str]:
    """
    웹 검색으로 실제 YouTube URL을 찾는다.

    Args:
        leader_name: 연사 이름 (예: "Simon Sinek")
        source_title: 출처 제목 (예: "How Great Leaders Inspire Action")
        wisdom_excerpt: 명언 원문 일부 (검색 정확도 향상용)

    Returns:
        YouTube URL 문자열 또는 None
    """
    client = _get_async_client()

    # 검색 쿼리 구성
    query_parts = [leader_name, source_title, "YouTube"]
    if wisdom_excerpt:
        # 첫 몇 단어만 사용
        words = wisdom_excerpt.split()[:8]
        query_parts.append(" ".join(words))

    search_query = " ".join(query_parts)

    prompt = (
        f'Find the exact YouTube video URL for this speech/talk:\n'
        f'- Speaker: {leader_name}\n'
        f'- Title: {source_title}\n'
        f'Search for: "{search_query}"\n\n'
        f'Return ONLY the YouTube URL (https://www.youtube.com/watch?v=...) and nothing else.\n'
        f'If you cannot find the exact video, return "NOT_FOUND".'
    )

    try:
        response = await client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=512,
            tools=[WEB_SEARCH_TOOL],
            messages=[{"role": "user", "content": prompt}],
        )

        # 응답에서 YouTube URL 추출
        urls = _extract_youtube_urls_from_response(response)

        if urls:
            logger.info(f"YouTube URL 발견: {leader_name} - {source_title} → {urls[0]}")
            return urls[0]

        # stop_reason이 end_turn이 아니면 추가 대화 필요할 수 있음
        # 하지만 간단히 텍스트에서 URL 추출 시도
        for block in response.content:
            if hasattr(block, "text") and block.text:
                text = block.text.strip()
                if text.startswith("http") and "youtube" in text:
                    return text.split()[0]  # 첫 번째 URL만

        logger.info(f"YouTube URL 미발견: {leader_name} - {source_title}")
        return None

    except Exception as e:
        logger.error(f"YouTube URL 검색 오류: {leader_name} - {source_title}: {e}")
        return None


async def batch_search_youtube_urls(wisdoms: list[dict]) -> list[dict]:
    """
    명언 리스트에서 YouTube 출처 항목의 실제 URL을 웹 검색으로 찾는다.

    YouTube 출처인데 source_url이 비어있거나 가짜인 항목을 대상으로
    Claude web_search로 실제 URL을 찾아서 채운다.

    Args:
        wisdoms: 명언 dict 리스트

    Returns:
        URL이 업데이트된 명언 리스트
    """
    tasks = []
    target_indices = []

    for i, w in enumerate(wisdoms):
        source = w.get("source", "").lower()
        source_type = w.get("source_type", "").lower()
        source_url = w.get("source_url", "")

        # YouTube 출처인데 URL이 비어있거나 무효한 경우
        is_yt_source = (
            "youtube" in source
            or "youtube" in source_type
            or "연설" in source_type
            or "ted" in source.lower()
        )

        needs_url = not source_url or w.get("_youtube_url_invalid", False)

        if is_yt_source and needs_url:
            leader_name = w.get("leader_name_en", w.get("leader_name", ""))
            source_title = w.get("source", "")
            # "YouTube" 제거해서 검색 품질 향상
            source_title = re.sub(r'\s*\(?\s*YouTube\s*\)?\s*$', '', source_title, flags=re.IGNORECASE)
            wisdom_excerpt = w.get("wisdom_original", "")[:100]

            tasks.append(search_youtube_url(leader_name, source_title, wisdom_excerpt))
            target_indices.append(i)

    if not tasks:
        return wisdoms

    logger.info(f"YouTube URL 웹 검색 시작: {len(tasks)}개")

    # 병렬 실행 (동시 요청 수 제한)
    semaphore = asyncio.Semaphore(3)  # 최대 3개 동시 요청

    async def limited_search(coro):
        async with semaphore:
            return await coro

    results = await asyncio.gather(
        *[limited_search(t) for t in tasks],
        return_exceptions=True,
    )

    found_count = 0
    for idx, result in zip(target_indices, results):
        if isinstance(result, Exception):
            logger.error(f"검색 오류 [{idx}]: {result}")
            continue
        if result:
            wisdoms[idx]["source_url"] = result
            wisdoms[idx].pop("_youtube_url_invalid", None)
            wisdoms[idx].pop("_youtube_rejection_reason", None)
            found_count += 1

    logger.info(f"YouTube URL 웹 검색 완료: {found_count}/{len(tasks)}개 발견")
    return wisdoms
