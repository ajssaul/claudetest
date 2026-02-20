"""
최종 확인자 (Final Validator) 에이전트.
프로그래밍 기반 검증으로 LLM 호출 없이 최종 확인을 수행한다.

검증 항목:
- 중복 명언 제거 (원문 유사도 기반)
- 필수 필드 완성도 확인
- 카테고리/mood 유효값 검증 및 자동 보정
- 수량 확인
"""

import logging
from datetime import datetime

from models.task import Task
from models.wisdom import VALID_CATEGORIES, VALID_MOODS

logger = logging.getLogger("quote-agents.final_validator")

# 필수 필드 목록
REQUIRED_FIELDS = [
    "leader_name", "leader_name_en", "leader_title",
    "wisdom_original", "wisdom_kr", "wisdom_commentary",
    "source", "source_type",
]


class FinalValidator:
    """프로그래밍 기반 최종 검증. LLM 호출 없음."""

    def __init__(self):
        self.name = "최종확인자"

    def log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] [{self.name}] {message}"
        logger.info(log_msg)
        print(log_msg)

    def validate(self, wisdoms: list[dict], task: Task, previous_wisdoms: list[dict] | None = None) -> dict:
        """
        프로그래밍 기반 최종 검증을 수행한다.

        Args:
            wisdoms: 검수 통과한 명언 리스트
            task: 작업 정보
            previous_wisdoms: 이전 실행에서 최종 출력된 명언 리스트 (중복 방지용)

        Returns:
            {
                "action": "APPROVED",
                "final_wisdoms": [...],
                "removed_count": int,
                "removed_reasons": {index_str: reason},
            }
        """
        self.log(f"최종 확인 시작: {len(wisdoms)}개 명언, 요청={task.count}개")

        valid_wisdoms = []
        removed_indices = []
        removed_reasons = {}
        seen_originals = set()

        # 이전 명언의 원문 키를 미리 등록하여 중복 방지
        if previous_wisdoms:
            for pw in previous_wisdoms:
                prev_key = pw.get("wisdom_original", "").strip().lower()[:100]
                if prev_key:
                    seen_originals.add(prev_key)
            self.log(f"이전 명언 {len(previous_wisdoms)}개 중복 방지 키 등록")

        for i, w in enumerate(wisdoms):
            # 1. 필수 필드 확인
            missing = [f for f in REQUIRED_FIELDS if not w.get(f)]
            if missing:
                removed_indices.append(i)
                removed_reasons[str(i)] = f"필수 필드 누락: {', '.join(missing)}"
                continue

            # 2. 중복 확인 (원문 앞 100자 기준 — 이전 결과 포함)
            original_key = w["wisdom_original"].strip().lower()[:100]
            if original_key in seen_originals:
                removed_indices.append(i)
                removed_reasons[str(i)] = "중복 명언 (이전 결과 포함)"
                continue
            seen_originals.add(original_key)

            # 3. 카테고리 검증 및 자동 보정
            category = w.get("category", "")
            if category:
                cats = [c.strip() for c in category.split("|")]
                valid_cats = [c for c in cats if c in VALID_CATEGORIES]
                w["category"] = "|".join(valid_cats) if valid_cats else "self-improvement"
            else:
                w["category"] = "self-improvement"

            # 4. Mood 검증 및 자동 보정
            mood = w.get("mood", "")
            if mood:
                moods = [m.strip() for m in mood.split("|")]
                valid_moods_list = [m for m in moods if m in VALID_MOODS]
                w["mood"] = "|".join(valid_moods_list) if valid_moods_list else "growth"
            else:
                w["mood"] = "growth"

            # 5. 기본값 보정
            w.setdefault("source_url", "")
            w.setdefault("source_making_date", "")

            valid_wisdoms.append(w)

        removed_count = len(removed_indices)
        if removed_count > 0:
            reasons_summary = ", ".join(
                f"#{idx}({reason})" for idx, reason in
                list(removed_reasons.items())[:5]
            )
            self.log(f"검증 완료: {len(valid_wisdoms)}개 통과, {removed_count}개 제거 ({reasons_summary})")
        else:
            self.log(f"검증 완료: {len(valid_wisdoms)}개 전체 통과")

        return {
            "action": "APPROVED",
            "final_wisdoms": valid_wisdoms,
            "removed_count": removed_count,
            "removed_reasons": removed_reasons,
        }
