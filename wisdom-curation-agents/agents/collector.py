"""
수집자 (Collector) 에이전트.
다양한 소스에서 명언 원문과 메타데이터를 수집한다.
Claude의 web_search tool을 활용하여 실제 웹 검색을 수행한다.
"""

import json
import logging
from typing import Optional

from .base_agent import BaseAgent
from models.task import Task
from tools.web_search import WebSearchTool
from tools.youtube_search import YouTubeSearchTool
from tools.x_search import XSearchTool
from tools.book_search import BookSearchTool

logger = logging.getLogger("wisdom-agents.collector")


class Collector(BaseAgent):
    """명언 수집 에이전트."""

    def __init__(self):
        super().__init__(
            name="수집자",
            role="다양한 소스에서 명언 원문과 메타데이터를 수집",
            system_prompt_file="collector_system.txt",
        )
        self._previous_feedback: Optional[dict] = None
        self._excluded_wisdoms: list[dict] = []

    async def run(
        self,
        task: Task,
        exclude: Optional[list] = None,
        target: Optional[int] = None,
        supplement_request: Optional[str] = None,
    ) -> list[dict]:
        """
        명언을 수집한다.

        Args:
            task: 태스크 정보 (주제, 인물, 개수 등)
            exclude: 이미 수집된 명언 (중복 방지)
            target: 수집 목표 개수
            supplement_request: 보완 수집 요구사항 (반려 시)

        Returns:
            수집된 명언 데이터 리스트
        """
        if exclude:
            self._excluded_wisdoms = exclude
        if target is None:
            target = int(task.count * 2)

        self.log(f"수집 시작: 주제='{task.topic}', 인물={task.leaders or '자동'}, 목표={target}개")

        # 수집 요청 메시지 구성
        user_message = self._build_collection_prompt(task, target, supplement_request)

        # Claude API 호출 (web_search tool 사용)
        messages = [{"role": "user", "content": user_message}]

        tools = [WebSearchTool.get_tool_definition()]
        collected = self._collect_with_search(messages, tools, task, target)

        self.log(f"수집 완료: {len(collected)}개 수집됨")
        return collected

    def _build_collection_prompt(
        self,
        task: Task,
        target: int,
        supplement_request: Optional[str] = None,
    ) -> str:
        """수집 요청 프롬프트를 구성한다."""
        prompt_parts = [
            f"아래 조건에 맞는 명언을 {target}개 수집해줘.\n",
            f"■ 주제: {task.topic}",
        ]

        if task.leaders:
            prompt_parts.append(f"■ 인물: {', '.join(task.leaders)}")
        else:
            prompt_parts.append("■ 인물: 해당 주제의 세계적 대가들 (자동 탐색)")

        if task.categories:
            prompt_parts.append(f"■ 카테고리 필터: {', '.join(task.categories)}")

        if task.constraints:
            prompt_parts.append(f"■ 기타 조건: {task.constraints}")

        # 보완 수집 모드
        if supplement_request:
            prompt_parts.append(f"\n⚠️ 보완 수집 모드:")
            prompt_parts.append(f"이전 수집이 반려되었다. 반려 사유: {supplement_request}")
            prompt_parts.append("기존 수집과 중복되지 않는 새로운 명언을 수집해라.")

        # 이미 수집된 명언 정보 (중복 방지)
        if self._excluded_wisdoms:
            excluded_names = []
            for w in self._excluded_wisdoms:
                if isinstance(w, dict):
                    name = w.get("leader_name_en", w.get("leader_name", ""))
                    original = w.get("wisdom_original", "")[:50]
                    excluded_names.append(f"- {name}: {original}...")
                else:
                    excluded_names.append(f"- {str(w)[:80]}...")

            if excluded_names:
                prompt_parts.append(f"\n⚠️ 이미 확보된 명언 (중복 방지):")
                prompt_parts.extend(excluded_names[:20])

        prompt_parts.append(f"""
■ 수집 지침:
- 출처가 명확한 명언만 수집 (구체적 출처명 필수)
- 웹에서 검색하여 실제 명언, 인터뷰 발언, 연설, 책 인용 등을 찾아라
- 각 명언에 발언자 이름(한글/영문), 직함, 원문, 출처명, 출처 유형, 출처 URL을 포함
- 퍼블릭 도메인 도서(저자 1954년 이전 사망)는 2~7문장 자유, 비퍼블릭 도메인 도서는 최대 2문장
- 주제와 관련성이 높은 것 위주로 수집
- 표면적이고 피상적인 내용, 맥락 없는 단편적 문구는 제외

결과를 JSON 배열로 응답해라. 각 항목:
{{
  "leader_name": "한글 이름",
  "leader_name_en": "English Name",
  "leader_title": "직함",
  "wisdom_original": "영어 원문 (2~7문장, 비퍼블릭 도메인 도서는 최대 2문장)",
  "source": "출처명 (책 제목, 연설명, 인터뷰명 등)",
  "source_type": "도서|도서 (비퍼블릭 도메인)|인터뷰|연설|팟캐스트|SNS|블로그|기타",
  "source_url": "출처 URL",
  "source_making_date": "날짜 (없으면 빈 문자열)",
  "is_public_domain": true/false
}}
""")

        return "\n".join(prompt_parts)

    def _collect_with_search(
        self,
        messages: list,
        tools: list,
        task: Task,
        target: int,
    ) -> list[dict]:
        """
        Claude의 web_search tool을 활용하여 명언을 수집한다.
        Claude가 자체적으로 웹 검색을 수행하고 결과를 종합하여 명언을 수집한다.
        """
        try:
            raw_response = self.call_llm(messages, tools=tools, temperature=0.7)
            collected = self._extract_json(raw_response)

            if isinstance(collected, dict):
                collected = collected.get("wisdoms", collected.get("results", [collected]))
            if not isinstance(collected, list):
                collected = [collected]

            # 기본 검증
            validated = []
            for item in collected:
                if not isinstance(item, dict):
                    continue
                if not item.get("wisdom_original"):
                    continue
                if not item.get("leader_name") and not item.get("leader_name_en"):
                    continue
                validated.append(item)

            return validated[:target]

        except Exception as e:
            logger.error(f"수집 중 오류 발생: {e}")
            # 웹 검색 없이 LLM 지식만으로 수집 시도
            return self._collect_from_knowledge(task, target)

    def _collect_from_knowledge(self, task: Task, target: int) -> list[dict]:
        """웹 검색 없이 LLM의 기존 지식으로 명언을 수집한다 (폴백)."""
        self.log("웹 검색 실패. LLM 지식 기반 수집으로 전환.")

        prompt = self._build_collection_prompt(task, target)
        prompt += "\n\n(웹 검색 없이 너의 지식 내에서 명언을 수집해줘. 출처는 최대한 정확하게.)"

        messages = [{"role": "user", "content": prompt}]

        try:
            raw_response = self.call_llm(messages, temperature=0.7)
            collected = self._extract_json(raw_response)

            if isinstance(collected, dict):
                collected = collected.get("wisdoms", collected.get("results", [collected]))
            if not isinstance(collected, list):
                collected = [collected]

            validated = []
            for item in collected:
                if isinstance(item, dict) and item.get("wisdom_original"):
                    validated.append(item)

            return validated[:target]

        except Exception as e:
            logger.error(f"지식 기반 수집도 실패: {e}")
            return []

    def receive_feedback(self, feedback: dict):
        """다른 에이전트로부터의 피드백을 수신한다."""
        self._previous_feedback = feedback
        self.log(f"피드백 수신: {feedback.get('reason', 'N/A')}")
