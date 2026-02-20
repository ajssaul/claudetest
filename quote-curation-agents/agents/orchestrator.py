"""
오케스트레이터 (Orchestrator) 에이전트.
전체 파이프라인을 조율하고 양방향 피드백 루프를 중앙에서 관리한다.
"""

import json
import logging
from datetime import datetime
from typing import Optional

from .base_agent import BaseAgent
from .collector import Collector
from .organizer import Organizer
from .reviewer import Reviewer
from .final_validator import FinalValidator
from models.task import Task
from models.wisdom import Wisdom, SourceType

import config

logger = logging.getLogger("quote-agents.orchestrator")


class PipelineReport:
    """강제 종료 시 사용자에게 보여줄 파이프라인 실행 리포트."""

    def __init__(self):
        self.requested_count = 0
        self.final_count = 0
        self.termination_reason = ""
        self.feedback_log: list[tuple] = []  # (경로, 횟수, 한도, 주요_사유)
        self.stage_tracking = {
            "collected": 0,
            "organized": 0,
            "review_passed": 0,
            "review_revised_to_pass": 0,
            "review_rejected": 0,
            "final_passed": 0,
            "final_removed": 0,
            "final_removed_reasons": {},
        }
        self.collection_rounds = 0

    def generate_report(self, feedback_counter: dict, max_same: int, max_restart: int, max_total: int) -> str:
        """파이프라인 실행 리포트를 생성한다."""
        lines = [
            "",
            "⚠️ 파이프라인 실행 리포트",
            "━" * 50,
            "",
            "■ 결과 요약",
            f"  - 요청 수량: {self.requested_count}개",
            f"  - 최종 확보 수량: {self.final_count}개",
            f"  - 미달 사유: {self.termination_reason}",
            "",
            "■ 강제 종료 원인",
        ]

        # 어떤 한도가 초과되었는지
        total_used = sum(feedback_counter.values())
        restart_count = feedback_counter.get("4→2", 0) + feedback_counter.get("5→2", 0)

        for route, count in feedback_counter.items():
            if count >= max_same:
                lines.append(f"  ☑ 동일 경로 피드백 {max_same}회 초과 (경로: {route})")
            else:
                lines.append(f"  □ 동일 경로 피드백 {max_same}회 초과 (경로: {route})")

        if restart_count >= max_restart:
            lines.append(f"  ☑ 파이프라인 재시작 {max_restart}회 초과")
        else:
            lines.append(f"  □ 파이프라인 재시작 {max_restart}회 초과")

        if total_used >= max_total:
            lines.append(f"  ☑ 전체 피드백 총 횟수 {max_total}회 초과")
        else:
            lines.append(f"  □ 전체 피드백 총 횟수 {max_total}회 초과")

        lines.extend([
            "",
            "■ 피드백 루프 사용 현황",
            f"  {'경로':<10} {'횟수/한도':<12} {'주요 반려 사유'}",
            f"  {'-'*10} {'-'*12} {'-'*30}",
        ])

        route_reasons = {}
        for route, count, limit, reason in self.feedback_log:
            if route not in route_reasons:
                route_reasons[route] = []
            route_reasons[route].append(reason)

        for route in ["3→2", "4→3", "4→2", "5→4", "5→2"]:
            count = feedback_counter.get(route, 0)
            if route in ["4→2", "5→2"]:
                limit = max_restart
            else:
                limit = max_same
            reasons = route_reasons.get(route, ["-"])
            reason_str = "; ".join(reasons[:2]) if reasons else "-"
            lines.append(f"  {route:<10} {count}/{limit}회{'':<6} {reason_str}")

        lines.append(f"  {'합계':<10} {total_used}/{max_total}회")

        lines.extend([
            "",
            "■ 단계별 수량 추적",
            f"  - 총 수집: {self.stage_tracking['collected']}개 ({self.collection_rounds}라운드)",
            f"  - 정리 후: {self.stage_tracking['organized']}개",
            f"  - 검수 통과: {self.stage_tracking['review_passed']}개 "
            f"(PASS {self.stage_tracking['review_passed']} / "
            f"REVISE→PASS {self.stage_tracking['review_revised_to_pass']} / "
            f"REJECT {self.stage_tracking['review_rejected']})",
            f"  - 최종 확인 통과: {self.stage_tracking['final_passed']}개 "
            f"(제거 {self.stage_tracking['final_removed']}개",
        ])

        # 제거 사유 상세
        if self.stage_tracking["final_removed_reasons"]:
            reason_parts = [
                f"{reason} {count}" for reason, count in
                self.stage_tracking["final_removed_reasons"].items()
            ]
            lines[-1] += ": " + ", ".join(reason_parts)
        lines[-1] += ")"

        shortage = self.requested_count - self.final_count
        lines.extend([
            "",
            "■ 권장 사항",
            f"  - 부족한 {shortage}개를 추가로 확보하려면, 동일 조건으로 재요청해주세요.",
            "  - 수량을 줄이거나 주제 범위를 넓히면 더 많은 결과를 얻을 수 있습니다.",
            "",
            "━" * 50,
            "",
            f"아래는 확보된 {self.final_count}개 명언입니다:",
            "",
        ])

        return "\n".join(lines)

    def should_show_report(self) -> bool:
        """강제 종료 시에만 True 반환."""
        return self.final_count < self.requested_count


