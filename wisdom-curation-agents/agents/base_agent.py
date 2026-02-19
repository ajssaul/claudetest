import json
import os
import logging
from datetime import datetime
from typing import Optional

import anthropic

import config

logger = logging.getLogger("wisdom-agents")


class BaseAgent:
    """모든 에이전트의 공통 베이스 클래스."""

    def __init__(self, name: str, role: str, system_prompt_file: Optional[str] = None):
        self.name = name
        self.role = role
        self.system_prompt = self._load_system_prompt(system_prompt_file)
        self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        self.model = config.DEFAULT_MODEL
        self.max_tokens = config.MAX_TOKENS

    def _load_system_prompt(self, filename: Optional[str]) -> str:
        """prompts/ 폴더에서 시스템 프롬프트를 로드한다."""
        if filename is None:
            return ""
        path = os.path.join(config.PROMPTS_DIR, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            logger.warning(f"시스템 프롬프트 파일 없음: {path}")
            return ""

    async def run(self, task_input: dict) -> dict:
        """에이전트 실행 메서드. 하위 클래스에서 구현."""
        raise NotImplementedError(f"{self.name} 에이전트의 run() 메서드가 구현되지 않았습니다.")

    def call_llm(
        self,
        messages: list,
        tools: Optional[list] = None,
        temperature: float = 0.7,
    ) -> str:
        """Claude API 호출 래퍼."""
        kwargs = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": self.system_prompt,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools

        response = self.client.messages.create(**kwargs)

        # tool_use 응답 처리
        result_parts = []
        for block in response.content:
            if block.type == "text":
                result_parts.append(block.text)
            elif block.type == "tool_use":
                result_parts.append(json.dumps({
                    "tool_use": block.name,
                    "tool_input": block.input,
                    "tool_id": block.id,
                }, ensure_ascii=False))

        return "\n".join(result_parts)

    def call_llm_json(
        self,
        messages: list,
        temperature: float = 0.5,
    ) -> dict:
        """Claude API를 호출하고 JSON 응답을 파싱한다."""
        raw = self.call_llm(messages, temperature=temperature)
        return self._extract_json(raw)

    def call_llm_with_tools(
        self,
        messages: list,
        tools: list,
        temperature: float = 0.7,
    ) -> tuple:
        """tool_use를 지원하는 Claude API 호출. (response, tool_calls) 반환."""
        kwargs = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": self.system_prompt,
            "messages": messages,
            "tools": tools,
            "temperature": temperature,
        }

        response = self.client.messages.create(**kwargs)

        text_parts = []
        tool_calls = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })

        return "\n".join(text_parts), tool_calls

    @staticmethod
    def _extract_json(text: str) -> dict:
        """텍스트에서 JSON 블록을 추출한다."""
        # ```json ... ``` 블록 추출 시도
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))

        # { ... } 직접 추출 시도
        brace_start = text.find('{')
        if brace_start != -1:
            depth = 0
            for i in range(brace_start, len(text)):
                if text[i] == '{':
                    depth += 1
                elif text[i] == '}':
                    depth -= 1
                    if depth == 0:
                        return json.loads(text[brace_start:i + 1])

        # [ ... ] 배열 추출 시도
        bracket_start = text.find('[')
        if bracket_start != -1:
            depth = 0
            for i in range(bracket_start, len(text)):
                if text[i] == '[':
                    depth += 1
                elif text[i] == ']':
                    depth -= 1
                    if depth == 0:
                        return json.loads(text[bracket_start:i + 1])

        raise ValueError(f"JSON을 추출할 수 없습니다: {text[:200]}...")

    def log(self, message: str):
        """에이전트 활동 로그."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] [{self.name}] {message}"
        logger.info(log_msg)
        print(log_msg)
