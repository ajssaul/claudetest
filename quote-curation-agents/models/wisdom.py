from pydantic import BaseModel, Field, field_validator
from typing import Optional
from enum import Enum


class SourceType(str, Enum):
    BOOK = "도서"
    BOOK_NON_PD = "도서 (비퍼블릭 도메인)"
    INTERVIEW = "인터뷰"
    SPEECH = "연설"
    PODCAST = "팟캐스트"
    SNS = "SNS"
    BLOG = "블로그"
    OTHER = "기타"


VALID_CATEGORIES = [
    "business", "marketing", "leadership", "self-improvement",
    "philosophy", "wealth", "creativity", "psychology", "relationships"
]

VALID_MOODS = [
    "execution", "growth", "challenge", "relationships", "motivation",
    "new-goal", "comfort", "contemplation", "anxiety", "habits", "meaning"
]


class Wisdom(BaseModel):
    leader_name: str = Field(description="명언을 말한 사람의 한글 이름")
    leader_name_en: str = Field(description="명언을 말한 사람의 영어 이름")
    leader_title: str = Field(description="직함 또는 직업")
    wisdom_original: str = Field(description="영어 원문 (5~6문장, 비퍼블릭 도메인 도서만 최대 2문장)")
    wisdom_kr: str = Field(description="한국어 번역 (5~6문장, 비퍼블릭 도메인 도서만 최대 2문장)")
    wisdom_commentary: str = Field(description="한국 맥락 해설 (200~400자, 4~6문장)")
    source: str = Field(description="출처명")
    source_type: SourceType
    source_url: str = Field(description="출처 URL")
    category: str = Field(description="카테고리 ('|'로 구분)")
    mood: Optional[str] = Field(default=None, description="mood 그룹 ('|'로 구분)")
    source_making_date: Optional[str] = Field(default=None, description="출처 날짜")

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        cats = [c.strip() for c in v.split("|")]
        for c in cats:
            if c not in VALID_CATEGORIES:
                raise ValueError(f"유효하지 않은 카테고리: {c}")
        return v

    @field_validator("mood")
    @classmethod
    def validate_mood(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        moods = [m.strip() for m in v.split("|")]
        for m in moods:
            if m not in VALID_MOODS:
                raise ValueError(f"유효하지 않은 mood: {m}")
        return v

    def to_tsv_row(self) -> str:
        """탭 구분 행으로 변환"""
        fields = [
            self.leader_name, self.leader_name_en, self.leader_title,
            self.wisdom_original, self.wisdom_kr, self.wisdom_commentary,
            self.source, self.source_type.value, self.source_url,
            self.category, self.mood or "", self.source_making_date or ""
        ]
        return "\t".join(fields)

    @staticmethod
    def tsv_header() -> str:
        """TSV 헤더 행 반환"""
        columns = [
            "leader_name", "leader_name_en", "leader_title",
            "wisdom_original", "wisdom_kr", "wisdom_commentary",
            "source", "source_type", "source_url",
            "category", "mood", "source_making_date"
        ]
        return "\t".join(columns)
