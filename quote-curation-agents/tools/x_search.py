"""
X(트위터) 검색 도구.
X API v2 접근이 제한적이므로 웹 검색을 통한 간접 수집을 기본으로 한다.
"""

import logging

logger = logging.getLogger("quote-agents.tools.x_search")


class XSearchTool:
    """X(트위터) 공개 트윗에서 명언을 검색한다."""

    @staticmethod
    def build_search_queries(topic: str, leaders: list[str]) -> list[str]:
        """X 검색을 위한 웹 검색 쿼리를 생성한다."""
        queries = []
        if leaders:
            for leader in leaders:
                queries.append(f'site:x.com "{leader}" {topic}')
                queries.append(f'site:twitter.com "{leader}" {topic} wisdom')
        else:
            queries.append(f"site:x.com {topic} wisdom quote")
            queries.append(f"site:twitter.com {topic} insight leader")
        return queries

    @staticmethod
    def format_tweet_source(username: str, tweet_url: str) -> dict:
        """트윗 출처 정보를 포맷한다."""
        return {
            "source": f"X (Twitter) - @{username}",
            "source_type": "SNS",
            "source_url": tweet_url,
        }
