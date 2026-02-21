"""
검수자 (Reviewer) 에이전트.
정리자의 산출물을 편집 교열 검증 프로세스에 따라 검수한다.
"""

import json
import logging
from typing import Optional

from .base_agent import BaseAgent
from models.task import Task
from utils.url_validator import is_youtube_url, batch_verify_youtube_sources

logger = logging.getLogger("quote-agents.reviewer")


class Reviewer(BaseAgent):
    """명언 검수 에이전트."""

    def __init__(self):
        super().__init__(
            name="검수자",
            role="정리된 산출물을 편집 교열 검증 기준에 따라 검수",
            system_prompt_file="reviewer_system.txt",
        )

    async def run(
        self,
        wisdoms: list[dict],
        task: Optional[Task] = None,
    ) -> dict:
        self.log(f"검수 시작: {len(wisdoms)}개 명언")

        # 1단계: YouTube URL 프로그래밍 검증 (LLM 호출 전)
        yt_pre_rejects, wisdoms = await self._pre_verify_youtube_urls(wisdoms)

        if not wisdoms and yt_pre_rejects:
            self.log(f"검수 완료: YouTube URL 사전 검증으로 전체 REJECT ({len(yt_pre_rejects)}개)")
            return {"reviews": yt_pre_rejects}

        # 2단계: LLM 기반 검수
        topic = task.topic if task else "일반"
        prompt = self._build_prompt(wisdoms, topic, task)
        messages = [{"role": "user", "content": prompt}]

        try:
            raw = await self.async_call_llm(messages, temperature=0.3)
            result = self._extract_json(raw)

            if isinstance(result, list):
                reviews = result
            elif isinstance(result, dict):
                reviews = result.get("reviews", [])
            else:
                reviews = []

            # 인덱스가 없는 리뷰에 자동 인덱스 할당
            for i, r in enumerate(reviews):
                if isinstance(r, dict) and "index" not in r:
                    r["index"] = i

            # 3단계: 사전 REJECT 결과와 LLM 결과를 원래 인덱스로 병합
            merged_reviews = self._merge_reviews(yt_pre_rejects, reviews, len(yt_pre_rejects) + len(wisdoms))

            # 통계
            pass_c = sum(1 for r in merged_reviews if r.get("verdict") == "PASS")
            revise_c = sum(1 for r in merged_reviews if r.get("verdict") == "REVISE")
            reject_c = sum(1 for r in merged_reviews if r.get("verdict") == "REJECT")
            self.log(f"검수 완료: PASS={pass_c}, REVISE={revise_c}, REJECT={reject_c}")

            return {"reviews": merged_reviews}

        except Exception as e:
            logger.error(f"검수 오류: {e}")
            # 오류 시: 사전 REJECT는 유지, 나머지는 PASS
            fallback = yt_pre_rejects + [
                {"index": i, "verdict": "PASS", "issues": [], "revision_instructions": ""}
                for i in range(len(wisdoms))
            ]
            return {"reviews": fallback}

    async def _pre_verify_youtube_urls(self, wisdoms: list[dict]) -> tuple[list[dict], list[dict]]:
        """
        LLM 검수 전 YouTube URL을 프로그래밍 방식으로 검증한다.

        Returns:
            (pre_reject_reviews, remaining_wisdoms)
            - pre_reject_reviews: YouTube URL 검증 실패로 자동 REJECT된 리뷰 리스트
            - remaining_wisdoms: 검증 통과 또는 YouTube가 아닌 명언 리스트 (LLM 검수 대상)
        """
        # YouTube URL이 있는 항목 식별
        yt_indices = []
        for i, w in enumerate(wisdoms):
            source_url = w.get("source_url", "")
            source_type = w.get("source_type", "").lower()
            # 수집자에서 이미 무효 판정된 경우
            if w.get("_youtube_url_invalid"):
                yt_indices.append((i, "ALREADY_INVALID"))
            elif is_youtube_url(source_url):
                yt_indices.append((i, "NEEDS_CHECK"))
            # source에 YouTube 언급인데 URL이 비어있는 경우
            elif "youtube" in source_type or "youtube" in w.get("source", "").lower():
                if not source_url:
                    yt_indices.append((i, "MISSING_URL"))

        if not yt_indices:
            return [], wisdoms

        # 검증이 필요한 항목만 batch 검증
        needs_check = [wisdoms[i] for i, status in yt_indices if status == "NEEDS_CHECK"]
        if needs_check:
            self.log(f"YouTube URL 사전 검증: {len(needs_check)}개")
            await batch_verify_youtube_sources(needs_check)

        # 결과 분류
        pre_rejects = []
        remaining = []
        rejected_original_indices = set()

        for orig_idx, status in yt_indices:
            w = wisdoms[orig_idx]

            if status == "ALREADY_INVALID":
                reason = w.get("_youtube_rejection_reason", "YouTube URL 검증 실패")
                pre_rejects.append({
                    "original_index": orig_idx,
                    "index": len(pre_rejects),
                    "verdict": "REJECT",
                    "issues": [f"YouTube URL 검증 실패: {reason}"],
                    "revision_instructions": "",
                })
                rejected_original_indices.add(orig_idx)

            elif status == "MISSING_URL":
                pre_rejects.append({
                    "original_index": orig_idx,
                    "index": len(pre_rejects),
                    "verdict": "REJECT",
                    "issues": ["YouTube 출처인데 source_url이 비어있음"],
                    "revision_instructions": "",
                })
                rejected_original_indices.add(orig_idx)

            elif status == "NEEDS_CHECK":
                verification = w.pop("_yt_verification", None)
                if verification:
                    if not verification.get("overall_valid", False):
                        reason = verification.get("rejection_reason", "URL 검증 실패")
                        pre_rejects.append({
                            "original_index": orig_idx,
                            "index": len(pre_rejects),
                            "verdict": "REJECT",
                            "issues": [f"YouTube URL 검증 실패: {reason}"],
                            "revision_instructions": "",
                        })
                        rejected_original_indices.add(orig_idx)
                    else:
                        # 검증 통과: 상태 정보를 명언에 주입
                        if verification.get("transcript_verified") is True:
                            w["_youtube_url_status"] = "VALID"
                        elif verification.get("transcript_verified") is None:
                            w["_youtube_url_status"] = "NO_TRANSCRIPT"
                        else:
                            w["_youtube_url_status"] = "VALID"

        # REJECT되지 않은 항목들을 remaining에 추가
        for i, w in enumerate(wisdoms):
            if i not in rejected_original_indices:
                # YouTube 내부 마커 제거
                w.pop("_youtube_url_invalid", None)
                w.pop("_youtube_rejection_reason", None)
                remaining.append(w)

        if pre_rejects:
            self.log(f"YouTube URL 사전 REJECT: {len(pre_rejects)}개")

        return pre_rejects, remaining

    @staticmethod
    def _merge_reviews(
        pre_rejects: list[dict],
        llm_reviews: list[dict],
        total_count: int,
    ) -> list[dict]:
        """사전 REJECT 결과와 LLM 검수 결과를 원래 인덱스 순서로 병합한다."""
        if not pre_rejects:
            return llm_reviews

        # 원래 인덱스 기준으로 병합
        merged = []
        pre_reject_map = {r["original_index"]: r for r in pre_rejects}
        llm_idx = 0

        for orig_idx in range(total_count):
            if orig_idx in pre_reject_map:
                review = pre_reject_map[orig_idx].copy()
                review["index"] = orig_idx
                merged.append(review)
            elif llm_idx < len(llm_reviews):
                review = llm_reviews[llm_idx].copy()
                review["index"] = orig_idx
                merged.append(review)
                llm_idx += 1

        return merged

    def get_passed(self, wisdoms: list[dict], reviews: list[dict]) -> list[dict]:
        passed = []
        for i, review in enumerate(reviews):
            if i < len(wisdoms) and review.get("verdict") == "PASS":
                passed.append(wisdoms[i])
        return passed

    def get_revise_items(self, wisdoms: list[dict], reviews: list[dict]) -> tuple:
        revise_w, revise_i = [], []
        for i, review in enumerate(reviews):
            if i < len(wisdoms) and review.get("verdict") == "REVISE":
                revise_w.append(wisdoms[i])
                revise_i.append(review.get("revision_instructions", "수정 필요"))
        return revise_w, revise_i

    def has_revise_items(self, reviews: list[dict]) -> bool:
        return any(r.get("verdict") == "REVISE" for r in reviews)

    def _build_prompt(self, wisdoms: list[dict], topic: str, task: Optional[Task]) -> str:
        parts = [f"아래 {len(wisdoms)}개 명언을 검수해줘.\n"]
        parts.append(f"■ 주제: {topic}")
        if task and task.leaders:
            parts.append(f"■ 인물: {', '.join(task.leaders)}")
        if task:
            parts.append(f"■ 요청 개수: {task.count}개")

        parts.append(f"""
■ 검수 체크리스트:
1. ⚠️ 1개 명언 = 1개 주제 (최우선): 문장을 하나씩 읽고 A-A-B-B-A처럼 다른 주제가 섞여 있으면 REVISE → "다른 주제 문장 제거하고 1주제만 남길 것"
2. 주제 '{topic}' 적합성
3. 출처 명확성 (구체적 출처명 필수)
4. YouTube URL 검증: _youtube_url_status 필드 확인. "INVALID"→REJECT, "TRANSCRIPT_MISMATCH"→REJECT, "VALID"→통과, "NO_TRANSCRIPT"→URL 유효하나 트랜스크립트 미확인이므로 다른 기준으로 검수. YouTube 출처인데 source_url이 비어있으면→REJECT
5. 비퍼블릭 도메인 도서: 원문 2문장, 번역 재구성 의역
6. 원문 길이: 목표 5~6문장이지만 1주제 유지가 우선. 1주제 유지 위해 3~4문장으로 축소한 경우는 PASS
7. 해설에 한국 특정 인물 실명이 있으면 REVISE → "실명 대신 일반 표현으로 변경" (단, 퍼블릭 도메인 인물과 원문 저자(leader_name) 본인은 예외)
8. 번역 품질, 어투('-다' 체), 해설 품질(200~400자, 4~6문장)
9. 도서 출처 한국어 제목: 한국어 번역본이 있는 도서인데 영어 원제만 표기된 경우 → REVISE "한국어 번역 제목으로 변경하고 영어 원제를 괄호로 병기"
10. 카테고리/mood 유효성

■ 카테고리: business, marketing, leadership, self-improvement, philosophy, wealth, creativity, psychology, relationships
■ Mood: execution, growth, challenge, relationships, motivation, new-goal, comfort, contemplation, anxiety, habits, meaning

■ 명언 데이터:
{json.dumps(wisdoms, ensure_ascii=False, separators=(',', ':'))}

반드시 아래 JSON 형식으로만 응답해라:
```json
{{
  "reviews": [
    {{
      "index": 0,
      "verdict": "PASS",
      "issues": [],
      "revision_instructions": ""
    }}
  ]
}}
```
verdict는 "PASS", "REVISE", "REJECT" 중 하나. 모든 명언에 대해 빠짐없이 판정해라.""")
        return "\n".join(parts)
