"""
최종 확인자 (Final Validator) 에이전트.
전체 산출물이 사용자 요구사항에 부합하는지 최종 확인한다.
"""

import json
import logging
from typing import Optional

from .base_agent import BaseAgent
from models.task import Task

logger = logging.getLogger("wisdom-agents.final_validator")


class FinalValidator(BaseAgent):
    """최종 확인 에이전트."""

    def __init__(self):
        super().__init__(
            name="최종확인자",
            role="전체 산출물이 사용자 요구사항에 부합하는지 최종 확인",
            system_prompt_file="final_validator_system.txt",
        )

    async def run(
        self,
        wisdoms: list[dict],
        task: Task,
    ) -> dict:
        """
        전체 산출물을 최종 확인한다.

        Args:
            wisdoms: 검수 통과한 명언 리스트
            task: 원래 태스크 정보

        Returns:
            {
                "action": "APPROVED" | "RETURN_TO_REVIEWER" | "RETURN_TO_COLLECTOR_VIA_ORCHESTRATOR",
                "final_wisdoms": [...],        # APPROVED일 때
                "problematic_items": [int],    # RETURN_TO_REVIEWER일 때
                "reason": str,
                ...
            }
        """
        self.log(f"최종 확인 시작: {len(wisdoms)}개 명언, 요청={task.count}개")

        user_message = self._build_validation_prompt(wisdoms, task)
        messages = [{"role": "user", "content": user_message}]

        try:
            raw_response = self.call_llm(messages, temperature=0.3)
            result = self._extract_json(raw_response)

            action = result.get("action", "APPROVED")

            if action == "APPROVED":
                final_indices = result.get("final_wisdoms_indices", list(range(len(wisdoms))))
                removed_indices = result.get("removed_indices", [])
                removed_reasons = result.get("removed_reasons", {})

                final_wisdoms = [
                    wisdoms[i] for i in final_indices if i < len(wisdoms)
                ]

                if removed_indices:
                    self.log(
                        f"최종 확인 완료: {len(final_wisdoms)}개 통과, "
                        f"{len(removed_indices)}개 제거"
                    )
                else:
                    self.log(f"최종 확인 완료: {len(final_wisdoms)}개 전체 통과")

                return {
                    "action": "APPROVED",
                    "final_wisdoms": final_wisdoms,
                    "removed_count": len(removed_indices),
                    "removed_reasons": removed_reasons,
                }

            elif action == "RETURN_TO_REVIEWER":
                self.log(f"검수자 반려: {result.get('reason', 'N/A')}")
                return {
                    "action": "RETURN_TO_REVIEWER",
                    "problematic_items": result.get("problematic_items", []),
                    "reason": result.get("reason", ""),
                    "instructions": result.get("instructions", ""),
                    "passing_subset": [
                        wisdoms[i] for i in range(len(wisdoms))
                        if i not in result.get("problematic_items", [])
                    ],
                }

            elif action == "RETURN_TO_COLLECTOR_VIA_ORCHESTRATOR":
                passed_indices = result.get("passed_wisdoms_indices", [])
                passed_wisdoms = [
                    wisdoms[i] for i in passed_indices if i < len(wisdoms)
                ]

                self.log(
                    f"수집 재시작 요청: 통과 {len(passed_wisdoms)}개, "
                    f"부족 {result.get('additional_needed', '?')}개"
                )

                return {
                    "action": "RETURN_TO_COLLECTOR_VIA_ORCHESTRATOR",
                    "reason": result.get("reason", ""),
                    "passed_wisdoms": passed_wisdoms,
                    "additional_needed": result.get("additional_needed", 0),
                    "topic": task.topic,
                }

            else:
                # 알 수 없는 액션 → APPROVED 처리
                return {
                    "action": "APPROVED",
                    "final_wisdoms": wisdoms,
                    "removed_count": 0,
                    "removed_reasons": {},
                }

        except Exception as e:
            logger.error(f"최종 확인 중 오류 발생: {e}")
            return {
                "action": "APPROVED",
                "final_wisdoms": wisdoms,
                "removed_count": 0,
                "removed_reasons": {},
            }

    def _build_validation_prompt(self, wisdoms: list[dict], task: Task) -> str:
        """최종 확인 프롬프트를 구성한다."""
        prompt_parts = [
            f"아래 명언 {len(wisdoms)}개를 최종 확인해줘.\n",
            f"■ 원래 사용자 요청:",
            f"  - 주제: {task.topic}",
        ]

        if task.leaders:
            prompt_parts.append(f"  - 인물: {', '.join(task.leaders)}")

        prompt_parts.append(f"  - 요청 개수: {task.count}개")

        if task.categories:
            prompt_parts.append(f"  - 카테고리: {', '.join(task.categories)}")

        if task.constraints:
            prompt_parts.append(f"  - 기타 조건: {task.constraints}")

        prompt_parts.append(f"""
■ 최종 확인 체크리스트:

1. 요구사항 일치성
   - 주제 '{task.topic}'과 모든 명언이 일치하는가?
   - 요청 인물의 명언이 포함되어 있는가?
   - 요청 개수 {task.count}개 충족 여부

2. 품질 일관성
   - 모든 명언의 품질이 일정한가?
   - 뒤쪽 명언에서 주제가 벗어나지 않았는가?

3. 형식 통일성
   - 필수 컬럼이 모두 채워져 있는가?
   - 카테고리/mood 값이 유효한가?

4. 이상 항목 제거
   - 중복 명언 → 하나만 남기고 제거
   - 요구사항에 벗어난 내용 → 제거
   - 누구나 이해 가능하고 실용적인지 확인

■ 판정 기준:
- 통과 비율 70% 이상 → APPROVED
- 품질/적합성 문제 있으나 수정 가능 → RETURN_TO_REVIEWER
- 통과 비율 70% 미만 → RETURN_TO_COLLECTOR_VIA_ORCHESTRATOR

■ 카테고리 유효값: business, marketing, leadership, self-improvement, philosophy, wealth, creativity, psychology, relationships
■ Mood 유효값: execution, growth, challenge, relationships, motivation, new-goal, comfort, contemplation, anxiety, habits, meaning

■ 명언 데이터 ({len(wisdoms)}개):
""")

        prompt_parts.append(json.dumps(wisdoms, ensure_ascii=False, indent=2))

        prompt_parts.append(f"""
아래 형식 중 하나로 응답해라:

1. 모두 통과:
{{
  "action": "APPROVED",
  "final_wisdoms_indices": [통과한 명언의 인덱스 리스트],
  "removed_indices": [제거된 명언의 인덱스 리스트],
  "removed_reasons": {{"인덱스": "제거 사유"}}
}}

2. 품질/적합성 문제 → 검수자에게 반려:
{{
  "action": "RETURN_TO_REVIEWER",
  "problematic_items": [문제 명언 인덱스],
  "reason": "반려 사유",
  "instructions": "검수자에게 전달할 지시"
}}

3. 수량 크게 부족 (통과 비율 70% 미만) → 수집부터 다시:
{{
  "action": "RETURN_TO_COLLECTOR_VIA_ORCHESTRATOR",
  "reason": "반려 사유",
  "passed_wisdoms_indices": [통과한 인덱스],
  "additional_needed": 부족 수량,
  "topic": "{task.topic}"
}}
""")

        return "\n".join(prompt_parts)
