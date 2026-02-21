"""
수집자 (Collector) 에이전트.
다양한 소스에서 명언 원문과 메타데이터를 수집한다.
"""

import asyncio
import json
import logging
import traceback
from typing import Optional

from .base_agent import BaseAgent
from models.task import Task
from utils.url_validator import is_youtube_url, batch_verify_youtube_sources

logger = logging.getLogger("quote-agents.collector")


class Collector(BaseAgent):
    """명언 수집 에이전트."""

    def __init__(self):
        super().__init__(
            name="수집자",
            role="다양한 소스에서 명언 원문과 메타데이터를 수집",
            system_prompt_file="collector_system.txt",
        )
        self._excluded_wisdoms: list[dict] = []

    async def run(
        self,
        task: Task,
        exclude: Optional[list] = None,
        target: Optional[int] = None,
        supplement_request: Optional[str] = None,
    ) -> list[dict]:
        if exclude:
            self._excluded_wisdoms = exclude
        if target is None:
            target = int(task.count * 2)

        self.log(f"수집 시작: 주제='{task.topic}', 인물={task.leaders or '자동'}, 목표={target}개")

        # 병렬 수집: target을 2개 청크로 나눠 동시에 요청
        if target >= 6:
            chunk_a = target // 2
            chunk_b = target - chunk_a
            self.log(f"병렬 수집: {chunk_a}개 + {chunk_b}개 동시 요청")

            results = await asyncio.gather(
                self._async_collect_from_knowledge(task, chunk_a, supplement_request),
                self._async_collect_from_knowledge(task, chunk_b, supplement_request),
            )
            collected = results[0] + results[1]

            # 중복 제거 (원문 기준)
            seen = set()
            deduped = []
            for item in collected:
                key = item.get("wisdom_original", "").strip().lower()
                if key and key not in seen:
                    seen.add(key)
                    deduped.append(item)
            collected = deduped[:target]
        else:
            collected = await self._async_collect_from_knowledge(task, target, supplement_request)

        if not collected:
            self.log("수집 실패: 0개")
            return collected

        self.log(f"수집 완료: {len(collected)}개")

        # YouTube URL 검증: 접근 불가 URL은 비우고, 트랜스크립트 불일치는 경고
        yt_count = sum(1 for c in collected if is_youtube_url(c.get("source_url", "")))
        if yt_count > 0:
            self.log(f"YouTube URL 검증 시작: {yt_count}개")
            collected = await batch_verify_youtube_sources(collected)
            invalidated = 0
            for item in collected:
                verification = item.pop("_yt_verification", None)
                if verification and not verification.get("overall_valid", True):
                    reason = verification.get("rejection_reason", "URL 검증 실패")
                    self.log(f"  YouTube URL 무효: {item.get('source_url', '')} → {reason}")
                    item["source_url"] = ""
                    item["_youtube_url_invalid"] = True
                    item["_youtube_rejection_reason"] = reason
                    invalidated += 1
            self.log(f"YouTube URL 검증 완료: {yt_count - invalidated}/{yt_count}개 유효")

        return collected

    async def _async_collect_from_knowledge(
        self, task: Task, target: int, supplement_request: Optional[str]
    ) -> list[dict]:
        """비동기 LLM 지식 기반으로 명언을 수집한다."""
        prompt = self._build_prompt(task, target, supplement_request)
        messages = [{"role": "user", "content": prompt}]

        try:
            self.log(f"Claude API 비동기 호출 중... (목표: {target}개)")
            raw = await self.async_call_llm(messages, temperature=0.7)
            self.log(f"API 응답 수신: {len(raw)}자")

            if not raw.strip():
                self.log("경고: 빈 응답")
                return []

            return self._parse_collected(raw, target)

        except Exception as e:
            self.log(f"오류: {e}")
            traceback.print_exc()
            return []

    def _collect_from_knowledge(
        self, task: Task, target: int, supplement_request: Optional[str]
    ) -> list[dict]:
        """LLM 지식 기반으로 명언을 수집한다 (동기 폴백)."""
        prompt = self._build_prompt(task, target, supplement_request)
        messages = [{"role": "user", "content": prompt}]

        try:
            self.log("Claude API 호출 중...")
            raw = self.call_llm(messages, temperature=0.7)
            self.log(f"API 응답 수신: {len(raw)}자")

            if not raw.strip():
                self.log("경고: 빈 응답")
                return []

            return self._parse_collected(raw, target)

        except Exception as e:
            self.log(f"오류: {e}")
            traceback.print_exc()
            return []

    def _parse_collected(self, raw_response: str, target: int) -> list[dict]:
        """LLM 응답에서 수집 데이터를 추출한다."""
        try:
            result = self._extract_json(raw_response)
        except ValueError as e:
            self.log(f"JSON 추출 실패: {e}")
            self.log(f"응답 앞부분: {raw_response[:500]}")
            return []

        # dict → 내부 리스트 추출
        if isinstance(result, dict):
            for key in ("wisdoms", "results", "quotes", "data"):
                if key in result and isinstance(result[key], list):
                    result = result[key]
                    break
            else:
                result = [result]

        if not isinstance(result, list):
            self.log(f"예상치 못한 결과 타입: {type(result)}")
            return []

        # 검증 및 기본값 채우기
        validated = []
        for item in result:
            if not isinstance(item, dict):
                continue
            if not item.get("wisdom_original"):
                continue
            if not item.get("leader_name") and not item.get("leader_name_en"):
                continue
            item.setdefault("leader_name", item.get("leader_name_en", ""))
            item.setdefault("leader_name_en", item.get("leader_name", ""))
            item.setdefault("leader_title", "")
            item.setdefault("source", "")
            item.setdefault("source_type", "기타")
            item.setdefault("source_url", "")
            item.setdefault("source_making_date", "")
            item.setdefault("is_public_domain", False)
            validated.append(item)

        self.log(f"파싱 결과: {len(validated)}개 유효")
        return validated[:target]

    def _build_prompt(
        self, task: Task, target: int, supplement_request: Optional[str]
    ) -> str:
        parts = []
        parts.append(f"너는 명언 수집 전문가야. 아래 조건에 맞는 명언을 정확히 {target}개 수집해줘.")
        parts.append(f"반드시 {target}개를 모두 JSON 배열로 응답해야 한다.\n")
        parts.append(f"■ 주제: {task.topic}")

        if task.leaders:
            parts.append(f"■ 인물: {', '.join(task.leaders)}")
        else:
            parts.append("■ 인물: 해당 주제의 세계적 대가들 (자동 탐색)")

        if task.categories:
            parts.append(f"■ 카테고리: {', '.join(task.categories)}")
        if task.constraints:
            parts.append(f"■ 기타 조건: {task.constraints}")

        if supplement_request:
            parts.append(f"\n⚠️ 보완 수집: {supplement_request}")

        if self._excluded_wisdoms:
            parts.append("\n⚠️ 중복 방지 (아래와 다른 명언을 수집):")
            for w in self._excluded_wisdoms[:10]:
                if isinstance(w, dict):
                    name = w.get("leader_name_en", w.get("leader_name", ""))
                    orig = w.get("wisdom_original", "")[:40]
                    parts.append(f"  - {name}: {orig}...")

        parts.append(f"""
■ 수집 규칙:
- 출처가 명확한 명언만 수집
- 원문은 영어로 5~6문장 필수. 비퍼블릭 도메인 도서만 최대 2문장
- 4문장 이하 명언은 반드시 원문의 앞뒤 문장을 찾아 5문장 이상으로 만들어라
- 단, 1명언 1주제를 지키기에 5문장이 너무 길다면 1주제를 유지할 수 있는 최대 문장 수로 축소 (최소 3문장)
- 주제 '{task.topic}'과 관련성이 높은 것만

다른 설명 없이 아래 형식의 JSON 배열만 출력해라:

[
  {{
    "leader_name": "한글 이름",
    "leader_name_en": "English Name",
    "leader_title": "직함 또는 직업",
    "wisdom_original": "영어 원문 (5~6문장, 비퍼블릭 도메인 도서만 최대 2문장)",
    "source": "출처명 (책제목, 연설명 등)",
    "source_type": "도서",
    "source_url": "https://example.com",
    "source_making_date": "",
    "is_public_domain": false
  }},
  ...총 {target}개...
]""")

        return "\n".join(parts)

    def receive_feedback(self, feedback: dict):
        self._excluded_wisdoms.extend(feedback.get("existing_wisdoms", []))
        self.log(f"피드백 수신: {feedback.get('reason', 'N/A')}")
