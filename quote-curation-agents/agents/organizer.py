"""
정리자 (Organizer) 에이전트.
수집된 명언 데이터를 필터링/정리하고, 한국어 번역과 해설을 작성한다.
"""

import json
import logging
from typing import Optional

from .base_agent import BaseAgent
from models.task import Task

logger = logging.getLogger("quote-agents.organizer")


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
        self.log(f"정리 시작: {len(collected_data)}개 수집 데이터")

        topic = task.topic if task else "일반"
        user_message = self._build_prompt(collected_data, topic, task, force)
        messages = [{"role": "user", "content": user_message}]

        try:
            raw = await self.async_call_llm(messages, temperature=0.5)
            result = self._extract_json(raw)

            # 배열이면 바로 wisdoms
            if isinstance(result, list):
                wisdoms = self._validate_wisdoms(result)
                self.log(f"정리 완료: {len(wisdoms)}개")
                return {"action": "ORGANIZED", "wisdoms": wisdoms}

            # dict이면 action 확인
            action = result.get("action", "ORGANIZED")
            if action == "RETURN_TO_COLLECTOR" and not force:
                self.log(f"수집자 반려: {result.get('reason', 'N/A')}")
                return {
                    "action": "RETURN_TO_COLLECTOR",
                    "reason": result.get("reason", "수집 데이터 품질 부족"),
                    "requirements": result.get("requirements", ""),
                }

            wisdoms = result.get("wisdoms", [])
            wisdoms = self._validate_wisdoms(wisdoms)
            self.log(f"정리 완료: {len(wisdoms)}개")
            return {"action": "ORGANIZED", "wisdoms": wisdoms}

        except Exception as e:
            logger.error(f"정리 중 오류: {e}")
            return {"action": "ORGANIZED", "wisdoms": []}

    async def revise(
        self,
        wisdoms: list[dict],
        instructions: list,
    ) -> list[dict]:
        self.log(f"수정 시작: {len(wisdoms)}개 명언")

        items = []
        for i, (w, inst) in enumerate(zip(wisdoms, instructions)):
            inst_str = inst if isinstance(inst, str) else json.dumps(inst, ensure_ascii=False)
            items.append(f"--- 명언 #{i} ---\n현재: {json.dumps(w, ensure_ascii=False)}\n수정 지시: {inst_str}\n")

        prompt = f"""검수자의 피드백에 따라 아래 명언들을 수정해줘.

수정 규칙:
- 번역은 '-다' 체, 성숙한 어투
- 해설은 150~250자, 원문 범위 내
- 비퍼블릭 도메인 도서: 원문 2문장, 번역은 재구성 의역, 해설 4~5문장

{"".join(items)}

수정된 명언을 JSON 배열로만 응답해라:
```json
[{{"leader_name": "...", "leader_name_en": "...", "leader_title": "...", "wisdom_original": "...", "wisdom_kr": "...", "wisdom_commentary": "...", "source": "...", "source_type": "...", "source_url": "...", "category": "...", "mood": "...", "source_making_date": ""}}]
```"""

        messages = [{"role": "user", "content": prompt}]
        try:
            raw = await self.async_call_llm(messages, temperature=0.5)
            result = self._extract_json(raw)
            if isinstance(result, dict):
                result = result.get("wisdoms", result.get("revised", [result]))
            if isinstance(result, list):
                self.log(f"수정 완료: {len(result)}개")
                return self._validate_wisdoms(result)
            return wisdoms
        except Exception as e:
            logger.error(f"수정 오류: {e}")
            return wisdoms

    def _validate_wisdoms(self, wisdoms: list) -> list[dict]:
        """명언 리스트의 기본 유효성을 확인하고 기본값을 채운다."""
        validated = []
        for w in wisdoms:
            if not isinstance(w, dict):
                continue
            if not w.get("wisdom_original") and not w.get("wisdom_kr"):
                continue
            w.setdefault("leader_name", w.get("leader_name_en", ""))
            w.setdefault("leader_name_en", w.get("leader_name", ""))
            w.setdefault("leader_title", "")
            w.setdefault("wisdom_original", "")
            w.setdefault("wisdom_kr", "")
            w.setdefault("wisdom_commentary", "")
            w.setdefault("source", "")
            w.setdefault("source_type", "기타")
            w.setdefault("source_url", "")
            w.setdefault("category", "self-improvement")
            w.setdefault("mood", "growth")
            w.setdefault("source_making_date", "")
            validated.append(w)
        return validated

    def _build_prompt(
        self, collected_data: list[dict], topic: str, task: Optional[Task], force: bool,
    ) -> str:
        parts = [f"아래 수집된 {len(collected_data)}개 명언을 정리하고 번역/해설을 작성해줘.\n"]
        parts.append(f"■ 주제: {topic}")
        if task and task.leaders:
            parts.append(f"■ 인물: {', '.join(task.leaders)}")
        if task:
            parts.append(f"■ 목표 개수: {task.count}개")

        if force:
            parts.append("\n⚠️ 강제 진행 모드: 가능한 데이터로 최대한 정리해라.")

        parts.append(f"""
■ 정리 규칙:
1. 주제 관련성 높은 것 우선
2. 원문: 3~7문장 (비퍼블릭 도메인 도서만 최대 2문장). 2문장만 있으면 앞뒤 맥락 포함하여 3문장 이상으로 확장 (1명언 1주제 유지 시)
3. 번역(wisdom_kr): '-다' 체, 비퍼블릭 도메인은 재구성 의역 필수
4. 해설(wisdom_commentary): 150~250자, 2~4문장, '-다' 체. 한국의 예를 들 때 특정 인물 실명 사용 금지 (예: "한 대기업 CEO가..." 등으로 표현). 단, 퍼블릭 도메인 인물(1954년 이전 사망)의 이름은 사용 가능
5. 카테고리: business|marketing|leadership|self-improvement|philosophy|wealth|creativity|psychology|relationships
6. Mood: execution|growth|challenge|relationships|motivation|new-goal|comfort|contemplation|anxiety|habits|meaning

■ 수집 데이터:
{json.dumps(collected_data, ensure_ascii=False, indent=2)}

반드시 아래 JSON 형식으로만 응답해라:
```json
{{
  "action": "ORGANIZED",
  "wisdoms": [
    {{
      "leader_name": "한글 이름",
      "leader_name_en": "English Name",
      "leader_title": "직함",
      "wisdom_original": "정리된 영어 원문",
      "wisdom_kr": "한국어 번역",
      "wisdom_commentary": "한국 맥락 해설",
      "source": "출처명",
      "source_type": "출처 유형",
      "source_url": "URL",
      "category": "카테고리",
      "mood": "mood",
      "source_making_date": ""
    }}
  ]
}}
```""")
        return "\n".join(parts)
