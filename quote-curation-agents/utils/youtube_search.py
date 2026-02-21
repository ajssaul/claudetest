"""
YouTube URL 검색 유틸리티.

1순위: YouTube Data API v3 (로컬 환경, API 키 필요)
2순위: Claude web_search tool (클라우드 환경, API 키 불필요)

로컬 맥북에서는 YouTube Data API로 정확한 URL을 찾고,
클라우드 환경에서는 Claude가 대신 웹 검색을 수행한다.
"""

import asyncio
import logging
import re
from typing import Optional

import httpx
import anthropic

import config

logger = logging.getLogger("quote-agents.youtube_search")


# ──────────────────────────────────────────────
# 방법 1: YouTube Data API v3 (로컬 맥북용)
# ──────────────────────────────────────────────

async def _search_via_youtube_api(
    leader_name: str,
    source_title: str,
    wisdom_excerpt: str = "",
) -> Optional[str]:
    """YouTube Data API v3로 영상을 검색하여 URL을 반환한다."""
    api_key = config.YOUTUBE_API_KEY
    if not api_key:
        return None

    query = f"{leader_name} {source_title}"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={
                    "part": "snippet",
                    "q": query,
                    "type": "video",
                    "maxResults": 5,
                    "key": api_key,
                },
            )

            if resp.status_code != 200:
                logger.warning(f"YouTube API 오류: {resp.status_code} - {resp.text[:200]}")
                return None

            data = resp.json()
            items = data.get("items", [])

            if not items:
                return None

            # 연사 이름 또는 출처 제목이 snippet에 포함된 결과 우선
            leader_lower = leader_name.lower()
            title_words = set(source_title.lower().split())

            best_match = None
            best_score = -1

            for item in items:
                snippet = item.get("snippet", {})
                video_title = snippet.get("title", "").lower()
                channel = snippet.get("channelTitle", "").lower()
                description = snippet.get("description", "").lower()
                combined = f"{video_title} {channel} {description}"

                score = 0
                if leader_lower in combined:
                    score += 3
                for word in title_words:
                    if len(word) >= 4 and word in combined:
                        score += 1

                if score > best_score:
                    best_score = score
                    video_id = item["id"]["videoId"]
                    best_match = f"https://www.youtube.com/watch?v={video_id}"

            if best_match and best_score >= 2:
                logger.info(f"YouTube API 발견 (score={best_score}): {leader_name} → {best_match}")
                return best_match

            # 매칭 점수가 낮아도 첫 번째 결과 반환
            if items:
                video_id = items[0]["id"]["videoId"]
                url = f"https://www.youtube.com/watch?v={video_id}"
                logger.info(f"YouTube API 발견 (기본): {leader_name} → {url}")
                return url

            return None

    except Exception as e:
        logger.warning(f"YouTube API 검색 실패: {e}")
        return None


# ──────────────────────────────────────────────
# 방법 2: Claude web_search tool (클라우드 백업)
# ──────────────────────────────────────────────

WEB_SEARCH_TOOL = {
    "type": "web_search_20250305",
    "name": "web_search",
    "max_uses": 3,
}


def _extract_youtube_urls_from_response(response) -> list[str]:
    """Claude API 응답에서 YouTube URL을 추출한다."""
    urls = set()

    for block in response.content:
        if block.type == "web_search_tool_result":
            for item in getattr(block, "content", []):
                url = getattr(item, "url", "")
                if url and ("youtube.com/watch" in url or "youtu.be/" in url):
                    urls.add(url)

        if hasattr(block, "text") and block.text:
            found = re.findall(
                r'https?://(?:www\.)?(?:youtube\.com/watch\?v=[A-Za-z0-9_-]{11}|youtu\.be/[A-Za-z0-9_-]{11})',
                block.text
            )
            urls.update(found)

    return list(urls)


async def _search_via_web_search(
    leader_name: str,
    source_title: str,
    wisdom_excerpt: str = "",
) -> Optional[str]:
    """Claude web_search tool로 YouTube URL을 검색한다."""
    client = anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)

    prompt = (
        f'Find the exact YouTube video URL for this speech/talk:\n'
        f'- Speaker: {leader_name}\n'
        f'- Title: {source_title}\n\n'
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

        urls = _extract_youtube_urls_from_response(response)
        if urls:
            logger.info(f"web_search 발견: {leader_name} - {source_title} → {urls[0]}")
            return urls[0]

        for block in response.content:
            if hasattr(block, "text") and block.text:
                text = block.text.strip()
                if text.startswith("http") and "youtube" in text:
                    return text.split()[0]

        logger.info(f"web_search 미발견: {leader_name} - {source_title}")
        return None

    except Exception as e:
        logger.error(f"web_search 오류: {leader_name} - {source_title}: {e}")
        return None


# ──────────────────────────────────────────────
# 통합 검색: YouTube API → web_search 순서
# ──────────────────────────────────────────────

async def search_youtube_url(
    leader_name: str,
    source_title: str,
    wisdom_excerpt: str = "",
) -> Optional[str]:
    """
    YouTube URL을 검색한다. YouTube Data API를 먼저 시도하고,
    실패하면 Claude web_search로 백업 검색한다.
    """
    # 1순위: YouTube Data API
    url = await _search_via_youtube_api(leader_name, source_title, wisdom_excerpt)
    if url:
        return url

    # 2순위: Claude web_search
    url = await _search_via_web_search(leader_name, source_title, wisdom_excerpt)
    if url:
        return url

    return None


async def batch_search_youtube_urls(wisdoms: list[dict]) -> list[dict]:
    """
    명언 리스트에서 YouTube/연설 출처 항목의 실제 URL을 검색으로 찾는다.

    source_url이 비어있거나 무효한 항목 대상으로
    YouTube Data API 또는 web_search로 실제 URL을 찾아서 채운다.
    """
    tasks = []
    target_indices = []

    for i, w in enumerate(wisdoms):
        source = w.get("source", "").lower()
        source_type = w.get("source_type", "").lower()
        source_url = w.get("source_url", "")

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
            source_title = re.sub(r'\s*\(?\s*YouTube\s*\)?\s*$', '', source_title, flags=re.IGNORECASE)
            wisdom_excerpt = w.get("wisdom_original", "")[:100]

            tasks.append(search_youtube_url(leader_name, source_title, wisdom_excerpt))
            target_indices.append(i)

    if not tasks:
        return wisdoms

    method = "YouTube API" if config.YOUTUBE_API_KEY else "web_search"
    logger.info(f"YouTube URL 검색 시작 ({method}): {len(tasks)}개")

    semaphore = asyncio.Semaphore(3)

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

    logger.info(f"YouTube URL 검색 완료: {found_count}/{len(tasks)}개 발견")
    return wisdoms
