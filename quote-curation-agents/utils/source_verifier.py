"""
출처(source) 검증 유틸리티.

웹 검색을 통해 명언의 source 필드가 실제 존재하는 출처인지,
해당 인물이 실제로 그 출처에서 발언/저술한 것이 맞는지 검증한다.

검증 대상:
- "Amazon Shareholder Letter 2011" → Jeff Bezos가 실제로 2011년 주주서한을 썼는지
- "CNBC Interview with Becky Quick" → 실제 인터뷰가 존재하는지
- "Principles: Life and Work" → Ray Dalio가 실제로 이 책을 썼는지
"""

import asyncio
import logging
import re
from typing import Optional

import anthropic

import config

logger = logging.getLogger("quote-agents.source_verifier")

WEB_SEARCH_TOOL = {
    "type": "web_search_20250305",
    "name": "web_search",
    "max_uses": 3,
}


async def verify_source(
    leader_name_en: str,
    source: str,
    wisdom_original: str = "",
    source_making_date: str = "",
) -> dict:
    """
    웹 검색으로 출처(source)가 실제 존재하고 해당 인물의 것인지 검증한다.

    Args:
        leader_name_en: 발언자 영문 이름 (예: "Jeff Bezos")
        source: 출처명 (예: "Amazon Shareholder Letter 2011")
        wisdom_original: 명언 원문 일부 (검증 보조용)
        source_making_date: 출처 날짜 (검증 보조용)

    Returns:
        {
            "source": str,
            "leader": str,
            "status": "VERIFIED" | "UNVERIFIED" | "SUSPICIOUS",
            "confidence": float (0.0~1.0),
            "reason": str,
            "suggested_correction": str | None,
        }
    """
    result = {
        "source": source,
        "leader": leader_name_en,
        "status": "UNVERIFIED",
        "confidence": 0.0,
        "reason": "",
        "suggested_correction": None,
    }

    if not source or not leader_name_en:
        result["reason"] = "출처 또는 발언자 정보 없음"
        return result

    # 도서 출처는 검증 스킵 (저자와 책 제목은 LLM이 이미 잘 알고 있음)
    source_lower = source.lower()
    if _is_well_known_book(leader_name_en, source):
        result["status"] = "VERIFIED"
        result["confidence"] = 0.9
        result["reason"] = "잘 알려진 도서 출처"
        return result

    client = anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)

    # 검색 쿼리 구성
    date_hint = f" {source_making_date}" if source_making_date else ""
    excerpt = wisdom_original[:150] if wisdom_original else ""

    prompt = (
        f"I need to verify whether the following source attribution is accurate.\n\n"
        f"Speaker/Author: {leader_name_en}\n"
        f"Claimed Source: {source}{date_hint}\n"
    )
    if excerpt:
        prompt += f"Quote excerpt: \"{excerpt}...\"\n"

    prompt += (
        f"\nPlease search the web to verify:\n"
        f"1. Does this source actually exist? (e.g., was there really an \"{source}\"?)\n"
        f"2. Is {leader_name_en} actually associated with this source?\n"
        f"3. If the source exists but details are wrong (e.g., wrong year, wrong event name), "
        f"what is the correct information?\n\n"
        f"Respond in this exact JSON format:\n"
        f'{{\n'
        f'  "verified": true/false,\n'
        f'  "confidence": 0.0 to 1.0,\n'
        f'  "reason": "brief explanation",\n'
        f'  "correct_source": "corrected source name if different, or null"\n'
        f'}}\n'
    )

    try:
        response = await client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1024,
            tools=[WEB_SEARCH_TOOL],
            messages=[{"role": "user", "content": prompt}],
        )

        # 응답에서 텍스트 추출
        text = ""
        for block in response.content:
            if hasattr(block, "text") and block.text:
                text += block.text

        # JSON 파싱
        parsed = _parse_verification_response(text)
        if parsed:
            verified = parsed.get("verified", False)
            confidence = float(parsed.get("confidence", 0.5))
            reason = parsed.get("reason", "")
            correct_source = parsed.get("correct_source")

            result["confidence"] = confidence

            if verified and confidence >= 0.7:
                result["status"] = "VERIFIED"
                result["reason"] = reason
            elif verified and confidence >= 0.4:
                result["status"] = "VERIFIED"
                result["reason"] = reason
            elif not verified and confidence >= 0.7:
                result["status"] = "SUSPICIOUS"
                result["reason"] = reason
            else:
                result["status"] = "UNVERIFIED"
                result["reason"] = reason or "검증 결과 불확실"

            if correct_source and correct_source != source:
                result["suggested_correction"] = correct_source

        else:
            result["reason"] = "검증 응답 파싱 실패"

    except Exception as e:
        logger.error(f"출처 검증 오류: {leader_name_en} - {source}: {e}")
        result["reason"] = f"검증 중 오류: {e}"

    return result


