"""
정리자 (Organizer) 에이전트.
수집된 명언 데이터를 필터링/정리하고, 한국어 번역과 해설을 작성한다.
"""

import json
import logging
from typing import Optional

from .base_agent import BaseAgent
from models.task import Task

logger = logging.getLogger("wisdom-agents.organizer")


class Organizer(BaseAgent):
    """명언 정리 에이전트."""

    def __init__(self):
        super().__init__(
            name="정리자",
            role="수집 데이터를 필터링/정리하고 번역과 해설을 작성",
            system_prompt_file="organizer_system.txt",
        )

    async def run(
        self,
        collected_data: list[dict],
        task: Optional[Task] = None,
        force: bool = False,
    ) -> dict:
        """
        수집된 데이터를 정리하고 번역/해설을 작성한다.

        Args:
            collected_data: 수집자가 수집한 명언 데이터
            task: 태스크 정보
            force: True면 품질 평가 없이 강제 진행

        Returns:
            {
                "action": "ORGANIZED" | "RETURN_TO_COLLECTOR",
                "wisdoms": [...],  # action이 ORGANIZED일 때
                "reason": str,     # action이 RETURN_TO_COLLECTOR일 때
                "requirements": str,
            }
        """
        self.log(f"정리 시작: {len(collected_data)}개 수집 데이터")

        topic = task.topic if task else "일반"

        # 품질 평가 프롬프트
        user_message = self._build_organize_prompt(collected_data, topic, task, force)
        messages = [{"role": "user", "content": user_message}]

        try:
            raw_response = self.call_llm(messages, temperature=0.5)
            result = self._extract_json(raw_response)

            if isinstance(result, list):
                result = {"action": "ORGANIZED", "wisdoms": result}

            action = result.get("action", "ORGANIZED")

            if action == "RETURN_TO_COLLECTOR" and not force:
                self.log(f"수집자 반려: {result.get('reason', 'N/A')}")
                return {
                    "action": "RETURN_TO_COLLECTOR",
                    "reason": result.get("reason", "수집 데이터 품질 부족"),
                    "requirements": result.get("requirements", ""),
                }

            wisdoms = result.get("wisdoms", [])
            self.log(f"정리 완료: {len(wisdoms)}개 정리됨")

            return {
                "action": "ORGANIZED",
                "wisdoms": wisdoms,
            }

        except Exception as e:
            logger.error(f"정리 중 오류 발생: {e}")
            return {
                "action": "ORGANIZED",
                "wisdoms": [],
            }

    async def revise(
        self,
        wisdoms: list[dict],
        instructions: list[dict],
    ) -> list[dict]:
        """
        검수자의 REVISE 판정에 따라 명언을 수정한다.

        Args:
            wisdoms: 수정할 명언 리스트
            instructions: 수정 지시 리스트 (각 명언에 대한 지시)

        Returns:
            수정된 명언 리스트
        """
        self.log(f"수정 시작: {len(wisdoms)}개 명언")

        revision_items = []
        for i, (wisdom, instruction) in enumerate(zip(wisdoms, instructions)):
            revision_items.append({
                "index": i,
                "wisdom": wisdom,
                "instruction": instruction,
            })

        user_message = self._build_revision_prompt(revision_items)
        messages = [{"role": "user", "content": user_message}]

        try:
            raw_response = self.call_llm(messages, temperature=0.5)
            result = self._extract_json(raw_response)

            if isinstance(result, dict):
                revised = result.get("wisdoms", result.get("revised", []))
            elif isinstance(result, list):
                revised = result
            else:
                revised = []

            self.log(f"수정 완료: {len(revised)}개")
            return revised

        except Exception as e:
            logger.error(f"수정 중 오류 발생: {e}")
            return wisdoms  # 수정 실패 시 원본 반환

    def _build_organize_prompt(
        self,
        collected_data: list[dict],
        topic: str,
        task: Optional[Task],
        force: bool,
    ) -> str:
        """정리 요청 프롬프트를 구성한다."""
        prompt_parts = [
            f"아래 수집 데이터를 정리하고 번역/해설을 작성해줘.\n",
            f"■ 주제: {topic}",
        ]

        if task and task.leaders:
            prompt_parts.append(f"■ 인물: {', '.join(task.leaders)}")

        if task:
            prompt_parts.append(f"■ 목표 개수: {task.count}개")

        if force:
            prompt_parts.append(
                "\n⚠️ 강제 진행 모드: 품질 평가를 건너뛰고 가능한 데이터로 최대한 정리해라."
            )
        else:
            prompt_parts.append("""
■ 품질 평가 기준:
- 수집된 명언 중 주제와 무관한 것이 50% 이상이면 → RETURN_TO_COLLECTOR
- 출처가 불명확한 명언이 대다수이면 → RETURN_TO_COLLECTOR
- 원문이 누락되거나 너무 짧아 정리가 불가능하면 → RETURN_TO_COLLECTOR

반려 시 형식:
{
  "action": "RETURN_TO_COLLECTOR",
  "reason": "반려 사유",
  "requirements": "보완 요구사항"
}
""")

        prompt_parts.append(f"""
■ 정리 규칙:
1. 주제 관련성이 높은 것을 우선 선별
2. 원문 정리: 2~7문장 (비퍼블릭 도메인 도서: 최대 2문장)
3. 한국어 번역: 직역이 자연스러우면 직역, 어색하면 의역. '-다' 체.
   - 비퍼블릭 도메인 도서: 직역 금지, 재구성 의역 필수
4. 해설: 150~250자, 2~4문장. 원문 범위 내에서 한국 독자가 적용할 수 있도록.
   - 비퍼블릭 도메인 도서: 해설 4~5문장으로 보완
5. 카테고리/mood 배정

■ 카테고리: business, marketing, leadership, self-improvement, philosophy, wealth, creativity, psychology, relationships
■ Mood: execution, growth, challenge, relationships, motivation, new-goal, comfort, contemplation, anxiety, habits, meaning

■ 수집 데이터 ({len(collected_data)}개):
""")

        prompt_parts.append(json.dumps(collected_data, ensure_ascii=False, indent=2))

        prompt_parts.append("""
정리된 결과를 JSON 형식으로 응답해라:
{
  "action": "ORGANIZED",
  "wisdoms": [
    {
      "leader_name": "한글 이름",
      "leader_name_en": "English Name",
      "leader_title": "직함",
      "wisdom_original": "정리된 영어 원문",
      "wisdom_kr": "한국어 번역",
      "wisdom_commentary": "한국 맥락 해설 (150~250자)",
      "source": "출처명",
      "source_type": "출처 유형",
      "source_url": "URL",
      "category": "카테고리 (|로 구분)",
      "mood": "mood (|로 구분)",
      "source_making_date": "날짜"
    }
  ]
}
""")

        return "\n".join(prompt_parts)

    def _build_revision_prompt(self, revision_items: list[dict]) -> str:
        """수정 요청 프롬프트를 구성한다."""
        prompt_parts = [
            "검수자의 피드백에 따라 아래 명언들을 수정해줘.\n",
            "■ 수정 규칙:",
            "- 수정 지시를 정확히 따른다",
            "- 번역은 '-다' 체, 성숙한 어투를 유지한다",
            "- 해설은 150~250자, 원문 범위 내에서 작성한다",
            "- 비퍼블릭 도메인 도서는 원문 2문장, 번역은 재구성 의역, 해설 4~5문장\n",
        ]

        for item in revision_items:
            prompt_parts.append(f"--- 명언 #{item['index']} ---")
            prompt_parts.append(f"현재 데이터: {json.dumps(item['wisdom'], ensure_ascii=False)}")
            prompt_parts.append(f"수정 지시: {item['instruction']}")
            prompt_parts.append("")

        prompt_parts.append("""
수정된 명언을 JSON 배열로 응답해라. 기존 필드를 모두 포함하되, 수정 지시에 따라 변경된 값만 업데이트:
[
  {
    "leader_name": "...",
    "leader_name_en": "...",
    "leader_title": "...",
    "wisdom_original": "...",
    "wisdom_kr": "...",
    "wisdom_commentary": "...",
    "source": "...",
    "source_type": "...",
    "source_url": "...",
    "category": "...",
    "mood": "...",
    "source_making_date": "..."
  }
]
""")

        return "\n".join(prompt_parts)