class Orchestrator(BaseAgent):
    """파이프라인 조율 에이전트."""

    def __init__(self):
        super().__init__(
            name="오케스트레이터",
            role="전체 파이프라인 조율 및 피드백 루프 관리",
            system_prompt_file="orchestrator_system.txt",
        )
        self.collector = Collector()
        self.organizer = Organizer()
        self.reviewer = Reviewer()
        self.final_validator = FinalValidator()

        self.feedback_counter = {
            "3→2": 0,
            "4→3": 0,
            "4→2": 0,
            "5→4": 0,
            "5→2": 0,
        }
        self.total_feedback_count = 0
        self.MAX_SAME_ROUTE = config.MAX_SAME_ROUTE_FEEDBACK
        self.MAX_PIPELINE_RESTART = config.MAX_PIPELINE_RESTART
        self.MAX_TOTAL_FEEDBACK = config.MAX_TOTAL_FEEDBACK

        self.report = PipelineReport()
        self._feedback_reasons: list[tuple] = []

    def can_feedback(self, route: str) -> bool:
        """해당 경로의 피드백이 아직 가능한지 확인한다."""
        if self.total_feedback_count >= self.MAX_TOTAL_FEEDBACK:
            return False
        if route in ["4→2", "5→2"]:
            restart_count = self.feedback_counter["4→2"] + self.feedback_counter["5→2"]
            if restart_count >= self.MAX_PIPELINE_RESTART:
                return False
        if self.feedback_counter[route] >= self.MAX_SAME_ROUTE:
            return False
        return True

    def record_feedback(self, route: str, reason: str = ""):
        """피드백 횟수를 기록한다."""
        self.feedback_counter[route] += 1
        self.total_feedback_count += 1
        limit = self.MAX_PIPELINE_RESTART if route in ["4→2", "5→2"] else self.MAX_SAME_ROUTE
        self._feedback_reasons.append((route, self.feedback_counter[route], limit, reason))
        self.report.feedback_log.append((route, self.feedback_counter[route], limit, reason))

    def can_continue(self) -> bool:
        """파이프라인을 계속 진행할 수 있는지 확인한다."""
        if self.total_feedback_count >= self.MAX_TOTAL_FEEDBACK:
            self.report.termination_reason = "전체 피드백 총 횟수 초과"
            return False
        restart_count = self.feedback_counter["4→2"] + self.feedback_counter["5→2"]
        if restart_count >= self.MAX_PIPELINE_RESTART:
            self.report.termination_reason = "파이프라인 재시작 횟수 초과"
            return False
        return True

    def parse_user_request(self, user_request: str) -> Task:
        """사용자 요청을 파싱하여 Task 객체로 변환한다."""
        self.log(f"사용자 요청 파싱: {user_request}")

        messages = [{
            "role": "user",
            "content": f"다음 사용자 요청을 분석해줘:\n\n{user_request}",
        }]

        try:
            result = self.call_llm_json(messages, temperature=0.3)
            task = Task(
                topic=result.get("topic", ""),
                leaders=result.get("leaders", []),
                count=result.get("count", 10),
                categories=result.get("categories", []),
                moods=result.get("moods", []),
                constraints=result.get("constraints", ""),
            )
            self.log(
                f"파싱 결과: 주제='{task.topic}', 인물={task.leaders}, "
                f"개수={task.count}"
            )
            return task
        except Exception as e:
            logger.error(f"요청 파싱 실패: {e}")
            # 기본 태스크 반환
            return Task(topic=user_request, count=10)

    async def run_pipeline(self, user_request: str) -> str:
        """
        양방향 피드백 루프가 포함된 전체 파이프라인을 실행한다.

        Returns:
            최종 결과물 (TSV 형식 문자열)
        """
        # STEP 1: 사용자 요청 파싱
        task = self.parse_user_request(user_request)
        self.report.requested_count = task.count

        all_passed_wisdoms: list[dict] = []

        while len(all_passed_wisdoms) < task.count:
            if not self.can_continue():
                self.log("피드백 한도 초과. 강제 종료.")
                break

            # STEP 2: 수집
            needed = task.count - len(all_passed_wisdoms)
            collect_target = int(needed * config.COLLECTION_MULTIPLIER)
            self.log(f"[수집 단계] 목표: {collect_target}개 (부족: {needed}개)")

            collected_data = await self.collector.run(
                task=task,
                exclude=all_passed_wisdoms,
                target=collect_target,
            )
            self.report.stage_tracking["collected"] += len(collected_data)
            self.report.collection_rounds += 1

            if not collected_data:
                self.log("수집 결과 없음. 파이프라인 종료.")
                self.report.termination_reason = "수집 결과 없음"
                break

            # STEP 3: 정리 (3→2 반려 가능)
            organized_result = await self._organize_with_feedback(collected_data, task)
            if organized_result is None:
                self.log("정리 실패. 다시 수집부터 시작.")
                continue

            wisdoms = organized_result
            self.report.stage_tracking["organized"] += len(wisdoms)

            if not wisdoms:
                self.log("정리 결과 없음. 다시 수집부터 시작.")
                continue

            # STEP 4: 검수 (4→3, 4→2 반려 가능)
            review_result = await self._review_with_feedback(wisdoms, task, all_passed_wisdoms)

            if review_result == "NEED_MORE_COLLECTION":
                continue

            if not review_result:
                self.log("검수 통과 없음. 다시 수집부터 시작.")
                continue

            all_passed_wisdoms.extend(review_result)

            # STEP 5: 최종 확인 (5→4, 5→2 반려 가능)
            final_result = await self._validate_with_feedback(all_passed_wisdoms, task)

            if final_result == "NEED_MORE_COLLECTION":
                continue
            elif final_result == "RETURN_TO_REVIEWER":
                continue
            elif isinstance(final_result, list):
                all_passed_wisdoms = final_result
                break  # 최종 통과

        # STEP 6: 결과 출력
        final_wisdoms = all_passed_wisdoms[:task.count]
        self.report.final_count = len(final_wisdoms)
        self.report.stage_tracking["final_passed"] = len(final_wisdoms)

        return self._format_output(final_wisdoms, task)

    async def _organize_with_feedback(
        self, collected_data: list[dict], task: Task
    ) -> Optional[list[dict]]:
        """정리 단계. 수집 데이터 부실 시 수집자에게 반려 (3→2)."""
        for attempt in range(self.MAX_SAME_ROUTE + 1):
            result = await self.organizer.run(collected_data, task)

            if result["action"] == "RETURN_TO_COLLECTOR":
                if not self.can_feedback("3→2"):
                    self.log("3→2 피드백 한도 초과. 현재 데이터로 강제 진행.")
                    force_result = await self.organizer.run(collected_data, task, force=True)
                    return force_result.get("wisdoms", [])

                reason = result.get("reason", "수집 데이터 부실")
                self.record_feedback("3→2", reason)
                self.log(
                    f"[3→2 반려] ({self.feedback_counter['3→2']}/"
                    f"{self.MAX_SAME_ROUTE}회): {reason}"
                )

                # 수집자에게 보완 수집 요청
                collected_data = await self.collector.run(
                    task=task,
                    supplement_request=result.get("requirements", reason),
                )
                self.report.stage_tracking["collected"] += len(collected_data)
                self.report.collection_rounds += 1

                if not collected_data:
                    return None
            else:
                return result.get("wisdoms", [])

        return None

    async def _review_with_feedback(
        self,
        organized_data: list[dict],
        task: Task,
        existing_passed: list[dict],
    ):
        """검수 단계. REVISE→정리자 반려 (4→3), 수량 부족→수집자 반려 (4→2)."""
        current_wisdoms = organized_data

        for revision_round in range(self.MAX_SAME_ROUTE + 1):
            review_result = await self.reviewer.run(current_wisdoms, task)
            reviews = review_result.get("reviews", [])

            # 검수 결과 분류
            passed = []
            revise_wisdoms = []
            revise_instructions = []
            reject_count = 0

            for i, review in enumerate(reviews):
                if i >= len(current_wisdoms):
                    break
                verdict = review.get("verdict", "PASS")
                if verdict == "PASS":
                    passed.append(current_wisdoms[i])
                elif verdict == "REVISE":
                    revise_wisdoms.append(current_wisdoms[i])
                    revise_instructions.append(
                        review.get("revision_instructions", "수정 필요")
                    )
                elif verdict == "REJECT":
                    reject_count += 1

            self.report.stage_tracking["review_passed"] += len(passed)
            self.report.stage_tracking["review_rejected"] += reject_count

            # REVISE 항목이 없으면 검수 완료
            if not revise_wisdoms:
                break

            # 4→3 피드백: 정리자에게 수정 요청
            if not self.can_feedback("4→3"):
                self.log("4→3 피드백 한도 초과. REVISE 항목은 REJECT 처리.")
                self.report.stage_tracking["review_rejected"] += len(revise_wisdoms)
                break

            self.record_feedback(
                "4→3",
                f"{len(revise_wisdoms)}개 수정 요청"
            )
            self.log(
                f"[4→3 반려] ({self.feedback_counter['4→3']}/"
                f"{self.MAX_SAME_ROUTE}회): {len(revise_wisdoms)}개 수정 요청"
            )

            revised = await self.organizer.revise(revise_wisdoms, revise_instructions)
            self.report.stage_tracking["review_revised_to_pass"] += len(revised)

            # 수정된 명언 + PASS 명언으로 재검수
            current_wisdoms = passed + revised

        # 최종 PASS 목록
        if not passed and not current_wisdoms:
            passed = []
        elif not passed:
            # 재검수 후 전체 다시 확인
            final_review = await self.reviewer.run(current_wisdoms, task)
            passed = self.reviewer.get_passed(
                current_wisdoms, final_review.get("reviews", [])
            )

        # 4→2: 수량 부족 확인
        total_available = len(existing_passed) + len(passed)
        if total_available < task.count:
            shortage = task.count - total_available

            if self.can_feedback("4→2"):
                self.record_feedback("4→2", f"수량 부족: {shortage}개")
                self.log(
                    f"[4→2 반려] ({self.feedback_counter['4→2']}/"
                    f"{self.MAX_PIPELINE_RESTART}회): "
                    f"수량 부족 {shortage}개, 수집자에게 추가 수집 요청"
                )
                # 현재까지 통과분을 existing_passed에 반영
                existing_passed.extend(passed)
                return "NEED_MORE_COLLECTION"
            else:
                self.log(
                    f"4→2 피드백 한도 초과. {total_available}개로 진행."
                )

        return passed

    async def _validate_with_feedback(
        self, all_wisdoms: list[dict], task: Task
    ):
        """최종 확인 단계. 5→4, 5→2 반려 가능."""
        validation = await self.final_validator.run(all_wisdoms, task)
        action = validation.get("action", "APPROVED")

        if action == "APPROVED":
            final_wisdoms = validation.get("final_wisdoms", all_wisdoms)
            removed = validation.get("removed_count", 0)
            self.report.stage_tracking["final_removed"] = removed
            if validation.get("removed_reasons"):
                self.report.stage_tracking["final_removed_reasons"] = validation["removed_reasons"]
            return final_wisdoms

        if action == "RETURN_TO_REVIEWER":
            if self.can_feedback("5→4"):
                reason = validation.get("reason", "품질/적합성 문제")
                self.record_feedback("5→4", reason)
                self.log(
                    f"[5→4 반려] ({self.feedback_counter['5→4']}/"
                    f"{self.MAX_SAME_ROUTE}회): {reason}"
                )

                # 문제 항목 제거 후 재검수 필요
                problematic = set(validation.get("problematic_items", []))
                all_wisdoms[:] = [
                    w for i, w in enumerate(all_wisdoms)
                    if i not in problematic
                ]
                return "RETURN_TO_REVIEWER"
            else:
                self.log("5→4 피드백 한도 초과. 현재 결과물로 진행.")
                passing = validation.get("passing_subset", all_wisdoms)
                return passing

        if action == "RETURN_TO_COLLECTOR_VIA_ORCHESTRATOR":
            if self.can_feedback("5→2"):
                reason = validation.get("reason", "수량 크게 부족")
                self.record_feedback("5→2", reason)
                self.log(
                    f"[5→2 반려] ({self.feedback_counter['5→2']}/"
                    f"{self.MAX_PIPELINE_RESTART}회): {reason}"
                )
                # 통과분만 유지
                all_wisdoms[:] = validation.get("passed_wisdoms", all_wisdoms)
                return "NEED_MORE_COLLECTION"
            else:
                self.log("5→2 피드백 한도 초과. 현재 결과물로 진행.")
                passing = validation.get("passed_wisdoms", all_wisdoms)
                return passing

        return all_wisdoms

    def _format_output(self, wisdoms: list[dict], task: Task) -> str:
        """최종 출력을 포맷한다."""
        output_parts = []

        # 강제 종료 시 리포트 출력
        if self.report.should_show_report():
            report_str = self.report.generate_report(
                self.feedback_counter,
                self.MAX_SAME_ROUTE,
                self.MAX_PIPELINE_RESTART,
                self.MAX_TOTAL_FEEDBACK,
            )
            output_parts.append(report_str)

        # TSV 출력
        header = Wisdom.tsv_header()
        output_parts.append(header)

        for w in wisdoms:
            try:
                # dict를 Wisdom 모델로 변환 시도
                wisdom_obj = self._dict_to_wisdom(w)
                output_parts.append(wisdom_obj.to_tsv_row())
            except Exception:
                # 모델 변환 실패 시 직접 TSV 행 생성
                row = self._dict_to_tsv_row(w)
                output_parts.append(row)

        return "\n".join(output_parts)

    @staticmethod
    def _dict_to_wisdom(data: dict) -> Wisdom:
        """딕셔너리를 Wisdom 모델로 변환한다."""
        # source_type 정규화
        source_type_raw = data.get("source_type", "기타")
        source_type_map = {
            "도서": SourceType.BOOK,
            "도서 (비퍼블릭 도메인)": SourceType.BOOK_NON_PD,
            "인터뷰": SourceType.INTERVIEW,
            "연설": SourceType.SPEECH,
            "팟캐스트": SourceType.PODCAST,
            "SNS": SourceType.SNS,
            "블로그": SourceType.BLOG,
        }
        source_type = source_type_map.get(source_type_raw, SourceType.OTHER)

        return Wisdom(
            leader_name=data.get("leader_name", ""),
            leader_name_en=data.get("leader_name_en", ""),
            leader_title=data.get("leader_title", ""),
            wisdom_original=data.get("wisdom_original", ""),
            wisdom_kr=data.get("wisdom_kr", ""),
            wisdom_commentary=data.get("wisdom_commentary", ""),
            source=data.get("source", ""),
            source_type=source_type,
            source_url=data.get("source_url", ""),
            category=data.get("category", "self-improvement"),
            mood=data.get("mood"),
            source_making_date=data.get("source_making_date"),
        )

    @staticmethod
    def _dict_to_tsv_row(data: dict) -> str:
        """딕셔너리를 직접 TSV 행으로 변환한다 (모델 변환 실패 시 폴백)."""
        fields = [
            data.get("leader_name", ""),
            data.get("leader_name_en", ""),
            data.get("leader_title", ""),
            data.get("wisdom_original", ""),
            data.get("wisdom_kr", ""),
            data.get("wisdom_commentary", ""),
            data.get("source", ""),
            data.get("source_type", "기타"),
            data.get("source_url", ""),
            data.get("category", ""),
            data.get("mood", ""),
            data.get("source_making_date", ""),
        ]
        return "\t".join(str(f) for f in fields)