async def batch_verify_sources(wisdoms: list[dict]) -> list[dict]:
    """
    명언 리스트의 source 필드를 일괄 검증한다.

    각 명언 dict에 '_source_verification' 키를 추가한다.

    Returns:
        검증 결과가 추가된 명언 리스트 (원본 수정)
    """
    tasks = []
    target_indices = []

    for i, w in enumerate(wisdoms):
        source = w.get("source", "")
        leader = w.get("leader_name_en", w.get("leader_name", ""))

        if not source or not leader:
            continue

        # 이미 검증된 항목 스킵
        if w.get("_source_verification"):
            continue

        tasks.append(
            verify_source(
                leader_name_en=leader,
                source=source,
                wisdom_original=w.get("wisdom_original", ""),
                source_making_date=w.get("source_making_date", ""),
            )
        )
        target_indices.append(i)

    if not tasks:
        return wisdoms

    logger.info(f"출처(source) 검증 시작: {len(tasks)}개")

    # 동시 실행 제한 (API rate limit 고려)
    semaphore = asyncio.Semaphore(3)

    async def limited_verify(coro):
        async with semaphore:
            return await coro

    results = await asyncio.gather(
        *[limited_verify(t) for t in tasks],
        return_exceptions=True,
    )

    verified_count = 0
    suspicious_count = 0
    unverified_count = 0

    for idx, result in zip(target_indices, results):
        if isinstance(result, Exception):
            logger.error(f"출처 검증 오류 [{idx}]: {result}")
            wisdoms[idx]["_source_verification"] = {
                "status": "UNVERIFIED",
                "confidence": 0.0,
                "reason": f"검증 오류: {result}",
                "suggested_correction": None,
            }
            unverified_count += 1
        else:
            wisdoms[idx]["_source_verification"] = result
            status = result.get("status", "UNVERIFIED")
            if status == "VERIFIED":
                verified_count += 1
            elif status == "SUSPICIOUS":
                suspicious_count += 1
            else:
                unverified_count += 1

    logger.info(
        f"출처(source) 검증 완료: 확인={verified_count}, 의심={suspicious_count}, "
        f"미확인={unverified_count} (총 {len(tasks)}개)"
    )

    return wisdoms


def _is_well_known_book(leader_name_en: str, source: str) -> bool:
    """잘 알려진 도서인지 간단히 확인한다 (API 호출 절약)."""
    known_books = {
        "jeff bezos": ["letter to shareholders", "shareholder letter"],
        "warren buffett": ["letter to shareholders", "shareholder letter", "berkshire hathaway"],
        "ray dalio": ["principles"],
        "peter drucker": ["management", "effective executive", "innovation and entrepreneurship"],
        "jim collins": ["good to great", "built to last"],
        "steven covey": ["7 habits", "seven habits"],
        "stephen covey": ["7 habits", "seven habits"],
        "elon musk": [],
        "steve jobs": ["stanford commencement"],
        "charlie munger": ["poor charlie", "almanack"],
        "benjamin graham": ["intelligent investor", "security analysis"],
        "nassim taleb": ["black swan", "antifragile", "fooled by randomness"],
        "adam smith": ["wealth of nations"],
        "sun tzu": ["art of war"],
        "niccolo machiavelli": ["the prince"],
        "marcus aurelius": ["meditations"],
        "seneca": ["letters", "moral letters"],
    }

    leader_lower = leader_name_en.lower()
    source_lower = source.lower()

    for known_leader, books in known_books.items():
        if known_leader in leader_lower:
            for book_keyword in books:
                if book_keyword in source_lower:
                    return True

    return False


def _parse_verification_response(text: str) -> Optional[dict]:
    """검증 응답에서 JSON을 추출한다."""
    import json

    if not text:
        return None

    # ```json ... ``` 블록
    json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?\s*```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # { ... } 직접 추출
    brace_start = text.find('{')
    if brace_start != -1:
        depth = 0
        for i in range(brace_start, len(text)):
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[brace_start:i + 1])
                    except json.JSONDecodeError:
                        break

    return None
