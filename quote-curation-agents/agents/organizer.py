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
            raw = await self.async_call_llm(messages, temperature=0.3)
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
- 해설은 200~400자, 4~6문장, 원문 범위 내, '-다' 체
- 해설 목적: 읽는 사람에게 유의미한 인사이트(깨달음, 새로운 시각)를 줄 것. 뻔한 조언("도전이 중요하다", "노력하면 성공한다") 금지
- 해설 작성 순서: 핵심 메시지 정리 → 왜 중요한지 논거 → 한국 맥락 구체적 사례 → 실천적 시사점
- 해설에서 한국 기업·문화·사회를 비하/부정 평가하는 표현 금지 (예: "한국은 아직~", "국내 기업은 ~하지 못한다" 등). 긍정적 사례나 발전 가능성 중심으로 서술
- 해설에서 한국 특정 인물 실명 사용 금지 ("한 대기업 CEO가..." 등으로 표현). 단, 퍼블릭 도메인 인물과 원문 저자(leader_name) 본인은 예외
- 비퍼블릭 도메인 도서: 원문 2문장, 번역은 재구성 의역
- 도서 출처: 한국어 번역본이 있으면 한국어 제목 사용, 영어 원제 괄호 병기 (예: "원칙 (Principles: Life and Work)")

{"".join(items)}

수정된 명언을 JSON 배열로만 응답해라:
```json
[{{"leader_name": "...", "leader_name_en": "...", "leader_title": "...", "wisdom_original": "...", "wisdom_kr": "...", "wisdom_commentary": "...", "source": "...", "source_type": "...", "source_url": "...", "category": "...", "mood": "...", "source_making_date": ""}}]
```"""

        messages = [{"role": "user", "content": prompt}]
        try:
            raw = await self.async_call_llm(messages, temperature=0.3)
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
■ 정리 규칙 (검수자가 이 기준으로 엄격 검수하므로 반드시 준수):

1. 원문 길이 (가장 흔한 반려 사유):
   - 비퍼블릭 도메인 도서 제외: 반드시 5~6문장. 4문장 이하이면 무조건 앞뒤 맥락 포함하여 5문장 이상으로 확장
   - 1명언 1주제 유지 어려우면 최소 3문장까지 축소 가능 (예외적)
   - 비퍼블릭 도메인 도서: 최대 2문장
   - ⚠️ 문장 수를 직접 세어서 확인해라

2. 번역(wisdom_kr):
   - '-다' 체 어투 (모든 문장 끝이 '-다'로 끝나는지 확인)
   - 원문의 구체적 사례와 숫자를 반드시 포함
   - 비퍼블릭 도메인 도서: 재구성 의역 필수 (문장 구조를 완전히 바꿔라)

3. 해설(wisdom_commentary) — 품질이 핵심:
   - 200~400자, 4~6문장 (글자 수와 문장 수를 세어 확인)
   - '-다' 체 어투
   - ⚠️ 핵심: 뻔한 조언 금지. "도전이 중요하다", "노력하면 성공한다" 같은 누구나 아는 말은 쓰지 마라
   - 원문의 핵심 메시지 → 왜 중요한지 논거 → 한국 맥락 구체적 사례 → 실천적 시사점 순서로 작성
   - 한국의 예를 들 때 특정 인물 실명 사용 금지 ("한 대기업 CEO가..." 등으로 표현). 단, 퍼블릭 도메인 인물(1954년 이전 사망)과 원문을 말한 사람(leader_name) 본인의 이름은 사용 가능
   - 한국 비하 표현 금지 ("한국은 아직~" 등)
   - 원문과 동일한 영역의 예시만 사용 (비즈니스 명언→비즈니스 사례, 투자 명언→투자 사례)

4. 출처: 구체적으로 명시 ("인터뷰"만 쓰지 말고 "Forbes Interview, 2015" 등으로)

5. 도서 출처 한국어 제목: source_type이 도서인 경우, 한국어 번역본이 출간된 도서라면 한국어 제목을 사용하고 영어 원제를 괄호로 병기
   예: "원칙 (Principles: Life and Work)", "린 스타트업 (The Lean Startup)", "손자병법 (The Art of War)"
   한국어 번역본이 없는 도서는 영어 원제 유지

6. source_type: 비퍼블릭 도메인 도서는 반드시 "도서 (비퍼블릭 도메인)"으로 표기

7. 카테고리: business|marketing|leadership|self-improvement|philosophy|wealth|creativity|psychology|relationships
8. Mood: execution|growth|challenge|relationships|motivation|new-goal|comfort|contemplation|anxiety|habits|meaning

■ 수집 데이터:
{json.dumps(collected_data, ensure_ascii=False, separators=(',', ':'))}

■ 출력 전 자기 검증: 각 명언에 대해 아래를 반드시 확인한 후 출력해라.
- 원문 문장 수가 기준에 맞는가?
- 번역이 모두 '-다' 체인가?
- 해설이 200~400자, 4~6문장이고 구체적 인사이트가 있는가?
- 해설에 실명/비하 표현이 없는가?
- 도서 출처인 경우, 한국어 번역 제목이 있으면 한국어로 표기했는가?

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
