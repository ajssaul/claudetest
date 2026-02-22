"""
검수자 (Reviewer) 에이전트.
정리자의 산출물을 편집 교열 검증 프로세스에 따라 검수한다.
"""

import json
import logging
from typing import Optional

from .base_agent import BaseAgent
from models.task import Task
from utils.url_validator import is_youtube_url, batch_verify_web_sources

logger = logging.getLogger("wisdom-agents.reviewer")


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

        # 0단계: 웹 URL 프로그래밍 검증 (LLM 호출 전)
        web_pre_rejects, wisdoms = await self._pre_verify_web_urls(wisdoms)

        # 0.5단계: 출처명(source) 검증 결과 기반 사전 REJECT
        source_pre_rejects, wisdoms = self._pre_check_source_status(wisdoms)

        all_pre_rejects = web_pre_rejects + source_pre_rejects

        if not wisdoms and all_pre_rejects:
            self.log(f"검수 완료: 사전 검증으로 전체 REJECT ({len(all_pre_rejects)}개)")
            return {"reviews": all_pre_rejects}

        # 1단계: LLM 기반 검수
        topic = task.topic if task else "일반"
        prompt = self._build_prompt(wisdoms, topic, task)
        messages = [{"role": "user", "content": prompt}]

        try:
            raw = self.call_llm(messages, temperature=0.3)
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

            # 사전 REJECT 결과와 LLM 결과 병합
            merged_reviews = self._merge_reviews(all_pre_rejects, reviews, len(all_pre_rejects) + len(wisdoms))

            # 통계
            pass_c = sum(1 for r in merged_reviews if r.get("verdict") == "PASS")
            revise_c = sum(1 for r in merged_reviews if r.get("verdict") == "REVISE")
            reject_c = sum(1 for r in merged_reviews if r.get("verdict") == "REJECT")
            self.log(f"검수 완료: PASS={pass_c}, REVISE={revise_c}, REJECT={reject_c}")

            return {"reviews": merged_reviews}

        except Exception as e:
            logger.error(f"검수 오류: {e}")
            # 오류 시: 사전 REJECT는 유지, 나머지는 PASS
            fallback = all_pre_rejects + [
                {"index": i, "verdict": "PASS", "issues": [], "revision_instructions": ""}
                for i in range(len(wisdoms))
            ]
            return {"reviews": fallback}

    async def _pre_verify_web_urls(self, wisdoms: list[dict]) -> tuple[list[dict], list[dict]]:
        """
        LLM 검수 전 웹 URL을 프로그래밍 방식으로 검증한다.

        Returns:
            (pre_reject_reviews, remaining_wisdoms)
        """
        web_indices = []
        for i, w in enumerate(wisdoms):
            source_url = w.get("source_url", "")
            web_url_status = w.get("_web_url_status", "")

            if web_url_status == "INACCESSIBLE":
                web_indices.append((i, "ALREADY_INACCESSIBLE"))
            elif web_url_status == "CONTENT_MISMATCH":
                web_indices.append((i, "ALREADY_MISMATCH"))
            elif source_url and source_url.startswith("http") and not is_youtube_url(source_url):
                web_indices.append((i, "NEEDS_CHECK"))

        if not web_indices:
            return [], wisdoms

        needs_check = [wisdoms[i] for i, status in web_indices if status == "NEEDS_CHECK"]
        if needs_check:
            self.log(f"웹 URL 사전 검증: {len(needs_check)}개")
            await batch_verify_web_sources(needs_check)

        pre_rejects = []
        remaining = []
        rejected_original_indices = set()

        for orig_idx, status in web_indices:
            w = wisdoms[orig_idx]

            if status == "ALREADY_INACCESSIBLE":
                error = w.get("_web_url_error", "URL 접근 불가")
                pre_rejects.append({
                    "original_index": orig_idx,
                    "index": len(pre_rejects),
                    "verdict": "REJECT",
                    "issues": [f"웹 URL 접근 불가: {error}"],
                    "revision_instructions": "",
                })
                rejected_original_indices.add(orig_idx)

            elif status == "ALREADY_MISMATCH":
                error = w.get("_web_url_error", "페이지 내용과 명언 출처 불일치")
                pre_rejects.append({
                    "original_index": orig_idx,
                    "index": len(pre_rejects),
                    "verdict": "REJECT",
                    "issues": [f"웹 URL 내용 불일치: {error}"],
                    "revision_instructions": "",
                })
                rejected_original_indices.add(orig_idx)

            elif status == "NEEDS_CHECK":
                verification = w.pop("_web_url_verification", None)
                if verification:
                    overall_status = verification.get("overall_status", "VALID")
                    if overall_status == "INACCESSIBLE":
                        error = verification.get("error", "URL 접근 불가")
                        pre_rejects.append({
                            "original_index": orig_idx,
                            "index": len(pre_rejects),
                            "verdict": "REJECT",
                            "issues": [f"웹 URL 접근 불가: {error}"],
                            "revision_instructions": "",
                        })
                        rejected_original_indices.add(orig_idx)
                    elif overall_status == "CONTENT_MISMATCH":
                        error = verification.get("error", "내용 불일치")
                        pre_rejects.append({
                            "original_index": orig_idx,
                            "index": len(pre_rejects),
                            "verdict": "REJECT",
                            "issues": [f"웹 URL 내용 불일치: {error}"],
                            "revision_instructions": "",
                        })
                        rejected_original_indices.add(orig_idx)
                    else:
                        w["_web_url_status"] = "VALID"

        for i, w in enumerate(wisdoms):
            if i not in rejected_original_indices:
                w.pop("_web_url_status", None)
                w.pop("_web_url_error", None)
                remaining.append(w)

        if pre_rejects:
            self.log(f"웹 URL 사전 REJECT: {len(pre_rejects)}개")

        return pre_rejects, remaining

    def _pre_check_source_status(self, wisdoms: list[dict]) -> tuple[list[dict], list[dict]]:
        """
        수집자에서 설정한 _source_status를 기반으로 SUSPICIOUS 출처를 사전 REJECT한다.

        Returns:
            (pre_reject_reviews, remaining_wisdoms)
        """
        pre_rejects = []
        remaining = []
        rejected_indices = set()

        for i, w in enumerate(wisdoms):
            source_status = w.get("_source_status", "")
            if source_status == "SUSPICIOUS":
                issue = w.get("_source_issue", "출처 검증 실패")
                pre_rejects.append({
                    "original_index": i,
                    "index": len(pre_rejects),
                    "verdict": "REJECT",
                    "issues": [f"출처 검증 실패: {issue}"],
                    "revision_instructions": "",
                })
                rejected_indices.add(i)

        for i, w in enumerate(wisdoms):
            if i not in rejected_indices:
                remaining.append(w)

        if pre_rejects:
            self.log(f"출처(source) 사전 REJECT: {len(pre_rejects)}개")

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
1. 1개 명언 = 1개 주제
2. 주제 '{topic}' 적합성
3. 출처 명확성 (구체적 출처명 필수)
4. 웹 URL 검증: _web_url_status 필드 확인. "INACCESSIBLE"→REJECT (URL 접근 불가), "CONTENT_MISMATCH"→REJECT (URL은 열리나 발언자 관련 내용 없음), "VALID"→통과
5. 출처명(source) 검증: _source_status 필드 확인. "SUSPICIOUS"→REJECT (출처가 실존하지 않거나 인물과 무관), "VERIFIED"→통과 (단, _source_suggested_correction이 있으면 REVISE "출처명을 수정된 값으로 변경"), "UNVERIFIED"→출처가 구체적이면 PASS 가능
6. 비퍼블릭 도메인 도서: 원문 2문장, 번역 재구성 의역, 해설 4~5문장
7. 번역 품질, 어투('-다' 체), 해설 품질(150~250자)
8. 카테고리/mood 유효성

■ 카테고리: business, marketing, leadership, self-improvement, philosophy, wealth, creativity, psychology, relationships
■ Mood: execution, growth, challenge, relationships, motivation, new-goal, comfort, contemplation, anxiety, habits, meaning

■ 명언 데이터:
{json.dumps(wisdoms, ensure_ascii=False, indent=2)}

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
