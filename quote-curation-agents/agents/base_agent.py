import asyncio
import json
import re
import os
import logging
import time
import traceback
from datetime import datetime
from typing import Optional

import anthropic

import config

logger = logging.getLogger("quote-agents")

# 공유 클라이언트 싱글턴 (커넥션 풀링)
_shared_sync_client: Optional[anthropic.Anthropic] = None
_shared_async_client: Optional[anthropic.AsyncAnthropic] = None


def _get_sync_client() -> anthropic.Anthropic:
    global _shared_sync_client
    if _shared_sync_client is None:
        _shared_sync_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _shared_sync_client


def _get_async_client() -> anthropic.AsyncAnthropic:
    global _shared_async_client
    if _shared_async_client is None:
        _shared_async_client = anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
    return _shared_async_client


class BaseAgent:
    """모든 에이전트의 공통 베이스 클래스."""

    def __init__(self, name: str, role: str, system_prompt_file: Optional[str] = None):
        self.name = name
        self.role = role
        self.system_prompt = self._load_system_prompt(system_prompt_file)
        self.model = config.DEFAULT_MODEL
        self.max_tokens = config.MAX_TOKENS

    @property
    def client(self) -> anthropic.Anthropic:
        return _get_sync_client()

    @property
    def async_client(self) -> anthropic.AsyncAnthropic:
        return _get_async_client()

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
        raise NotImplementedError(f"{self.name} 에이전트의 run() 미구현")

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
            "messages": list(messages),
            "temperature": temperature,
        }

        max_retries = 4
        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(**kwargs)
                break
            except Exception as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    wait = 2 ** (attempt + 1)
                    self.log(f"Rate limit 초과, {wait}초 후 재시도 ({attempt + 1}/{max_retries})")
                    time.sleep(wait)
                else:
                    self.log(f"API 호출 실패: {e}")
                    raise

        text_parts = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)

        result = "\n".join(text_parts)
        if not result.strip():
            self.log("경고: API가 빈 텍스트를 반환했습니다")

        return result

    async def async_call_llm(
        self,
        messages: list,
        tools: Optional[list] = None,
        temperature: float = 0.7,
    ) -> str:
        """비동기 Claude API 호출 래퍼."""
        kwargs = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": self.system_prompt,
            "messages": list(messages),
            "temperature": temperature,
        }

        max_retries = 4
        for attempt in range(max_retries):
            try:
                response = await self.async_client.messages.create(**kwargs)
                break
            except Exception as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    wait = 2 ** (attempt + 1)
                    self.log(f"Rate limit 초과, {wait}초 후 재시도 ({attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait)
                else:
                    self.log(f"API 호출 실패: {e}")
                    raise

        text_parts = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)

        result = "\n".join(text_parts)
        if not result.strip():
            self.log("경고: API가 빈 텍스트를 반환했습니다")

        return result

    async def async_call_llm_json(
        self,
        messages: list,
        temperature: float = 0.5,
    ) -> dict:
        """비동기 Claude API를 호출하고 JSON 응답을 파싱한다."""
        raw = await self.async_call_llm(messages, temperature=temperature)
        return self._extract_json(raw)

    def call_llm_json(
        self,
        messages: list,
        temperature: float = 0.5,
    ) -> dict:
        """Claude API를 호출하고 JSON 응답을 파싱한다."""
        raw = self.call_llm(messages, temperature=temperature)
        return self._extract_json(raw)

    @staticmethod
    def _find_matching_bracket(text: str, start: int, open_ch: str, close_ch: str) -> int:
        """매칭되는 닫는 괄호 위치를 찾는다. 없으면 -1."""
        depth = 0
        in_string = False
        escape = False
        for i in range(start, len(text)):
            ch = text[i]
            if escape:
                escape = False
                continue
            if ch == '\\' and in_string:
                escape = True
                continue
            if ch == '"' and not escape:
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == open_ch:
                depth += 1
            elif ch == close_ch:
                depth -= 1
                if depth == 0:
                    return i
        return -1

    @staticmethod
    def _extract_json(text: str):
        """텍스트에서 JSON을 추출한다. dict 또는 list를 반환."""
        if not text or not text.strip():
            raise ValueError("빈 응답에서 JSON을 추출할 수 없습니다")

        # 1) ```json ... ``` 블록 추출
        json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # 2) 먼저 나오는 { 또는 [ 기준으로 추출 (바깥쪽 구조 우선)
        brace_start = text.find('{')
        bracket_start = text.find('[')

        # { 가 [ 보다 먼저 → 객체 우선 시도
        if brace_start != -1 and (bracket_start == -1 or brace_start < bracket_start):
            end = BaseAgent._find_matching_bracket(text, brace_start, '{', '}')
            if end != -1:
                try:
                    return json.loads(text[brace_start:end + 1])
                except json.JSONDecodeError:
                    pass

        # [ 가 { 보다 먼저 → 배열 우선 시도
        if bracket_start != -1 and (brace_start == -1 or bracket_start < brace_start):
            end = BaseAgent._find_matching_bracket(text, bracket_start, '[', ']')
            if end != -1:
                try:
                    return json.loads(text[bracket_start:end + 1])
                except json.JSONDecodeError:
                    pass

        # 3) 둘 다 실패 시 나머지 시도
        if brace_start != -1 and (bracket_start == -1 or brace_start >= bracket_start):
            end = BaseAgent._find_matching_bracket(text, brace_start, '{', '}')
            if end != -1:
                try:
                    return json.loads(text[brace_start:end + 1])
                except json.JSONDecodeError:
                    pass

        if bracket_start != -1 and (brace_start == -1 or bracket_start >= brace_start):
            end = BaseAgent._find_matching_bracket(text, bracket_start, '[', ']')
            if end != -1:
                try:
                    return json.loads(text[bracket_start:end + 1])
                except json.JSONDecodeError:
                    pass

        # 4) 여러 개의 JSON 객체가 나열된 경우
        objects = []
        for m in re.finditer(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text):
            try:
                obj = json.loads(m.group())
                objects.append(obj)
            except json.JSONDecodeError:
                continue
        if objects:
            return objects

        raise ValueError(f"JSON을 추출할 수 없습니다: {text[:300]}...")

    def log(self, message: str):
        """에이전트 활동 로그."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] [{self.name}] {message}"
        logger.info(log_msg)
        print(log_msg)
