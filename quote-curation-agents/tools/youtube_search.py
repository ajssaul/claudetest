"""
유튜브 검색 및 자막 추출 도구.
youtube-transcript-api를 사용하여 자막에서 명언을 추출한다.
"""

import logging
from typing import Optional

logger = logging.getLogger("quote-agents.tools.youtube")


class YouTubeSearchTool:
    """유튜브에서 명언 관련 영상을 검색하고 자막을 추출한다."""

    @staticmethod
    def build_search_queries(topic: str, leaders: list[str]) -> list[str]:
        """유튜브 검색 쿼리를 생성한다."""
        queries = []
        if leaders:
            for leader in leaders:
                queries.append(f"{leader} {topic} speech")
                queries.append(f"{leader} {topic} interview")
        else:
            queries.append(f"{topic} leadership speech")
            queries.append(f"greatest {topic} speeches")
        return queries

    @staticmethod
    async def get_transcript(video_id: str, languages: list[str] = None) -> Optional[str]:
        """유튜브 영상의 자막을 추출한다."""
        if languages is None:
            languages = ["en", "ko"]
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            transcript = None
            for lang in languages:
                try:
                    transcript = transcript_list.find_transcript([lang])
                    break
                except Exception:
                    continue

            if transcript is None:
                try:
                    transcript = transcript_list.find_generated_transcript(["en"])
                except Exception:
                    return None

            entries = transcript.fetch()
            full_text = " ".join(entry["text"] for entry in entries)
            return full_text

        except ImportError:
            logger.warning("youtube-transcript-api가 설치되지 않았습니다.")
            return None
        except Exception as e:
            logger.warning(f"유튜브 자막 추출 실패 (video_id={video_id}): {e}")
            return None

    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        """유튜브 URL에서 video_id를 추출한다."""
        import re
        patterns = [
            r'(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
