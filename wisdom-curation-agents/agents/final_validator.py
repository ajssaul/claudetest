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

    async def run(self, wisdoms: list[dict], task: Task) -> dict:
        self.log(f"최종 확인 시작: {len(wisdoms)}개 명언, 요청={task.count}개")

        prompt = self._build_prompt(wisdoms, task)
        messages = [{"role": "user", "content": prompt}]

        try:
            raw = self.call_llm(messages, temperature=0.3)
            result = self._extract_json(raw)

            if not isinstance(result, dict):
                return {"action": "APPROVED", "final_wisdoms": wisdoms, "removed_count": 0, "removed_reasons": {}}

            action = result.get("action", "APPROVED")

            if action == "APPROVED":
                final_indices = result.get("final_wisdoms_indices", list(range(len(wisdoms))))
                removed_indices = result.get("removed_indices", [])
                removed_reasons = result.get("removed_reasons", {})
                final_wisdoms = [wisdoms[i] for i in final_indices if i < len(wisdoms)]
                self.log(f"최종 확인 완료: {len(final_wisdoms)}개 통과, {len(removed_indices)}개 제거")
                return {
                    "action": "APPROVED",
                    "final_wisdoms": final_wisdoms,
                    "removed_count": len(removed_indices),
                    "removed_reasons": removed_reasons,
                }

            elif action == "RETURN_TO_REVIEWER":
                self.log(f"검수자 반려: {result.get('reason', 'N/A')}")
                problematic = result.get("problematic_items", [])
                return {
                    "action": "RETURN_TO_REVIEWER",
                    "problematic_items": problematic,
                    "reason": result.get("reason", ""),
                    "instructions": result.get("instructions", ""),
                    "passing_subset": [w for i, w in enumerate(wisdoms) if i not in problematic],
                }

            elif action == "RETURN_TO_COLLECTOR_VIA_ORCHESTRATOR":
                passed_indices = result.get("passed_wisdoms_indices", list(range(len(wisdoms))))
                passed_wisdoms = [wisdoms[i] for i in passed_indices if i < len(wisdoms)]
                self.log(f"수집 재시작: 통과 {len(passed_wisdoms)}개")
                return {
                    "action": "RETURN_TO_COLLECTOR_VIA_ORCHESTRATOR",
                    "reason": result.get("reason", ""),
                    "passed_wisdoms": passed_wisdoms,
                    "additional_needed": result.get("additional_needed", 0),
                    "topic": task.topic,
                }

            return {"action": "APPROVED", "final_wisdoms": wisdoms, "removed_count": 0, "removed_reasons": {}}

        except Exception as e:
            logger.error(f"최종 확인 오류: {e}")
            return {"action": "APPROVED", "final_wisdoms": wisdoms, "removed_count": 0, "removed_reasons": {}}

    def _build_prompt(self, wisdoms: list[dict], task: Task) -> str:
        parts = [f"아래 {len(wisdoms)}개 명언을 최종 확인해줘.\n"]
        parts.append(f"■ 주제: {task.topic}")
        if task.leaders:
            parts.append(f"■ 인물: {', '.join(task.leaders)}")
        parts.append(f"■ 요청 개수: {task.count}개")

        parts.append(f"""
■ 확인 사항:
1. 주제 '{task.topic}'과 일치하는가?
2. 품질이 일관적인가?
3. 중복 명언이 있는가? (있으면 제거)
4. 모든 필수 필드가 채워져 있는가?

■ 명언 데이터:
{json.dumps(wisdoms, ensure_ascii=False, indent=2)}

반드시 아래 JSON 형식으로만 응답해라:
```json
{{
  "action": "APPROVED",
  "final_wisdoms_indices": [0, 1, 2],
  "removed_indices": [],
  "removed_reasons": {{}}
}}
```
문제가 있으면 action을 "RETURN_TO_REVIEWER" 또는 "RETURN_TO_COLLECTOR_VIA_ORCHESTRATOR"로 변경.""")
        return "\n".join(parts)
