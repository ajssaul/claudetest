"""
검수자 (Reviewer) 에이전트.
정리자의 산출물을 편집 교열 검증 프로세스에 따라 검수한다.
"""

import json
import logging
from typing import Optional

from .base_agent import BaseAgent
from models.task import Task

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

            # 통계
            pass_c = sum(1 for r in reviews if r.get("verdict") == "PASS")
            revise_c = sum(1 for r in reviews if r.get("verdict") == "REVISE")
            reject_c = sum(1 for r in reviews if r.get("verdict") == "REJECT")
            self.log(f"검수 완료: PASS={pass_c}, REVISE={revise_c}, REJECT={reject_c}")

            return {"reviews": reviews}

        except Exception as e:
            logger.error(f"검수 오류: {e}")
            # 오류 시 전체 PASS
            return {
                "reviews": [
                    {"index": i, "verdict": "PASS", "issues": [], "revision_instructions": ""}
                    for i in range(len(wisdoms))
                ]
            }

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
4. 비퍼블릭 도메인 도서: 원문 2문장, 번역 재구성 의역
5. 원문 길이: 목표 5~6문장이지만 1주제 유지가 우선. 1주제 유지 위해 3~4문장으로 축소한 경우는 PASS
6. 해설에 한국 특정 인물 실명이 있으면 REVISE → "실명 대신 일반 표현으로 변경" (단, 퍼블릭 도메인 인물과 원문 저자(leader_name) 본인은 예외)
7. 번역 품질, 어투('-다' 체), 해설 품질(200~400자, 4~6문장)
8. 도서 출처 한국어 제목: 한국어 번역본이 있는 도서인데 영어 원제만 표기된 경우 → REVISE "한국어 번역 제목으로 변경하고 영어 원제를 괄호로 병기"
9. 카테고리/mood 유효성

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
