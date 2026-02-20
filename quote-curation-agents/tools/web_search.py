"""
웹 검색 도구.
Anthropic Claude의 web_search tool을 활용하여 명언 관련 페이지를 수집한다.
대안으로 DuckDuckGo 인스턴트 검색도 지원한다.
"""

import json
import logging
from typing import Optional

import httpx

logger = logging.getLogger("quote-agents.tools.web_search")


class WebSearchTool:
    """Claude tool_use의 web_search를 통해 웹 검색을 수행한다."""

    # Claude tool_use에서 사용할 도구 정의
    TOOL_DEFINITION = {
        "type": "web_search_20250305",
        "name": "web_search",
        "max_uses": 10,
    }

    @staticmethod
    def get_tool_definition() -> dict:
        return WebSearchTool.TOOL_DEFINITION

    @staticmethod
    def build_search_queries(
        topic: str,
        leaders: list[str],
        source_type: str = "general",
    ) -> list[str]:
        """주제와 인물 기반으로 검색 쿼리를 생성한다."""
        queries = []

        if leaders:
            for leader in leaders:
                queries.append(f'"{leader}" {topic} quotes wisdom')
                queries.append(f'"{leader}" {topic} speech interview insights')
        else:
            queries.append(f"{topic} quotes from great leaders")
            queries.append(f"{topic} wisdom famous leaders insights")
            queries.append(f"best {topic} quotes business leaders")

        if source_type == "book":
            if leaders:
                for leader in leaders:
                    queries.append(f'"{leader}" book quotes {topic}')
            else:
                queries.append(f"{topic} book quotes famous authors")

        return queries

    @staticmethod
    async def search_duckduckgo(query: str, max_results: int = 10) -> list[dict]:
        """DuckDuckGo API를 사용한 대안 검색."""
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1,
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()

            results = []
            # Abstract 결과
            if data.get("AbstractText"):
                results.append({
                    "title": data.get("Heading", ""),
                    "snippet": data["AbstractText"],
                    "url": data.get("AbstractURL", ""),
                })
            # Related Topics
            for topic_item in data.get("RelatedTopics", [])[:max_results]:
                if isinstance(topic_item, dict) and "Text" in topic_item:
                    results.append({
                        "title": topic_item.get("Text", "")[:100],
                        "snippet": topic_item.get("Text", ""),
                        "url": topic_item.get("FirstURL", ""),
                    })
            return results

        except Exception as e:
            logger.warning(f"DuckDuckGo 검색 실패: {e}")
            return []
