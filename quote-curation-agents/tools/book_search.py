"""
도서 검색 및 원문 추출 도구.

■ 퍼블릭 도메인 도서:
  - Project Gutenberg에서 전문 검색/추출
  - 원문 길이 제한 없음 (2~7문장)

■ 비퍼블릭 도메인 도서:
  - 웹에 공개된 인용/발췌만 수집 (최대 2문장)
  - Google Books 미리보기, Goodreads 인용 등 활용
"""

import logging
from typing import Optional

import httpx

logger = logging.getLogger("quote-agents.tools.book_search")


class BookSearchTool:
    """도서에서 명언을 검색한다."""

    # 주요 퍼블릭 도메인 저자와 사망 연도
    PUBLIC_DOMAIN_AUTHORS = {
        "Marcus Aurelius": 180,
        "Seneca": 65,
        "Sun Tzu": -496,
        "Niccolò Machiavelli": 1527,
        "Machiavelli": 1527,
        "Friedrich Nietzsche": 1900,
        "Benjamin Franklin": 1790,
        "Ralph Waldo Emerson": 1882,
        "Henry David Thoreau": 1862,
        "Leo Tolstoy": 1910,
        "Mark Twain": 1910,
        "Confucius": -479,
        "Lao Tzu": -531,
        "Epictetus": 135,
        "Plato": -348,
        "Aristotle": -322,
        "Adam Smith": 1790,
        "Charles Darwin": 1882,
        "Winston Churchill": 1965,  # 1954 이후이지만 공개 연설은 사용 가능
    }

    @staticmethod
    def is_public_domain_author(author_name: str, death_year: Optional[int] = None) -> bool:
        """저자가 퍼블릭 도메인인지 확인한다 (1954년 이전 사망)."""
        if death_year is not None:
            return death_year < 1954

        # 알려진 저자 DB 확인
        for known_author, known_year in BookSearchTool.PUBLIC_DOMAIN_AUTHORS.items():
            if known_author.lower() in author_name.lower():
                return known_year < 1954
        return False

    @staticmethod
    def build_search_queries(
        topic: str,
        leaders: list[str],
        public_domain_only: bool = False,
    ) -> list[str]:
        """도서 검색 쿼리를 생성한다."""
        queries = []

        if leaders:
            for leader in leaders:
                queries.append(f'"{leader}" book quotes {topic}')
                if public_domain_only:
                    queries.append(f'"{leader}" Project Gutenberg {topic}')
                else:
                    queries.append(f'"{leader}" goodreads quotes {topic}')
        else:
            if public_domain_only:
                queries.append(f"Project Gutenberg {topic} classic books quotes")
            else:
                queries.append(f"best {topic} book quotes")
                queries.append(f"{topic} wisdom from books goodreads")

        return queries

    @staticmethod
    async def search_gutenberg(query: str, max_results: int = 5) -> list[dict]:
        """Project Gutenberg에서 도서를 검색한다."""
        url = "https://gutendex.com/books/"
        params = {"search": query}

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()

            results = []
            for book in data.get("results", [])[:max_results]:
                book_info = {
                    "title": book.get("title", ""),
                    "authors": [
                        a.get("name", "") for a in book.get("authors", [])
                    ],
                    "gutenberg_id": book.get("id"),
                    "url": f"https://www.gutenberg.org/ebooks/{book.get('id')}",
                    "is_public_domain": True,
                }
                # 텍스트 형식 URL
                formats = book.get("formats", {})
                for fmt_key, fmt_url in formats.items():
                    if "text/plain" in fmt_key:
                        book_info["text_url"] = fmt_url
                        break
                results.append(book_info)

            return results

        except Exception as e:
            logger.warning(f"Gutenberg 검색 실패: {e}")
            return []

    @staticmethod
    async def fetch_gutenberg_text(text_url: str, max_chars: int = 50000) -> Optional[str]:
        """Gutenberg 텍스트를 가져온다."""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(text_url)
                resp.raise_for_status()
                text = resp.text[:max_chars]
                return text
        except Exception as e:
            logger.warning(f"Gutenberg 텍스트 가져오기 실패: {e}")
            return None
