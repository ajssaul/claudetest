"""
수집자 (Collector) 에이전트.
다양한 소스에서 명언 원문과 메타데이터를 수집한다.
"""

import json
import logging
from typing import Optional

from .base_agent import BaseAgent
from models.task import Task
from tools.web_search import WebSearchTool

logger = logging.getLogger("wisdom-agents.collector")


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

        # 1차: web_search tool 사용 시도
        collected = self._try_web_search(task, target, supplement_request)

        # 2차: 실패 시 지식 기반 수집
        if not collected:
            self.log("웹 검색 실패/결과 없음. LLM 지식 기반 수집으로 전환.")
            collected = self._collect_from_knowledge(task, target, supplement_request)

        self.log(f"수집 완료: {len(collected)}개 수집됨")
        return collected

    def _try_web_search(
        self, task: Task, target: int, supplement_request: Optional[str]
    ) -> list[dict]:
        """Claude web_search tool을 사용하여 수집을 시도한다."""
        try:
            prompt = self._build_prompt(task, target, supplement_request)
            messages = [{"role": "user", "content": prompt}]
            tools = [WebSearchTool.get_tool_definition()]

            raw = self.call_llm(messages, tools=tools, temperature=0.7)
            return self._parse_collected(raw, target)
        except Exception as e:
            logger.warning(f"웹 검색 수집 실패: {e}")
            return []

    def _collect_from_knowledge(
        self, task: Task, target: int, supplement_request: Optional[str]
    ) -> list[dict]:
        """웹 검색 없이 LLM 지식만으로 수집한다."""
        try:
            prompt = self._build_prompt(task, target, supplement_request)
            prompt += "\n\n(웹 검색 없이 너의 지식에서 수집해라. 출처는 최대한 정확하게.)"
            messages = [{"role": "user", "content": prompt}]

            raw = self.call_llm(messages, temperature=0.7)
            return self._parse_collected(raw, target)
        except Exception as e:
            logger.error(f"지식 기반 수집도 실패: {e}")
            return []

    def _parse_collected(self, raw_response: str, target: int) -> list[dict]:
        """LLM 응답에서 수집 데이터를 추출하고 검증한다."""
        try:
            result = self._extract_json(raw_response)
        except ValueError as e:
            logger.error(f"JSON 추출 실패: {e}")
            return []

        # dict인 경우 wisdoms 키에서 리스트 추출
        if isinstance(result, dict):
            for key in ("wisdoms", "results", "quotes", "data"):
                if key in result and isinstance(result[key], list):
                    result = result[key]
                    break
            else:
                result = [result]

        if not isinstance(result, list):
            return []

        # 기본 검증
        validated = []
        for item in result:
            if not isinstance(item, dict):
                continue
            if not item.get("wisdom_original"):
                continue
            if not item.get("leader_name") and not item.get("leader_name_en"):
                continue
            # 빈 값 기본값 채우기
            item.setdefault("leader_name", item.get("leader_name_en", ""))
            item.setdefault("leader_name_en", item.get("leader_name", ""))
            item.setdefault("leader_title", "")
            item.setdefault("source", "")
            item.setdefault("source_type", "기타")
            item.setdefault("source_url", "")
            item.setdefault("source_making_date", "")
            item.setdefault("is_public_domain", False)
            validated.append(item)

        return validated[:target]

    def _build_prompt(
        self, task: Task, target: int, supplement_request: Optional[str]
    ) -> str:
        parts = [f"아래 조건에 맞는 명언을 정확히 {target}개 수집해줘.\n"]
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
            parts.append(f"\n⚠️ 보완 수집 모드: {supplement_request}")
            parts.append("기존 수집과 중복되지 않는 새로운 명언을 수집해라.")

        if self._excluded_wisdoms:
            parts.append("\n⚠️ 아래 명언과 중복 방지:")
            for w in self._excluded_wisdoms[:10]:
                if isinstance(w, dict):
                    name = w.get("leader_name_en", w.get("leader_name", ""))
                    orig = w.get("wisdom_original", "")[:40]
                    parts.append(f"  - {name}: {orig}...")

        parts.append("""
■ 수집 규칙:
- 출처가 명확한 명언만 수집 (구체적 출처명 필수)
- 각 명언에 발언자 이름(한글/영문), 직함, 원문, 출처명, 출처 유형, 출처 URL 포함
- 퍼블릭 도메인 도서(저자 1954년 이전 사망)는 2~7문장, 비퍼블릭 도메인 도서는 최대 2문장
- 주제 관련성이 높은 것 위주

반드시 아래 JSON 배열 형식으로만 응답해라. 설명 텍스트 없이 JSON만:
```json
[
  {
    "leader_name": "한글 이름",
    "leader_name_en": "English Name",
    "leader_title": "직함",
    "wisdom_original": "영어 원문",
    "source": "출처명",
    "source_type": "도서|도서 (비퍼블릭 도메인)|인터뷰|연설|팟캐스트|SNS|블로그|기타",
    "source_url": "URL",
    "source_making_date": "",
    "is_public_domain": false
  }
]
```""")

        return "\n".join(parts)

    def receive_feedback(self, feedback: dict):
        self._excluded_wisdoms.extend(feedback.get("existing_wisdoms", []))
        self.log(f"피드백 수신: {feedback.get('reason', 'N/A')}")
