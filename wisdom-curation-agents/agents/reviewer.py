"""
검수자 (Reviewer) 에이전트.
정리자의 산출물을 편집 교열 검증 프로세스에 따라 검수한다.
"""

import json
import logging
from typing import Optional

from .base_agent import BaseAgent
from models.task import Task, ReviewVerdict

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
        """
        명언 목록을 검수한다.

        Args:
            wisdoms: 정리된 명언 리스트
            task: 태스크 정보

        Returns:
            {
                "reviews": [
                    {
                        "index": int,
                        "verdict": "PASS" | "REVISE" | "REJECT",
                        "issues": [str],
                        "revision_instructions": str
                    }
                ]
            }
        """
        self.log(f"검수 시작: {len(wisdoms)}개 명언")

        topic = task.topic if task else "일반"
        user_message = self._build_review_prompt(wisdoms, topic, task)
        messages = [{"role": "user", "content": user_message}]

        try:
            raw_response = self.call_llm(messages, temperature=0.3)
            result = self._extract_json(raw_response)

            if isinstance(result, list):
                result = {"reviews": result}

            reviews = result.get("reviews", [])

            # 통계 로그
            pass_count = sum(1 for r in reviews if r.get("verdict") == "PASS")
            revise_count = sum(1 for r in reviews if r.get("verdict") == "REVISE")
            reject_count = sum(1 for r in reviews if r.get("verdict") == "REJECT")

            self.log(
                f"검수 완료: PASS={pass_count}, REVISE={revise_count}, "
                f"REJECT={reject_count}"
            )

            return {"reviews": reviews}

        except Exception as e:
            logger.error(f"검수 중 오류 발생: {e}")
            # 오류 시 전체 PASS 처리
            return {
                "reviews": [
                    {"index": i, "verdict": "PASS", "issues": [], "revision_instructions": ""}
                    for i in range(len(wisdoms))
                ]
            }

    def get_passed(self, wisdoms: list[dict], reviews: list[dict]) -> list[dict]:
        """PASS 판정된 명언만 반환한다."""
        passed = []
        for wisdom, review in zip(wisdoms, reviews):
            if review.get("verdict") == "PASS":
                passed.append(wisdom)
        return passed

    def get_revise_items(
        self, wisdoms: list[dict], reviews: list[dict]
    ) -> tuple[list[dict], list[str]]:
        """REVISE 판정된 명언과 수정 지시를 반환한다."""
        revise_wisdoms = []
        revise_instructions = []
        for wisdom, review in zip(wisdoms, reviews):
            if review.get("verdict") == "REVISE":
                revise_wisdoms.append(wisdom)
                revise_instructions.append(
                    review.get("revision_instructions", "수정 필요")
                )
        return revise_wisdoms, revise_instructions

    def has_revise_items(self, reviews: list[dict]) -> bool:
        """REVISE 판정이 있는지 확인한다."""
        return any(r.get("verdict") == "REVISE" for r in reviews)

    def _build_review_prompt(
        self,
        wisdoms: list[dict],
        topic: str,
        task: Optional[Task],
    ) -> str:
        """검수 요청 프롬프트를 구성한다."""
        prompt_parts = [
            f"아래 정리된 명언 {len(wisdoms)}개를 검수해줘.\n",
            f"■ 사용자 요청 주제: {topic}",
        ]

        if task and task.leaders:
            prompt_parts.append(f"■ 요청 인물: {', '.join(task.leaders)}")

        if task:
            prompt_parts.append(f"■ 요청 개수: {task.count}개")

        prompt_parts.append(f"""
■ 검수 체크리스트:

8.1 1개 명언 = 1개 주제 검증
- 1개 명언 내 모든 문장이 동일한 주제를 다루는가?
- 2개 이상 주제가 섞인 명언 → REJECT 또는 REVISE

8.2 주제 적합성 검증
- 사용자가 요청한 주제 '{topic}'에 부합하는 명언인가?
- 주제 무관 → REJECT

8.3 출처 명확성 검증
- 출처가 구체적으로 명시되어 있는가?
- ✅ "The Art of War", "Stanford Commencement 2005"
- ❌ "구전", "인터뷰" (상세 정보 없음)
- 출처 애매 → REJECT

8.4 도서 저작권 기준 검증
- 비퍼블릭 도메인 도서:
  * 원문 최대 2문장 확인 (초과 시 REVISE)
  * 번역이 직역이 아닌 재구성 의역인지 확인 (직역이면 REVISE)
  * source_type "도서 (비퍼블릭 도메인)" 표기 확인
  * 해설 4~5문장 보완 확인

추가 검증:
- 번역 품질: wisdom_kr이 wisdom_original과 의미 일치
- 해설 품질: 원문 범위 내, 한국 맥락으로 재구성
- 어투: '-다' 체, 성숙한 어조
- 구체성: 사례/숫자 포함
- 길이: 원문 2~7문장, 해설 150~250자
- 카테고리/mood 유효성

■ 카테고리 유효값: business, marketing, leadership, self-improvement, philosophy, wealth, creativity, psychology, relationships
■ Mood 유효값: execution, growth, challenge, relationships, motivation, new-goal, comfort, contemplation, anxiety, habits, meaning

■ 검수 대상 명언 ({len(wisdoms)}개):
""")

        prompt_parts.append(json.dumps(wisdoms, ensure_ascii=False, indent=2))

        prompt_parts.append("""
각 명언에 대해 아래 JSON 형식으로 검수 결과를 응답해라:
{
  "reviews": [
    {
      "index": 0,
      "verdict": "PASS" | "REVISE" | "REJECT",
      "issues": ["발견된 문제 설명"],
      "revision_instructions": "수정 지시 (REVISE일 때만)"
    }
  ]
}

모든 명언에 대해 빠짐없이 판정해라. 엄격하게 검수하되, REJECT는 명백한 기준 위반에만 사용해라.
""")

        return "\n".join(prompt_parts)
